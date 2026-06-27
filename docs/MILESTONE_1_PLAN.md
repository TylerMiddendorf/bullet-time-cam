# Milestone 1 Plan - Bench-Top End-to-End Capture

## Outcome

Prove the complete version 1 data path on the bench:

`shared shutter -> four ESP32S3 nodes -> Raspberry Pi -> preserved JPEGs -> GIF -> touchscreen`

Battery integration, removable user media, and enclosure work are intentionally outside this milestone. Milestone 1 may temporarily store capture sets on the Raspberry Pi boot filesystem.

## Working Technical Direction

- Use the Raspberry Pi 4B 2 GB already on hand.
- Build the Pi application in Python unless the touchscreen or measured performance exposes a reason not to.
- Use USB as the first live-transfer transport.
- Keep transport behind an interface so Wi-Fi can be added without rewriting capture grouping, media handling, or the UI.
- Send each JPEG directly from the ESP32S3 camera frame buffer.
- Preserve original JPEG bytes without image normalization.
- Generate a separate display/export GIF from the available camera images.
- Keep the physical button connected directly to the shared ESP32S3 trigger line.
- Have each node report capture start immediately so the Pi can enter its loading state and group events from one press.

These are implementation recommendations for the milestone, not irreversible product decisions.

## Checkpoint 1 - Bench Inventory and Pi Bring-Up

Cost gate: no purchase

Work:

- Record the touchscreen manufacturer, model, size, native resolution, display interface, touch interface, and power requirements.
- Install or verify Raspberry Pi OS on the protected internal boot card.
- Verify the touchscreen displays the desktop or a full-screen test image.
- Verify touch input if the display provides it, although touch interaction is not required for version 1.
- Connect one XIAO ESP32S3 directly to the Pi and record how it enumerates.
- Determine whether the existing battery hub carries data or only supplies power.
- Record the current firmware, board-core, PSRAM, and USB-CDC build settings.

Exit gate:

- The Pi boots reliably.
- A full-screen test image appears on the intended display.
- One camera node is visible to the Pi over USB.
- The remaining hardware unknowns are written down.

Evidence recorded June 27, 2026 (partial; checkpoint remains open):

- A Windows bench host detected one connected XIAO as `COM6`, an ESP32 USB serial/JTAG device.
- Arduino CLI 1.5.1 with Espressif ESP32 core 3.3.10 compiled and uploaded `button_capture` using `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`.
- The compiled sketch used 424,233 bytes of flash and 33,568 bytes of dynamic memory.
- Upload verification identified an ESP32-S3 with 8 MB embedded PSRAM and verified all written image hashes.
- A bounded 115200-baud serial smoke test observed the 2048x1536 camera-ready, microSD-ready, and shared-trigger-ready messages.
- The repository skill at `.agents/skills/deploy-xiao-esp32s3-sense` repeats the guarded compile, upload, and startup verification workflow.
- Still unresolved for this checkpoint: Raspberry Pi enumeration, Pi boot/display verification, touchscreen identification, and whether the existing battery hub carries USB data.

## Checkpoint 2 - Offline Media and UI Vertical Slice

Cost gate: no purchase

Use the JPEGs already under `photos/` so Pi software can progress before camera transfer changes.

Work:

- Define a capture-set directory containing:
  - `manifest.json`
  - `camera_01.jpg` through `camera_04.jpg` when available
  - `bullet_time.gif`
- Include capture ID, logical camera IDs, dimensions, byte counts, timing, and errors in the manifest.
- Build the GIF from images ordered by logical camera number.
- Make forward/backward playback configurable; an initial test sequence can be `1,2,3,4,3,2`.
- Keep GIF resolution, frame delay, and looping configurable until they are chosen from touchscreen and performance tests.
- Implement a minimal full-screen state machine:
  - `READY` or the last result
  - `LOADING`
  - `REVIEW`
  - `REVIEW_WITH_ERROR`
- Keep the latest animation visible until the next simulated capture.
- Exercise complete sets `photo_0001` through `photo_0006`.
- Use the missing Camera 4 `photo_0007` as the first partial-capture test.
- Measure JPEG loading, GIF generation, and display time on the Pi.

Exit gate:

- Existing repository photos produce a preserved capture set and animated GIF.
- The touchscreen moves through loading and review states.
- The partial set produces a usable result and identifies Camera 4 as missing.
- Stage timings are recorded.

## Checkpoint 3 - One-Node Direct USB Transfer

Cost gate: no purchase

Work:

- Refactor the node firmware so capture, optional node storage, and transfer are separate operations.
- Emit a capture-start event immediately after the debounced trigger is accepted.
- Add a binary-safe protocol with, at minimum:
  - Protocol version
  - Stable hardware UID
  - Local capture sequence number
  - Event or message type
  - JPEG width, height, and byte length
  - JPEG payload
  - CRC32 or equivalent integrity check
  - Explicit success/error response
