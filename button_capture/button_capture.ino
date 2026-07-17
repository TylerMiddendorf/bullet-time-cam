#include "esp_camera.h"
#include "esp_mac.h"
#include "esp_system.h"

#if __has_include("esp_idf_version.h")
#include "esp_idf_version.h"
#endif

#define CAMERA_MODEL_XIAO_ESP32S3
#include "camera_pins.h"

static const uint8_t CAMERA_COUNT = 4;

// Wire this pin from all four XIAO boards together. The shared trigger bus is
// idle HIGH and a normally-open button pulls it to the common GND rail.
static const int TRIGGER_PIN = 2;  // XIAO D1 / GPIO2

static const uint16_t CAPTURE_WIDTH = 2048;
static const uint16_t CAPTURE_HEIGHT = 1536;
static const framesize_t CAPTURE_FRAME_SIZE = FRAMESIZE_QXGA;

static const uint8_t JPEG_QUALITY = 8;  // Lower means higher quality in esp32-camera.
static const unsigned long LIGHT_SETTLE_MS = 700;
static const uint8_t WARMUP_FRAME_COUNT = 4;
static const gainceiling_t SENSOR_GAIN_CEILING = GAINCEILING_4X;
static const int SENSOR_SHARPNESS = 1;
static const int SENSOR_DENOISE = 1;
static const unsigned long TRIGGER_DEBOUNCE_MS = 40;
static const unsigned long HOST_ACK_TIMEOUT_MS = 10000;
static const size_t USB_CHUNK_SIZE = 4096;
static const uint8_t PROTOCOL_VERSION = 1;
static const uint8_t MSG_HELLO = 1;
static const uint8_t MSG_CAPTURE_STARTED = 2;
static const uint8_t MSG_IMAGE = 3;
static const uint8_t MSG_TRANSFER_COMPLETE = 4;
static const uint8_t MSG_ERROR = 5;
static const uint8_t MSG_LOG = 6;
static const uint8_t MSG_CAPTURE_REQUEST = 7;
static const uint8_t MSG_PING = 8;
// Test-only command: the next USB image has a valid header CRC for the
// original frame buffer but one payload byte is changed on the wire. It is
// inert unless the host explicitly sends this command.
static const uint8_t MSG_TEST_CORRUPT_NEXT_IMAGE = 9;
static const uint8_t MSG_ACK = 0x80;
static const uint8_t MSG_NACK = 0x81;

static bool lastRawTriggerState = HIGH;
static bool stableTriggerState = HIGH;
static unsigned long lastTriggerChangeMs = 0;
static uint32_t captureSequence = 0;
static uint32_t bootId = 0;
static char nodeUid[13] = {};
static uint8_t idleMagicMatched = 0;
static bool corruptNextUsbImage = false;

void sendHelloFrame();

uint32_t crc32Bytes(const uint8_t *data, size_t length, uint32_t crc = 0) {
  crc = ~crc;
  for (size_t i = 0; i < length; ++i) {
    crc ^= data[i];
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc >> 1) ^ (0xEDB88320UL & (0U - (crc & 1U)));
    }
  }
  return ~crc;
}

void writeU16Le(uint8_t *target, uint16_t value) {
  target[0] = value & 0xff;
  target[1] = (value >> 8) & 0xff;
}

void writeU32Le(uint8_t *target, uint32_t value) {
  target[0] = value & 0xff;
  target[1] = (value >> 8) & 0xff;
  target[2] = (value >> 16) & 0xff;
  target[3] = (value >> 24) & 0xff;
}

uint32_t readU32Le(const uint8_t *source) {
  return static_cast<uint32_t>(source[0]) |
         (static_cast<uint32_t>(source[1]) << 8) |
         (static_cast<uint32_t>(source[2]) << 16) |
         (static_cast<uint32_t>(source[3]) << 24);
}

bool writeAll(const uint8_t *data, size_t length) {
  size_t offset = 0;
  while (offset < length) {
    size_t chunk = min(USB_CHUNK_SIZE, length - offset);
    size_t written = Serial.write(data + offset, chunk);
    if (written == 0) {
      return false;
    }
    offset += written;
    yield();
  }
  return true;
}

bool writePayloadWithOneCorruptByte(const uint8_t *data, size_t length) {
  if (length == 0) {
    return true;
  }
  const size_t corruptOffset = length / 2;
  const uint8_t corrupted = data[corruptOffset] ^ 0x01;
  return writeAll(data, corruptOffset) &&
         writeAll(&corrupted, 1) &&
         writeAll(data + corruptOffset + 1, length - corruptOffset - 1);
}

