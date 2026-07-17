#include "btc_protocol.h"

#include <Arduino.h>
#include <esp_mac.h>
#include <esp_system.h>
#include <string.h>

#include "firmware_config.h"

namespace {

uint32_t captureSequence = 0;
uint32_t bootId = 0;
char uid[13] = {};
uint8_t idleMagicMatched = 0;
bool corruptNextUsbImage = false;

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
    const size_t chunk = min(USB_CHUNK_SIZE, length - offset);
    const size_t written = Serial.write(data + offset, chunk);
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
  return writeAll(data, corruptOffset) && writeAll(&corrupted, 1) &&
         writeAll(data + corruptOffset + 1, length - corruptOffset - 1);
}

bool readInboundFrame(uint8_t &messageType, char *metadata,
                      size_t metadataCapacity) {
  const char magic[] = "BTC1";
  while (Serial.available()) {
    uint8_t value = Serial.read();
    idleMagicMatched =
        (value == static_cast<uint8_t>(magic[idleMagicMatched]))
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
        crc32Bytes(remainder, 20,
                   crc32Bytes(reinterpret_cast<const uint8_t *>("BTC1"), 4)) !=
            readU32Le(remainder + 20) ||
        metadataLength + 1 > metadataCapacity || payloadLength > 1024) {
      idleMagicMatched = 0;
      return false;
    }
    if (Serial.readBytes(reinterpret_cast<uint8_t *>(metadata), metadataLength) !=
        metadataLength) {
      idleMagicMatched = 0;
      return false;
    }
    metadata[metadataLength] = '\0';
    const uint32_t expectedMetadataCrc = readU32Le(remainder + 12);
    if (crc32Bytes(reinterpret_cast<const uint8_t *>(metadata), metadataLength) !=
        expectedMetadataCrc) {
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

}  // namespace

uint32_t crc32Bytes(const uint8_t *data, size_t length, uint32_t crc) {
  crc = ~crc;
  for (size_t i = 0; i < length; ++i) {
    crc ^= data[i];
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc >> 1) ^ (0xEDB88320UL & (0U - (crc & 1U)));
    }
  }
  return ~crc;
}

bool sendFrame(uint8_t messageType, const char *metadata,
               const uint8_t *payload, size_t payloadLength,
               bool corruptPayloadOnWire) {
  const size_t metadataLength = strlen(metadata);
  uint8_t header[28] = {};
  memcpy(header, "BTC1", 4);
  header[4] = PROTOCOL_VERSION;
  header[5] = messageType;
  writeU16Le(header + 6, 0);
  writeU32Le(header + 8, metadataLength);
  writeU32Le(header + 12, payloadLength);
  writeU32Le(
      header + 16,
      crc32Bytes(reinterpret_cast<const uint8_t *>(metadata), metadataLength));
  writeU32Le(header + 20,
             payloadLength ? crc32Bytes(payload, payloadLength) : 0);
  writeU32Le(header + 24, crc32Bytes(header, 24));
  return writeAll(header, sizeof(header)) &&
         writeAll(reinterpret_cast<const uint8_t *>(metadata), metadataLength) &&
         (!payloadLength ||
          (corruptPayloadOnWire
               ? writePayloadWithOneCorruptByte(payload, payloadLength)
               : writeAll(payload, payloadLength)));
}

void initializeNodeIdentity() {
  uint8_t mac[6];
  esp_efuse_mac_get_default(mac);
  snprintf(uid, sizeof(uid), "%02X%02X%02X%02X%02X%02X", mac[0], mac[1],
           mac[2], mac[3], mac[4], mac[5]);
  bootId = esp_random();
}

const char *nodeUid() { return uid; }

uint32_t nodeBootId() { return bootId; }

uint32_t currentCaptureSequence() { return captureSequence; }

uint32_t nextCaptureSequence() { return ++captureSequence; }

void sendNodeMessage(uint8_t messageType, uint32_t sequence,
                     uint64_t timestampUs, const char *message) {
  char metadata[384];
  snprintf(metadata, sizeof(metadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,"
           "\"timestamp_us\":%llu,\"message\":\"%s\"}",
           uid, static_cast<unsigned long>(bootId),
           static_cast<unsigned long>(sequence),
           static_cast<unsigned long long>(timestampUs), message);
  sendFrame(messageType, metadata);
}

void sendHelloFrame() {
  char metadata[320];
  snprintf(metadata, sizeof(metadata),
           "{\"node_uid\":\"%s\",\"boot_id\":%lu,\"capture_seq\":%lu,"
           "\"firmware_version\":\"0.2.0\",\"timestamp_us\":%llu}",
           uid, static_cast<unsigned long>(bootId),
           static_cast<unsigned long>(captureSequence),
           static_cast<unsigned long long>(esp_timer_get_time()));
  sendFrame(MSG_HELLO, metadata);
}

bool waitForHostAck(uint32_t sequence) {
  const unsigned long started = millis();
  char metadata[1024];
  char uidNeedle[48];
  char bootNeedle[48];
  char sequenceNeedle[48];
  snprintf(uidNeedle, sizeof(uidNeedle), "\"node_uid\":\"%s\"", uid);
  snprintf(bootNeedle, sizeof(bootNeedle), "\"boot_id\":%lu",
           static_cast<unsigned long>(bootId));
  snprintf(sequenceNeedle, sizeof(sequenceNeedle), "\"capture_seq\":%lu",
           static_cast<unsigned long>(sequence));
  while ((millis() - started) < HOST_ACK_TIMEOUT_MS) {
    uint8_t messageType = 0;
    if (!readInboundFrame(messageType, metadata, sizeof(metadata))) {
      delay(1);
      continue;
    }
    const bool matching = strstr(metadata, uidNeedle) &&
                          strstr(metadata, bootNeedle) &&
                          strstr(metadata, sequenceNeedle);
    if (matching && messageType == MSG_ACK) {
      return true;
    }
    if (matching && messageType == MSG_NACK) {
      return false;
    }
  }
  sendNodeMessage(MSG_ERROR, sequence, esp_timer_get_time(),
                  "HOST_ACK_TIMEOUT");
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
    sendNodeMessage(MSG_LOG, 0, esp_timer_get_time(),
                    "TEST_CORRUPTION_ARMED");
    return false;
  }
  return messageType == MSG_CAPTURE_REQUEST;
}

bool consumeCorruptNextUsbImage() {
  const bool shouldCorrupt = corruptNextUsbImage;
  corruptNextUsbImage = false;
  return shouldCorrupt;
}
