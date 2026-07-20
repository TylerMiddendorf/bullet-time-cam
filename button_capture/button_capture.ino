#include <Arduino.h>

#include "btc_protocol.h"
#include "camera_capture.h"
#include "firmware_config.h"
#include "trigger_input.h"

void setup() {
  const size_t usbTxBufferBytes = Serial.setTxBufferSize(USB_TX_BUFFER_BYTES);
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.printf("XIAO ESP32S3 Sense %u-Camera Shared Trigger\n",
                static_cast<unsigned int>(CAMERA_COUNT));
  if (usbTxBufferBytes != USB_TX_BUFFER_BYTES) {
    Serial.printf("Stopped. USB TX buffer allocation failed: requested %u, received %u.\n",
                  static_cast<unsigned int>(USB_TX_BUFFER_BYTES),
                  static_cast<unsigned int>(usbTxBufferBytes));
    while (true) {
      delay(1000);
    }
  }

  initializeSharedTrigger();
  initializeNodeIdentity();
  initializeCamera();

  Serial.printf("USB protocol ready: BTC1 v%u, node UID %s.\n", PROTOCOL_VERSION, nodeUid());
  Serial.println("Ready. Pull the shared trigger LOW to capture.");
  sendHelloFrame();
}

void loop() {
  const bool captureRequested = pollForUsbCaptureRequest();
  if (sharedTriggerPressed() || captureRequested) {
    capturePhoto();
  } else if (consumeUsbPreviewRequest() && sendPreviewFrame()) {
    capturePhoto();
  }
  delay(5);
}