bool sendFrame(uint8_t messageType, const char *metadata, const uint8_t *payload = nullptr, size_t payloadLength = 0,
               bool corruptPayloadOnWire = false) {
  const size_t metadataLength = strlen(metadata);
  uint8_t header[28] = {};
  memcpy(header, "BTC1", 4);
  header[4] = PROTOCOL_VERSION;
  header[5] = messageType;
  writeU16Le(header + 6, 0);
  writeU32Le(header + 8, metadataLength);
  writeU32Le(header + 12, payloadLength);
  writeU32Le(header + 16, crc32Bytes(reinterpret_cast<const uint8_t *>(metadata), metadataLength));
  writeU32Le(header + 20, payloadLength ? crc32Bytes(payload, payloadLength) : 0);
  writeU32Le(header + 24, crc32Bytes(header, 24));
  return writeAll(header, sizeof(header)) &&
         writeAll(reinterpret_cast<const uint8_t *>(metadata), metadataLength) &&
         (!payloadLength || (corruptPayloadOnWire ? writePayloadWithOneCorruptByte(payload, payloadLength)
                                                  : writeAll(payload, payloadLength)));
}

void sendNodeMessage(uint8_t messageType, uint32_t sequence, uint64_t timestampUs, const char *message) {
  char metadata[384];
  snprintf(metadata, sizeof(metadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,\"timestamp_us\":%llu,\"message\":\"%s\"}",
           nodeUid, static_cast<unsigned long>(bootId), static_cast<unsigned long>(sequence),
           static_cast<unsigned long long>(timestampUs), message);
  sendFrame(messageType, metadata);
}

bool readInboundFrame(uint8_t &messageType, char *metadata, size_t metadataCapacity) {
  const char magic[] = "BTC1";
  while (Serial.available()) {
    uint8_t value = Serial.read();
    idleMagicMatched = (value == static_cast<uint8_t>(magic[idleMagicMatched]))
                           ? idleMagicMatched + 1
                           : (value == 'B' ? 1 : 0);
    if (idleMagicMatched != 4) {
      continue;
    }
    uint8_t remainder[24];
    if (Serial.readBytes(remainder, sizeof(remainder)) != sizeof(remainder)) {
      idleMagicMatched = 0;
      return false;
    }
    const uint32_t metadataLength = readU32Le(remainder + 4);
    const uint32_t payloadLength = readU32Le(remainder + 8);
    if (remainder[0] != PROTOCOL_VERSION ||
        crc32Bytes(remainder, 20, crc32Bytes(reinterpret_cast<const uint8_t *>("BTC1"), 4)) != readU32Le(remainder + 20) ||
        metadataLength + 1 > metadataCapacity || payloadLength > 1024) {
      idleMagicMatched = 0;
      return false;
    }
    if (Serial.readBytes(reinterpret_cast<uint8_t *>(metadata), metadataLength) != metadataLength) {
      idleMagicMatched = 0;
      return false;
    }
    metadata[metadataLength] = '\0';
    const uint32_t expectedMetadataCrc = readU32Le(remainder + 12);
    if (crc32Bytes(reinterpret_cast<const uint8_t *>(metadata), metadataLength) != expectedMetadataCrc) {
      idleMagicMatched = 0;
      return false;
    }
    uint32_t payloadCrc = 0;
    for (uint32_t i = 0; i < payloadLength; ++i) {
      if (Serial.readBytes(&value, 1) != 1) {
        idleMagicMatched = 0;
        return false;
      }
      payloadCrc = crc32Bytes(&value, 1, payloadCrc);
    }
    if (payloadCrc != readU32Le(remainder + 16)) {
      idleMagicMatched = 0;
      return false;
    }
    messageType = remainder[1];
    idleMagicMatched = 0;
    return true;
  }
  return false;
}

bool waitForHostAck(uint32_t sequence) {
  const unsigned long started = millis();
  char metadata[1024];
  char uidNeedle[48];
  char bootNeedle[48];
  char sequenceNeedle[48];
  snprintf(uidNeedle, sizeof(uidNeedle), "\"node_uid\":\"%s\"", nodeUid);
  snprintf(bootNeedle, sizeof(bootNeedle), "\"boot_id\":%lu", static_cast<unsigned long>(bootId));
  snprintf(sequenceNeedle, sizeof(sequenceNeedle), "\"capture_seq\":%lu", static_cast<unsigned long>(sequence));
  while ((millis() - started) < HOST_ACK_TIMEOUT_MS) {
    uint8_t messageType = 0;
    if (!readInboundFrame(messageType, metadata, sizeof(metadata))) {
      delay(1);
      continue;
    }
    const bool matching = strstr(metadata, uidNeedle) && strstr(metadata, bootNeedle) && strstr(metadata, sequenceNeedle);
    if (matching && messageType == MSG_ACK) {
      return true;
    }
    if (matching && messageType == MSG_NACK) {
      return false;
    }
  }
  sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "HOST_ACK_TIMEOUT");
  return false;
}