- Keep human-readable diagnostics inside framed protocol messages so logs cannot corrupt JPEG payloads.
- Hold the camera frame buffer until transfer succeeds or the transfer attempt ends.
- On the Pi, discover the node, receive to a temporary file, verify length and checksum, then atomically rename the JPEG into its capture set.
- Map the hardware UID to logical Camera 1 in Pi configuration rather than compiling different firmware for each board.
- Instrument trigger accepted, frame ready, transfer start/end, validation, and file commit times.

Proposed transfer test:

- 20 consecutive full-resolution transfers
- Zero checksum or truncation failures
- Reconnect the USB cable and confirm the node is rediscovered without editing code

Exit gate:

- One physical button press produces one verified JPEG on the Pi without reading the node microSD card.
- The node is identified consistently after reconnect.
- Measured transfer time is recorded.

## Checkpoint 4 - Transport Decision Gate

Cost gate: decide before buying a hub

Evaluate one-node USB results against:

- Transfer latency
- Reconnect behavior
- CPU and memory use
- Power and wiring implications
- Expected four-node behavior
- Path toward 12+ nodes

Decision:

- Continue with USB for version 1 if results are reliable and compatible with the soft two-second target.
- Run a focused Wi-Fi transfer spike only if USB exposes a concrete blocker or if a comparison is still needed to make the decision.
- Do not build two complete production transports before the first end-to-end milestone.

Exit gate:

- The version 1 transport choice and supporting measurements are recorded.
- Any required hub/cabling specification is known before purchase.

## Checkpoint 5 - Four-Node Capture and Grouping

Cost gate: acquire a powered data hub only after Checkpoint 4 confirms USB

Work:

- Register all four hardware UIDs as logical Cameras 1 through 4.
- Listen to all node connections concurrently.
- Create a central capture ID when the first capture-start event for a button press arrives.
- Group the other node events into that capture using a bounded arrival window and local sequence/timing metadata.
- Lock out or safely queue a second capture while the current set is active.
- Receive and validate all available JPEGs.
- Preserve successful images even when one node fails.
- Close a set only when all expected nodes have completed or the defined no-progress timeout is reached.
- Write camera-specific errors into `manifest.json` and surface them to the UI.

Proposed grouping tests:

- 25 consecutive normal four-camera captures
- One forced disconnect for each logical camera
- One corrupted or truncated transfer test
- One node reboot between captures
- No images assigned to the wrong capture set

Exit gate:

- Normal presses reliably form four-image capture sets.
- Forced failures form valid partial sets with the correct camera-specific error.
- Reconnection does not change logical camera numbering.

## Checkpoint 6 - Integrated GIF and Touchscreen Flow

Cost gate: no additional purchase

Work:

- Connect the live capture coordinator to the offline media/UI vertical slice.
- Switch to `LOADING` on the first capture-start event.
- Preserve every successfully transferred original.
- Generate the back-and-forth GIF from cameras in logical order.
- Display the new animation until another capture starts.
- Overlay or accompany partial results with the failed camera number and useful details.
- Keep the loading state active while progress continues beyond two seconds.
- Avoid an automatic recapture of a missed moment; transfer retries may reuse the retained frame buffer when safe.

Exit gate:

- A real button press completes the full node-to-screen path without manual file movement.
- Complete and partial captures behave as defined.
- The user never needs to interact with the Pi desktop during normal capture.

## Checkpoint 7 - Performance and Reliability Pass

Cost gate: no purchase

Record these timestamps for each node and capture set:

- Trigger accepted
- Frame ready
- Transfer started
- Transfer completed
- Original committed
- GIF completed
- First frame displayed

Use the measurements to separate:

- Existing 700 ms settle and warm-up cost
- Sensor capture cost
- USB transfer cost
- Storage cost
- GIF-generation cost
- Display-update cost

Validation:

- Run at least 25 additional normal capture cycles.
- Record median, slowest, and failure count.
- Confirm normal results approach the soft two-second target.
- Confirm active progress keeps the loading screen alive.
- Confirm no original is overwritten or assigned to the wrong set.
- Confirm the app recovers after node disconnect/reconnect without a Pi reboot.
- Confirm incomplete captures remain reviewable and preserved.

Exit gate:

- Milestone 1 behavior is repeatable rather than a one-shot demo.
- Remaining latency and reliability limitations are measured and documented.
- The requirements for removable media, battery sizing, and enclosure layout are clearer than estimates.

## Recommended Build Order

1. Checkpoint 1: Pi and display bring-up
2. Checkpoint 2: offline GIF/UI using existing photos
3. Checkpoint 3: one-node direct USB transfer
4. Checkpoint 4: transport decision
5. Checkpoint 5: four-node grouping and failure handling
6. Checkpoint 6: integrated live flow
7. Checkpoint 7: performance and reliability pass

This order produces visible progress early, isolates failures, and avoids buying hardware before its requirements are known.

## Immediate Next Actions

1. Identify the touchscreen model and interfaces.
2. Boot the Pi and confirm the touchscreen.
3. Copy or clone this repository onto the Pi.
4. Implement the offline capture-set/GIF/UI slice using the existing photos.
5. Only then modify one camera node for direct USB JPEG transfer.
