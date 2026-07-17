#include <Arduino.h>

#include "btc_protocol.h"
#include "camera_capture.h"
#include "firmware_config.h"
#include "trigger_input.h"

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.printf("XIAO ESP32S3 Sense %u-Camera Shared Trigger\n",
                static_cast<unsigned int>(CAMERA_COUNT));

  initializeSharedTrigger();
  initializeNodeIdentity();
  initializeCamera();

  Serial.printf("USB protocol ready: BTC1 v%u, node UID %s.\n",
                PROTOCOL_VERSION, nodeUid());
  Serial.println("Ready. Pull the shared trigger LOW to capture.");
  sendHelloFrame();
}

void loop() {
  if (sharedTriggerPressed() || pollForUsbCaptureRequest()) {
    capturePhoto();
  }
  delay(5);
}
