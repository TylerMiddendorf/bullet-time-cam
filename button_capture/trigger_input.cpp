#include "trigger_input.h"

#include <Arduino.h>

#include "firmware_config.h"

namespace {

bool lastRawTriggerState = HIGH;
bool stableTriggerState = HIGH;
unsigned long lastTriggerChangeMs = 0;

}  // namespace

void initializeSharedTrigger() {
  pinMode(TRIGGER_PIN, INPUT_PULLUP);
  lastRawTriggerState = digitalRead(TRIGGER_PIN);
  stableTriggerState = lastRawTriggerState;
  lastTriggerChangeMs = millis();
}

bool sharedTriggerPressed() {
  const bool rawState = digitalRead(TRIGGER_PIN);
  if (rawState != lastRawTriggerState) {
    lastRawTriggerState = rawState;
    lastTriggerChangeMs = millis();
  }
  if ((millis() - lastTriggerChangeMs) < TRIGGER_DEBOUNCE_MS || rawState == stableTriggerState) {
    return false;
  }
  stableTriggerState = rawState;
  return stableTriggerState == LOW;
}
