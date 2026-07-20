#include "camera_capture.h"

#include <Arduino.h>
#include <esp_camera.h>
#include <string.h>

#if __has_include("esp_idf_version.h")
#include "esp_idf_version.h"
#endif

#define CAMERA_MODEL_XIAO_ESP32S3
#include "camera_pins.h"

#include "btc_protocol.h"
#include "firmware_config.h"
#include "trigger_input.h"

namespace {

void haltForever(const char* message) {
  Serial.println(message);
  Serial.println("Stopped. Fix the issue and press Reset.");
  while (true) {
    delay(1000);
  }
}

bool discardWarmupFrames() {
  for (uint8_t i = 0; i < WARMUP_FRAME_COUNT; ++i) {
    camera_fb_t* frame = esp_camera_fb_get();
    if (!frame) {
      return false;
    }
    esp_camera_fb_return(frame);
  }
  return true;
}

uint8_t transferSlot() {
  const char* identity = nodeUid();
  return crc32Bytes(reinterpret_cast<const uint8_t*>(identity), strlen(identity)) % CAMERA_COUNT;
}

bool setFrameSize(sensor_t* sensor, framesize_t frameSize) {
  return sensor && sensor->set_framesize && sensor->set_framesize(sensor, frameSize) == 0;
}

void configureCameraPins(camera_config_t& config) {
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

}  // namespace

bool sendPreviewFrame() {
  static uint32_t previewSequence = 0;
  sensor_t* sensor = esp_camera_sensor_get();
  if (!setFrameSize(sensor, PREVIEW_FRAME_SIZE)) {
    sendNodeMessage(MSG_LOG, 0, esp_timer_get_time(), "PREVIEW_SIZE_FAILED");
    return false;
  }

  camera_fb_t* frame = nullptr;
  for (uint8_t attempt = 0; attempt < PREVIEW_FRAME_ATTEMPTS; ++attempt) {
    frame = esp_camera_fb_get();
    if (!frame) {
      break;
    }
    if (frame->format == PIXFORMAT_JPEG && frame->width == PREVIEW_WIDTH &&
        frame->height == PREVIEW_HEIGHT) {
      break;
    }
    esp_camera_fb_return(frame);
    frame = nullptr;
    if (sharedTriggerPressed()) {
      if (!setFrameSize(sensor, CAPTURE_FRAME_SIZE)) {
        haltForever("Camera did not restore the still-photo frame size after preview.");
      }
      return true;
    }
  }
  const bool restored = setFrameSize(sensor, CAPTURE_FRAME_SIZE);
  if (!frame) {
    sendNodeMessage(MSG_LOG, 0, esp_timer_get_time(), "PREVIEW_FRAME_FAILED");
    return false;
  }

  if (!restored) {
    esp_camera_fb_return(frame);
    haltForever("Camera did not restore the still-photo frame size after preview.");
  }

  // Capture always wins once a debounced shared-trigger press is observable.
  if (sharedTriggerPressed()) {
    esp_camera_fb_return(frame);
    return true;
  }

  if (frame->len == 0 || frame->len > MAX_PREVIEW_JPEG_BYTES) {
    esp_camera_fb_return(frame);
    sendNodeMessage(MSG_LOG, 0, esp_timer_get_time(), "PREVIEW_FRAME_INVALID");
    return false;
  }

  const uint32_t sequence = ++previewSequence;
  const uint32_t jpegCrc = crc32Bytes(frame->buf, frame->len);
  char metadata[384];
  snprintf(metadata, sizeof(metadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"preview_seq\":%lu,"
           "\"width\":%u,\"height\":%u,\"jpeg_bytes\":%u,"
           "\"jpeg_crc32\":\"%08lx\",\"timestamp_us\":%llu}",
           nodeUid(), static_cast<unsigned long>(nodeBootId()),
           static_cast<unsigned long>(sequence), static_cast<unsigned int>(frame->width),
           static_cast<unsigned int>(frame->height), static_cast<unsigned int>(frame->len),
           static_cast<unsigned long>(jpegCrc),
           static_cast<unsigned long long>(esp_timer_get_time()));
  sendFrame(MSG_PREVIEW_IMAGE, metadata, frame->buf, frame->len);
  esp_camera_fb_return(frame);
  return false;
}

bool capturePhoto() {
  const uint32_t sequence = nextCaptureSequence();
  const uint64_t triggerAcceptedUs = esp_timer_get_time();
  char captureMetadata[320];
  snprintf(captureMetadata, sizeof(captureMetadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,"
           "\"trigger_accepted_us\":%llu}",
           nodeUid(), static_cast<unsigned long>(nodeBootId()),
           static_cast<unsigned long>(sequence),
           static_cast<unsigned long long>(triggerAcceptedUs));
  sendFrame(MSG_CAPTURE_STARTED, captureMetadata);

  const uint64_t acquisitionStartedUs = esp_timer_get_time();
  delay(LIGHT_SETTLE_MS);
  if (!discardWarmupFrames()) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "CAMERA_SETTLE_FAILED");
    return false;
  }

  camera_fb_t* frame = esp_camera_fb_get();
  if (!frame) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_BUFFER_FAILED");
    return false;
  }

