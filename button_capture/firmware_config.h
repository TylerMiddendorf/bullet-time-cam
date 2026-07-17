#pragma once

#include "esp_camera.h"

constexpr uint8_t CAMERA_COUNT = 4;
constexpr int TRIGGER_PIN = 2;  // XIAO D1 / GPIO2

constexpr uint16_t CAPTURE_WIDTH = 2048;
constexpr uint16_t CAPTURE_HEIGHT = 1536;
constexpr framesize_t CAPTURE_FRAME_SIZE = FRAMESIZE_QXGA;

constexpr uint8_t JPEG_QUALITY = 8;  // Lower is higher quality.
constexpr unsigned long LIGHT_SETTLE_MS = 700;
constexpr uint8_t WARMUP_FRAME_COUNT = 4;
constexpr gainceiling_t SENSOR_GAIN_CEILING = GAINCEILING_4X;
constexpr int SENSOR_SHARPNESS = 1;
constexpr int SENSOR_DENOISE = 1;

constexpr unsigned long TRIGGER_DEBOUNCE_MS = 40;
constexpr unsigned long HOST_ACK_TIMEOUT_MS = 10000;
constexpr size_t USB_CHUNK_SIZE = 4096;
constexpr uint8_t PROTOCOL_VERSION = 1;
