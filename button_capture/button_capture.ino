#include "esp_camera.h"
#include "FS.h"
#include "SD.h"
#include "SPI.h"

#if __has_include("esp_idf_version.h")
#include "esp_idf_version.h"
#endif

#define CAMERA_MODEL_XIAO_ESP32S3
#include "camera_pins.h"

static const uint8_t CAMERA_COUNT = 4;

// Wire this pin from all four XIAO boards together. The shared trigger bus is
// idle HIGH and a normally-open button pulls it to the common GND rail.
static const int TRIGGER_PIN = 2;  // XIAO D1 / GPIO2
static const int STATUS_LED_PIN = 1;  // XIAO D0 / GPIO1
static const int SD_CS_PIN = 21;  // Onboard Sense microSD chip-select
static const char *PHOTO_DIR = "/photos";

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
static const unsigned long MIN_STATUS_LED_ON_MS = 1000;

static bool lastRawTriggerState = HIGH;
static bool stableTriggerState = HIGH;
static unsigned long lastTriggerChangeMs = 0;
static uint16_t nextPhotoNumber = 1;

void halt(const char *message) {
  Serial.println(message);
  Serial.println("Stopped. Fix the issue and press Reset.");
  while (true) {
    delay(1000);
  }
}

bool ensurePhotoDirectory() {
  if (SD.exists(PHOTO_DIR)) {
    File dir = SD.open(PHOTO_DIR);
    if (!dir) {
      return false;
    }

    bool ok = dir.isDirectory();
    dir.close();
    return ok;
  }

  return SD.mkdir(PHOTO_DIR);
}

uint16_t findNextPhotoNumber() {
  char path[40];

  for (uint16_t number = 1; number < 10000; number++) {
    snprintf(path, sizeof(path), "%s/photo_%04u.jpg", PHOTO_DIR, static_cast<unsigned int>(number));
    if (!SD.exists(path)) {
      return number;
    }
  }

  return 0;
}

bool writeJpegToSd(const char *path, const uint8_t *data, size_t len) {
  File file = SD.open(path, FILE_WRITE);
  if (!file) {
    Serial.printf("Failed to open %s for writing.\n", path);
    return false;
  }

  size_t written = file.write(data, len);
  file.flush();
  file.close();

  if (written != len) {
    Serial.printf("Write failed for %s: wrote %u of %u bytes.\n",
                  path,
                  static_cast<unsigned int>(written),
                  static_cast<unsigned int>(len));
    return false;
  }

  return true;
}

void finishStatusLed(unsigned long ledStartedAt) {
  unsigned long elapsed = millis() - ledStartedAt;
  if (elapsed < MIN_STATUS_LED_ON_MS) {
    delay(MIN_STATUS_LED_ON_MS - elapsed);
  }

  digitalWrite(STATUS_LED_PIN, LOW);
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
  if (nextPhotoNumber == 0) {
    Serial.println("No available photo filename below photo_9999.jpg.");
    return false;
  }

  Serial.println("Capturing photo...");
  digitalWrite(STATUS_LED_PIN, HIGH);
  unsigned long ledStartedAt = millis();

  delay(LIGHT_SETTLE_MS);
  if (!discardWarmupFrames()) {
    Serial.println("Failed to settle camera before capture.");
    finishStatusLed(ledStartedAt);
    return false;
  }

  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Failed to get camera frame buffer.");
    finishStatusLed(ledStartedAt);
    return false;
  }

  bool ok = false;

  if (fb->format != PIXFORMAT_JPEG) {
    Serial.printf("Capture was not JPEG. Format code: %d\n", fb->format);
  } else if (fb->width != CAPTURE_WIDTH || fb->height != CAPTURE_HEIGHT) {
    Serial.printf("Capture was %ux%u, not target %ux%u. Not saving.\n",
                  static_cast<unsigned int>(fb->width),
                  static_cast<unsigned int>(fb->height),
                  CAPTURE_WIDTH,
                  CAPTURE_HEIGHT);
  } else {
    char path[40];
    snprintf(path, sizeof(path), "%s/photo_%04u.jpg", PHOTO_DIR, static_cast<unsigned int>(nextPhotoNumber));

    if (writeJpegToSd(path, fb->buf, fb->len)) {
      Serial.printf("Saved %s (%ux%u, %u bytes)\n",
                    path,
                    static_cast<unsigned int>(fb->width),
                    static_cast<unsigned int>(fb->height),
                    static_cast<unsigned int>(fb->len));
      nextPhotoNumber = findNextPhotoNumber();
      ok = true;
    }
  }

  esp_camera_fb_return(fb);
  finishStatusLed(ledStartedAt);
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

void initializeSdCard() {
  Serial.println("Initializing microSD...");

  if (!SD.begin(SD_CS_PIN)) {
    halt("Card Mount Failed.");
  }

  uint8_t cardType = SD.cardType();
  if (cardType == CARD_NONE) {
    halt("No SD card attached.");
  }

  if (!ensurePhotoDirectory()) {
    halt("Failed to create or open /photos directory.");
  }

  nextPhotoNumber = findNextPhotoNumber();
  if (nextPhotoNumber == 0) {
    halt("No available photo filename below photo_9999.jpg.");
  }

  Serial.printf("microSD ready: %s, next file photo_%04u.jpg.\n",
                PHOTO_DIR,
                static_cast<unsigned int>(nextPhotoNumber));
}

void runStatusLedSelfTest() {
  Serial.println("Testing status LED...");
  digitalWrite(STATUS_LED_PIN, HIGH);
  delay(1500);
  digitalWrite(STATUS_LED_PIN, LOW);
}

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.printf("XIAO ESP32S3 Sense %u-Camera Shared Trigger\n",
                static_cast<unsigned int>(CAMERA_COUNT));

  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  pinMode(STATUS_LED_PIN, OUTPUT);
  digitalWrite(STATUS_LED_PIN, LOW);
  runStatusLedSelfTest();

  lastRawTriggerState = digitalRead(TRIGGER_PIN);
  stableTriggerState = lastRawTriggerState;
  lastTriggerChangeMs = millis();

  initializeCamera();
  initializeSdCard();

  Serial.println("Ready. Pull the shared trigger LOW to capture.");
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

  delay(5);
}