  const uint64_t frameReadyUs = esp_timer_get_time();
  bool ok = false;
  if (frame->format != PIXFORMAT_JPEG) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_NOT_JPEG");
  } else if (frame->width != CAPTURE_WIDTH || frame->height != CAPTURE_HEIGHT) {
    sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(), "FRAME_DIMENSIONS_INVALID");
  } else {
    const uint32_t jpegCrc = crc32Bytes(frame->buf, frame->len);
    const uint8_t slot = transferSlot();
    delay(slot * TRANSFER_SLOT_SPACING_MS);
    const uint64_t transferStartedUs = esp_timer_get_time();
    char imageMetadata[640];
    snprintf(imageMetadata, sizeof(imageMetadata),
             "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,"
             "\"width\":%u,\"height\":%u,\"jpeg_bytes\":%u,"
             "\"jpeg_crc32\":\"%08lx\",\"trigger_accepted_us\":%llu,"
             "\"acquisition_started_us\":%llu,\"frame_ready_us\":%llu,"
             "\"transfer_slot\":%u,\"transfer_started_us\":%llu}",
             nodeUid(), static_cast<unsigned long>(nodeBootId()),
             static_cast<unsigned long>(sequence), static_cast<unsigned int>(frame->width),
             static_cast<unsigned int>(frame->height), static_cast<unsigned int>(frame->len),
             static_cast<unsigned long>(jpegCrc),
             static_cast<unsigned long long>(triggerAcceptedUs),
             static_cast<unsigned long long>(acquisitionStartedUs),
             static_cast<unsigned long long>(frameReadyUs), static_cast<unsigned int>(slot),
             static_cast<unsigned long long>(transferStartedUs));

    const bool transferred =
        sendFrame(MSG_IMAGE, imageMetadata, frame->buf, frame->len, consumeCorruptNextUsbImage());
    const uint64_t transferCompletedUs = esp_timer_get_time();
    char completeMetadata[384];
    snprintf(completeMetadata, sizeof(completeMetadata),
             "{\"node_uid\":\"%s\",\"boot_id\":%lu,"
             "\"capture_seq\":%lu,\"transfer_completed_us\":%llu,"
             "\"status\":\"%s\"}",
             nodeUid(), static_cast<unsigned long>(nodeBootId()),
             static_cast<unsigned long>(sequence),
             static_cast<unsigned long long>(transferCompletedUs),
             transferred ? "written" : "write_failed");
    sendFrame(transferred ? MSG_TRANSFER_COMPLETE : MSG_ERROR, completeMetadata);
    ok = transferred && waitForHostAck(sequence);
  }

  esp_camera_fb_return(frame);
  return ok;
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
    haltForever("PSRAM was not found. Enable PSRAM before uploading.");
  }

  Serial.println("Initializing camera...");
  const esp_err_t error = esp_camera_init(&config);
  if (error != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", error);
    haltForever("Camera initialization failed.");
  }

  sensor_t* sensor = esp_camera_sensor_get();
  if (!sensor) {
    haltForever("Camera initialized, but sensor handle was unavailable.");
  }

  if (sensor->set_quality)
    sensor->set_quality(sensor, JPEG_QUALITY);
  if (sensor->set_brightness)
    sensor->set_brightness(sensor, 0);
  if (sensor->set_contrast)
    sensor->set_contrast(sensor, 1);
  if (sensor->set_saturation)
    sensor->set_saturation(sensor, 0);
  if (sensor->set_sharpness)
    sensor->set_sharpness(sensor, SENSOR_SHARPNESS);
  if (sensor->set_denoise)
    sensor->set_denoise(sensor, SENSOR_DENOISE);
  if (sensor->set_gainceiling)
    sensor->set_gainceiling(sensor, SENSOR_GAIN_CEILING);
  if (sensor->set_whitebal)
    sensor->set_whitebal(sensor, 1);
  if (sensor->set_awb_gain)
    sensor->set_awb_gain(sensor, 1);
  if (sensor->set_gain_ctrl)
    sensor->set_gain_ctrl(sensor, 1);
  if (sensor->set_exposure_ctrl)
    sensor->set_exposure_ctrl(sensor, 1);
  if (sensor->set_aec2)
    sensor->set_aec2(sensor, 1);
  if (sensor->set_bpc)
    sensor->set_bpc(sensor, 1);
  if (sensor->set_wpc)
    sensor->set_wpc(sensor, 1);
  if (sensor->set_raw_gma)
    sensor->set_raw_gma(sensor, 1);

  if (sensor->status.framesize != CAPTURE_FRAME_SIZE) {
    haltForever("Camera did not accept the target still-photo frame size.");
  }

  Serial.printf("Camera ready: %ux%u JPEG, quality %u.\n", CAPTURE_WIDTH, CAPTURE_HEIGHT,
                JPEG_QUALITY);
}