bool pollForUsbCaptureRequest() {
  uint8_t messageType = 0;
  char metadata[1024];
  if (!readInboundFrame(messageType, metadata, sizeof(metadata))) {
    return false;
  }
  if (messageType == MSG_PING) {
    sendHelloFrame();
    return false;
  }
  if (messageType == MSG_TEST_CORRUPT_NEXT_IMAGE) {
    corruptNextUsbImage = true;
    sendNodeMessage(MSG_LOG, 0, esp_timer_get_time(), "TEST_CORRUPTION_ARMED");
    return false;
  }
  return messageType == MSG_CAPTURE_REQUEST;
}

void initializeNodeIdentity() {
  uint8_t mac[6];
  esp_efuse_mac_get_default(mac);
  snprintf(nodeUid, sizeof(nodeUid), "%02X%02X%02X%02X%02X%02X",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
  bootId = esp_random();
}

void sendHelloFrame() {
  char helloMetadata[320];
  snprintf(helloMetadata, sizeof(helloMetadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,\"firmware_version\":\"0.2.0\",\"timestamp_us\":%llu}",
           nodeUid, static_cast<unsigned long>(bootId), static_cast<unsigned long>(captureSequence),
           static_cast<unsigned long long>(esp_timer_get_time()));
  sendFrame(MSG_HELLO, helloMetadata);
}

void halt(const char *message) {
  Serial.println(message);
  Serial.println("Stopped. Fix the issue and press Reset.");
  while (true) {
    delay(1000);
  }
}

bool discardWarmupFrames() {
  for (uint8_t i = 0; i < WARMUP_FRAME_COUNT; i++) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      return false;
    }

    esp_camera_fb_return(fb);
  }

  return true;
}

bool capturePhoto() {
  const uint32_t sequence = ++captureSequence;
  const uint64_t triggerAcceptedUs = esp_timer_get_time();
  char captureMetadata[320];
  snprintf(captureMetadata, sizeof(captureMetadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,\"trigger_accepted_us\":%llu}",
           nodeUid, static_cast<unsigned long>(bootId), static_cast<unsigned long>(sequence),
           static_cast<unsigned long long>(triggerAcceptedUs));
  sendFrame(MSG_CAPTURE_STARTED, captureMetadata);

  const uint64_t acquisitionStartedUs = esp_timer_get_time();
  delay(LIGHT_SETTLE_MS);
  if (!discardWarmupFrames()) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "CAMERA_SETTLE_FAILED");
    return false;
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_BUFFER_FAILED");
    return false;
  }

  const uint64_t frameReadyUs = esp_timer_get_time();
  bool ok = false;

  if (fb->format != PIXFORMAT_JPEG) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_NOT_JPEG");
  } else if (fb->width != CAPTURE_WIDTH || fb->height != CAPTURE_HEIGHT) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_DIMENSIONS_INVALID");
  } else {
    const uint32_t jpegCrc = crc32Bytes(fb->buf, fb->len);
    const uint64_t transferStartedUs = esp_timer_get_time();
    char imageMetadata[640];
    snprintf(imageMetadata, sizeof(imageMetadata),
             "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,\"width\":%u,\"height\":%u,\"jpeg_bytes\":%u,\"jpeg_crc32\":\"%08lx\",\"trigger_accepted_us\":%llu,\"acquisition_started_us\":%llu,\"frame_ready_us\":%llu,\"transfer_started_us\":%llu}",
             nodeUid, static_cast<unsigned long>(bootId), static_cast<unsigned long>(sequence),
             static_cast<unsigned int>(fb->width), static_cast<unsigned int>(fb->height),
             static_cast<unsigned int>(fb->len), static_cast<unsigned long>(jpegCrc),
             static_cast<unsigned long long>(triggerAcceptedUs),
             static_cast<unsigned long long>(acquisitionStartedUs),
             static_cast<unsigned long long>(frameReadyUs),
             static_cast<unsigned long long>(transferStartedUs));

    const bool corruptPayloadOnWire = corruptNextUsbImage;
    corruptNextUsbImage = false;
    bool transferred = sendFrame(MSG_IMAGE, imageMetadata, fb->buf, fb->len, corruptPayloadOnWire);
    const uint64_t transferCompletedUs = esp_timer_get_time();
    char completeMetadata[384];
    snprintf(completeMetadata, sizeof(completeMetadata),
             "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,\"transfer_completed_us\":%llu,\"status\":\"%s\"}",
             nodeUid, static_cast<unsigned long>(bootId), static_cast<unsigned long>(sequence),
             static_cast<unsigned long long>(transferCompletedUs), transferred ? "written" : "write_failed");
    sendFrame(transferred ? MSG_TRANSFER_COMPLETE : MSG_ERROR, completeMetadata);
    bool acknowledged = transferred && waitForHostAck(sequence);

    ok = acknowledged;
  }

  esp_camera_fb_return(fb);
  return ok;
}

