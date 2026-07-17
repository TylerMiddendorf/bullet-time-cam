#pragma once

#include <Arduino.h>

constexpr uint8_t MSG_HELLO = 1;
constexpr uint8_t MSG_CAPTURE_STARTED = 2;
constexpr uint8_t MSG_IMAGE = 3;
constexpr uint8_t MSG_TRANSFER_COMPLETE = 4;
constexpr uint8_t MSG_ERROR = 5;
constexpr uint8_t MSG_LOG = 6;
constexpr uint8_t MSG_CAPTURE_REQUEST = 7;
constexpr uint8_t MSG_PING = 8;
constexpr uint8_t MSG_TEST_CORRUPT_NEXT_IMAGE = 9;
constexpr uint8_t MSG_ACK = 0x80;
constexpr uint8_t MSG_NACK = 0x81;

void initializeNodeIdentity();
const char *nodeUid();
uint32_t nodeBootId();
uint32_t currentCaptureSequence();
uint32_t nextCaptureSequence();

uint32_t crc32Bytes(const uint8_t *data, size_t length, uint32_t crc = 0);
bool sendFrame(uint8_t messageType, const char *metadata,
               const uint8_t *payload = nullptr, size_t payloadLength = 0,
               bool corruptPayloadOnWire = false);
void sendNodeMessage(uint8_t messageType, uint32_t sequence,
                     uint64_t timestampUs, const char *message);
void sendHelloFrame();
bool waitForHostAck(uint32_t sequence);
bool pollForUsbCaptureRequest();
bool consumeCorruptNextUsbImage();