void configureCameraPins(camera_config_t &config) {
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;

#if defined(ESP_IDF_VERSION_MAJOR) && ESP_IDF_VERSION_MAJOR >= 5
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
#else
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
#endif

  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
}

void initializeCamera() {
  camera_config_t config = {};

  configureCameraPins(config);
  config.xclk_freq_hz = 20000000;
  config.frame_size = CAPTURE_FRAME_SIZE;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_LATEST;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = JPEG_QUALITY;
  config.fb_count = 1;

  if (!psramFound()) {
    halt("PSRAM was not found. Enable PSRAM in Arduino IDE before uploading.");
  }

  Serial.println("Initializing camera...");
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    halt("Camera initialization failed.");
  }

  sensor_t *sensor = esp_camera_sensor_get();
  if (!sensor) {
    halt("Camera initialized, but sensor handle was not available.");
  }

  if (sensor->set_quality) {
    sensor->set_quality(sensor, JPEG_QUALITY);
  }
  if (sensor->set_brightness) {
    sensor->set_brightness(sensor, 0);
  }
  if (sensor->set_contrast) {
    sensor->set_contrast(sensor, 1);
  }
  if (sensor->set_saturation) {
    sensor->set_saturation(sensor, 0);
  }
  if (sensor->set_sharpness) {
    sensor->set_sharpness(sensor, SENSOR_SHARPNESS);
  }
  if (sensor->set_denoise) {
    sensor->set_denoise(sensor, SENSOR_DENOISE);
  }
  if (sensor->set_gainceiling) {
    sensor->set_gainceiling(sensor, SENSOR_GAIN_CEILING);
  }
  if (sensor->set_whitebal) {
    sensor->set_whitebal(sensor, 1);
  }
  if (sensor->set_awb_gain) {
    sensor->set_awb_gain(sensor, 1);
  }
  if (sensor->set_gain_ctrl) {
    sensor->set_gain_ctrl(sensor, 1);
  }
  if (sensor->set_exposure_ctrl) {
    sensor->set_exposure_ctrl(sensor, 1);
  }
  if (sensor->set_aec2) {
    sensor->set_aec2(sensor, 1);
  }
  if (sensor->set_bpc) {
    sensor->set_bpc(sensor, 1);
  }
  if (sensor->set_wpc) {
    sensor->set_wpc(sensor, 1);
  }
  if (sensor->set_raw_gma) {
    sensor->set_raw_gma(sensor, 1);
  }

  if (sensor->status.framesize != CAPTURE_FRAME_SIZE) {
    halt("Camera did not accept the target still-photo frame size.");
  }

  Serial.printf("Camera ready: %ux%u JPEG, quality %u.\n",
                CAPTURE_WIDTH,
                CAPTURE_HEIGHT,
                JPEG_QUALITY);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.printf("XIAO ESP32S3 Sense %u-Camera Shared Trigger\n",
                static_cast<unsigned int>(CAMERA_COUNT));

  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  initializeNodeIdentity();

  lastRawTriggerState = digitalRead(TRIGGER_PIN);
  stableTriggerState = lastRawTriggerState;
  lastTriggerChangeMs = millis();

  initializeCamera();

  Serial.printf("USB protocol ready: BTC1 v%u, node UID %s.\n", PROTOCOL_VERSION, nodeUid);
  Serial.println("Ready. Pull the shared trigger LOW to capture.");
  sendHelloFrame();
}

void loop() {
  bool rawState = digitalRead(TRIGGER_PIN);

  if (rawState != lastRawTriggerState) {
    lastRawTriggerState = rawState;
    lastTriggerChangeMs = millis();
  }

  if ((millis() - lastTriggerChangeMs) >= TRIGGER_DEBOUNCE_MS && rawState != stableTriggerState) {
    stableTriggerState = rawState;

    if (stableTriggerState == LOW) {
      capturePhoto();
    }
  }

  if (pollForUsbCaptureRequest()) {
    capturePhoto();
  }

  delay(5);
}
