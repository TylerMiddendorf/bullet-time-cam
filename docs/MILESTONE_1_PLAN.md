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
- Do not initialize, read, write, or require camera-node microSD storage.
- Do not reserve or drive a camera-node GPIO for a status LED.
- Preserve original JPEG bytes without image normalization.
- Generate a separate display/export GIF from the available camera images.
- Keep the physical button connected directly to the shared ESP32S3 trigger line.
- Drive the same shared active-low trigger from Raspberry Pi BCM GPIO17 through the approved 2N3904 open-collector circuit; idle GPIO17 low and pulse it high for 100 ms.
- Treat USB `CAPTURE_STARTED` as the Pi notification path for either trigger source; do not add a Pi trigger-sense input.
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
- Determine whether the available powered USB hub carries data or only supplies power.
- Record the current firmware, board-core, PSRAM, and USB-CDC build settings.

Exit gate:

- The Pi boots reliably.
- A full-screen test image appears on the intended display.
- One camera node is visible to the Pi over USB.
- The remaining hardware unknowns are written down.

Evidence recorded June 27 and July 8, 2026 (partial; checkpoint remains open):

- A Windows bench host detected one connected XIAO as `COM6`, an ESP32 USB serial/JTAG device.
- Arduino CLI 1.5.1 with Espressif ESP32 core 3.3.10 compiled and uploaded `button_capture` using `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`.
- The compiled sketch used 424,233 bytes of flash and 33,568 bytes of dynamic memory.
- Upload verification identified an ESP32-S3 with 8 MB embedded PSRAM and verified all written image hashes.
- A bounded 115200-baud serial smoke test observed the 2048x1536 camera-ready, microSD-ready, and shared-trigger-ready messages.
- The repository skill at `.agents/skills/deploy-xiao-esp32s3-sense` repeats the guarded compile, upload, and startup verification workflow.
- The Raspberry Pi 4 was imaged successfully and boots to Raspberry Pi OS with its HDMI display working.
- The intended display is confirmed at 800x480 resolution, with HDMI for video and a micro-USB connection for touch and/or display-side power.
- Touch input on the intended display now works on the Raspberry Pi.
- One XIAO ESP32S3 camera node was identified by the Raspberry Pi as expected through the powered USB hub, confirming that the hub carries USB data for at least one node.
- On July 10, 2026, the Pi was verified on the bench LAN as `camerapi` at `10.0.0.136` with OpenSSH available. A dedicated ED25519 development key was installed and a fresh key-only login succeeded as user `username`; the verified Pi host-key fingerprint and non-secret operating instructions are in `RASPBERRY_PI_SSH.md`.
- Still unresolved for this checkpoint: touchscreen manufacturer/model/physical size, exact display power requirements, exact Raspberry Pi enumeration output for the connected XIAO, and whether a direct-to-Pi comparison should also be recorded.

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

- Keep node capture and USB transfer as separate operations without node-local storage.
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

## Checkpoint 4 - Active One-Node Full-System Bench Test

Status: active by product-owner decision on July 10, 2026

Cost gate: no purchase; use one node, the available powered data hub, Raspberry Pi, and touchscreen

Purpose:

Build the narrowest real vertical slice before completing the broader offline and transport-isolation work: one physical trigger causes one node to capture, transfers the JPEG directly over USB through the hub, the Pi validates and preserves it, performs representative display processing, and shows the result on the touchscreen. Checkpoints 2 and 3 are not complete; their necessary one-node elements are absorbed here, and their remaining multi-image/isolated-test coverage is deferred.

End-to-end path:

`physical shutter or Pi GPIO17 pulse -> one ESP32S3 -> frame-buffer JPEG -> USB hub -> Raspberry Pi -> validated original -> display artifact -> touchscreen`

Work:

- Refactor the node firmware so capture and USB transfer are separate operations; remove all node microSD code, messages, card checks, backup behavior, and deployment requirements.
- Remove the node status LED pin, self-test, timing, messages, and writes so `D0 / GPIO1` is unused.
- Until the physical button is wired for this bench setup, accept a framed Pi-to-node USB capture request. Treat this as test scaffolding and retain the physical-trigger path for later validation.
- Add Pi BCM GPIO17 output support and move normal touchscreen/Pi-initiated captures to a 100 ms hardware-trigger pulse. Do not send a USB `CAPTURE_REQUEST` for the same action; retain it only as explicitly selected test scaffolding if it remains useful.
- Emit framed, binary-safe messages containing protocol version, hardware UID, local capture sequence, event type, dimensions, byte length, payload checksum, and explicit completion/error status.
- Map the node UID to logical Camera 1 in Pi configuration.
- Implement a minimal Pi coordinator with `READY`, `LOADING`, `REVIEW`, and `REVIEW_WITH_ERROR` states.
- Receive into a temporary file, validate byte length and checksum, then atomically commit the original JPEG into a capture-set directory with `manifest.json`.
- Produce and display a representative processed artifact. For one image, this may be a single-frame/duplicated-frame GIF or the original JPEG, but the processing and display stages must remain separately timed so multi-image GIF cost can later be substituted cleanly.
- Keep the latest result visible until the next trigger and require no Pi desktop interaction during normal capture.
- Record errors without discarding a successfully validated original.

Required instrumentation for every run:

- Node monotonic timestamps: trigger accepted, frame acquisition started, frame ready, transfer started, and transfer completed.
- Pi monotonic timestamps: first capture event received, payload receive started/completed, validation completed, original committed, processing started/completed, display request issued, and first result visibly rendered when measurable.
- Derived durations: trigger-to-frame, transfer, validation, storage commit, processing, display update, and total trigger-to-review.
- Context: capture ID, node UID/logical ID, JPEG dimensions and bytes, checksum result, USB device/path, success/error, retry count, and software/firmware versions.
- Pi resource observations during capture, transfer, and processing: CPU load, memory use, and storage bytes written. Record available USB topology/link information; defer electrical power measurement until suitable instrumentation exists.
- Use monotonic clocks for durations. Because ESP32 and Pi clocks are not synchronized, derive cross-device total time from a Pi-observed capture-start event or record the clock-correlation method and uncertainty.

Validation sequence:

1. Demonstrate one complete trigger-to-screen capture and retain its manifest/log.
2. Run at least 20 consecutive full-resolution captures with zero truncation/checksum failures and no overwritten originals.
3. Disconnect/reconnect the node through the hub and confirm automatic rediscovery without code/config edits or a Pi reboot.
4. Force one interrupted transfer and confirm a partial file is not committed as a valid original and the UI reports the error.
5. Report median, p95, slowest, and failure count for each measured stage and total trigger-to-review.

Exit gate:

- One physical button press repeatedly produces one verified, preserved JPEG on the Pi without reading node microSD and displays the result on the touchscreen.
- The node remains logically Camera 1 after reconnect, and interrupted transfers fail safely.
- The manifest/log artifacts contain enough stage timing, size, integrity, resource, and failure data to project likely four-node bottlenecks and guide transport, processing, storage, timeout/retry, hub, and later power-test decisions.
- The results and limitations are recorded before Checkpoint 5 begins.

Decision after evidence:

Evaluate the one-node results against:

- Transfer latency
- Reconnect behavior
- CPU and memory use
- Power and wiring implications
- Expected four-node behavior
- Path toward 12+ nodes

Current direction after the one-node evidence:

- Continue with USB for version 1 while validating the physical trigger and four-node path; the measured vertical slice is reliable but still exceeds the soft two-second target.
- Run a focused Wi-Fi spike only if USB exposes a concrete blocker; do not build two complete production transports before the first end-to-end milestone.
- Extrapolation may identify risks, but final four-node concurrency and power behavior still require Checkpoints 5 and 7 measurements.

Evidence recorded July 10-11, 2026 (Checkpoint 4 remains active):

- Implemented and Git-deployed a CRC-protected `BTC1` USB protocol with PING/HELLO discovery, stable eFuse UID, capture request/start, JPEG image, transfer completion, ACK/NACK, LOG, and ERROR messages.
- Node `E072A1F9A190` is mapped to logical Camera 1. The Pi checkout at `/home/username/bullet-time-cam` was pulled from `origin/main`; firmware and Pi runtime tests were executed from that Git-tracked source.
- Demonstrated the temporary touchscreen/Pi USB request through the powered hub to a 2048x1536 frame-buffer JPEG, Pi checksum/length/decode validation, atomic original commit, manifest creation, and visible touchscreen review. The physical button was not connected for this test.
- Final resource-instrumented run: 20 consecutive captures, 20 complete manifests, zero checksum failures, zero recorded errors, zero leftover `.part` files.
- JPEG size: 554,270-byte median, 561,018-byte p95, and 561,320-byte maximum.
- Node trigger event to frame ready: 1,373.7 ms median, 1,407.2 ms p95, and 1,407.6 ms maximum. The existing settle/warm-up acquisition is the largest latency stage.
- Node USB transfer: 773.1 ms median, 783.5 ms p95, and 784.3 ms maximum. Pi payload receive: 643.2 ms median and 651.1 ms p95.
- Pi payload-received to atomic original commit: 35.9 ms median, 41.7 ms p95, and 63.8 ms maximum. JPEG decode validation was 0.296 ms median after warm-up.
- Capture event to display callback: 2,493.8 ms median, 2,580.0 ms p95, 2,588.4 ms maximum, and 2,422.4 ms minimum. None of this final run met the soft two-second target; acquisition and USB transfer are the primary optimization targets.
- Pi application CPU time from capture event through payload receipt: 220 ms median and 270 ms p95. Peak process RSS was about 59.9 MB median and 61.5 MB maximum; minimum available system memory remained about 1.48 GB and one-minute system load remained below 0.08.
- Terminating the receiver during a requested transfer left the manifest count unchanged and left no `.part` file. After the node's bounded ACK timeout, a new service rediscovered the same UID and completed a reviewed capture without a Pi reboot or configuration edit.
- Concrete evidence artifacts are under `docs/evidence/`, including the final 20-run summary, a successful review screenshot, recovery screenshot, representative manifest, and screenshots of defects found and fixed during integration.
- Two physical hub disconnect/reconnect cycles were completed. Kernel enumeration advanced from device 7 to 8 to 9 with the same serial number and `/dev/ttyACM0`; the same service process rediscovered logical Camera 1 without configuration edits or a Pi reboot.
- A later live disconnect visibly produced `No camera node found`, then returned to `Camera 1 connected` after reconnect. Its tapped capture completed before cable removal, so it demonstrates missing-node error presentation and recovery rather than a mid-payload interruption.
- On July 11, a test-only one-shot command deliberately changed one byte of the next live USB IMAGE payload while retaining the original CRC. The Pi independently detected `JPEG metadata checksum mismatch`, sent a targeted NACK, kept the touchscreen UI alive with a visible error, and committed neither a manifest/JPEG nor a `.part` file. Counts remained 44 manifests, 44 Camera 1 originals, and zero partials. The immediately following normal request succeeded as capture 45 with zero partials, and the normal UI service was restored active. Evidence: `docs/evidence/checkpoint4-live-nack.txt`, `checkpoint4-live-nack.png`, and `checkpoint4-live-nack-recovered.png`.
- At the end of the July 10-11 run, the node simplification, physical shared shutter, and Raspberry Pi GPIO17 initiation were still required. The node simplification was implemented and startup-verified on July 17; both hardware-trigger demonstrations remain open. The deliberately corrupted transfer requirement is satisfied. Electrical power and concurrent four-node measurements remain later validation work and are not replaced by this one-node test.
- Electrical power was not measured; suitable instrumentation is still required. One-node data cannot validate four-node hub contention or aggregate power.

Evidence recorded July 16, 2026:

- Built commit `f9729ea` for `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`, then wrote and verified the same firmware image set on all four Pi-attached nodes. All four cameras reached camera-ready and trigger-ready after flashing, but all four reported `microSD unavailable: card mount failed`; therefore deployment is not fully startup-verified and Checkpoint 4 remains open. The Pi receiver service was restored active and all four stable USB identities remained present. See `docs/evidence/four-node-flash-2026-07-16.md` for hashes, node identities, and exact limitations.

The July 16 result above is historical pre-revision evidence. Its card gate was valid for that firmware but is superseded by the July 17 node design.

Evidence recorded July 17, 2026 (Checkpoint 4 remains active):

- Pi inspection confirmed Raspberry Pi OS Trixie, kernel `6.18.34+rpt-rpi-v8`, Python 3.13.5, `/dev/gpiochip0`, application-user membership in `gpio`, and installed Raspberry Pi package `python3-lgpio` 0.2.2. Direct `lgpio` was selected as the smallest installed maintained backend.
- Implemented GPIO17 ownership behind an injectable abstraction. It claims BCM 17 LOW, pulses HIGH for the configured 100 ms, returns LOW in pulse-error cleanup, and writes LOW again before release/shutdown. Normal capture sends no USB `CAPTURE_REQUEST`; the USB request requires explicit `--diagnostic-usb-trigger` selection.
- `python -m unittest discover -s pi_app/tests -v` passed 13/13 tests, including initialization, one pulse, repeated pulses, exception cleanup, and mutually exclusive hardware/diagnostic selection.
- Compiled firmware 0.2.0 for `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`: 371,077 bytes flash and 33,368 bytes dynamic memory. Application image SHA-256: `275f9a9c5e18c7383cf1f4b1b4d55280c7070fac40ff1089fcc6f5f20d3f9ab0`.
- Flashed the same non-erase image set with esptool 5.3.1 to `E072A1F99CF8`, `E072A1F99CC0`, `E072A1F9A190`, and `E072A1F9B3E4`; every image write passed hash verification and every board reported 8 MB PSRAM.
- Bounded serial reads on all four nodes passed camera-ready (2048x1536 JPEG quality 8), BTC1 v1 protocol/matching eFuse UID, and shared-trigger-ready gates. No card marker was required or emitted.
- Detailed commands and hashes are in `docs/evidence/milestone1-trigger-refactor-2026-07-17.md`.
- Product-owner approval was received to push through `e365a0a`; `origin/main` and the Pi checkout match that revision. The Pi reran 13 tests successfully, the pinned installer completed with backup `20260717T194902Z`, and 30 persistent setup checks passed with only the intentionally stopped service reported inactive.
- Still required: unpowered circuit measurements, service startup/LOW claim verification, one physical-button capture, one Pi-pulse capture, and repeated timing/integrity/duplicate evidence. Startup verification is not capture or four-node concurrency proof.

## Checkpoint 5 - Four-Node Capture and Grouping

Cost gate: use the available powered data hub for initial four-node validation. Acquire a replacement hub or cabling only if measured four-node reliability, topology, or power behavior shows the bench hardware is inadequate.

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
- Keep the screen free of operating-system content during early boot, show `assets/Logo_800x480.png` throughout graphical/application startup, then hand directly to the full-screen camera UI without exposing Raspberry Pi firmware artwork, the desktop, a console/login prompt, a cursor, or startup diagnostics.

Exit gate:

- A real button press completes the full node-to-screen path without manual file movement.
- Complete and partial captures behave as defined.
- The user never needs to interact with the Pi desktop during normal capture.
- A filmed cold boot shows no operating-system or diagnostic frame; after an accepted blank early phase, only the product logo appears before the camera application.

Boot-presentation evidence recorded July 16-17, 2026 (visual sub-gate satisfied; integrated real-button flow remains open):

- The first hardware trial used Raspberry Pi's supported early fullscreen image helper, a custom static Plymouth script theme, a logo compositor background, and an app-owned logo first frame.
- Plymouth 24.004.60 crashed in `libply-splash-core`/`libply` before normal root startup; the display showed its backtrace and the Pi never reached networking or the application.
- Two timestamped pre-change backups were created under `/var/lib/bullet-time-boot-backups/` before the failed reboot.
- The repository follow-up removes the custom Plymouth theme, restores the distro `pix` theme as a fallback, and explicitly disables Plymouth. It retains the supported early fullscreen logo and matched compositor/application frames. SD-card recovery and a new cold-boot demonstration are still required.
- The recovered Pi booted when both splash mechanisms were absent, showing only the temporary recovery console before the app logo. A subsequent trial kept Plymouth disabled but re-enabled Raspberry Pi's early fullscreen logo; the Pi produced black/no-signal output and never reached networking. That early-logo path is therefore also rejected for the current OS/kernel.
- The next fallback disables both initramfs splash paths and the HDMI console, leaving a black pre-graphical display before matched compositor/application logo frames. It prioritizes reliable startup and no visible OS/debug output, but does not satisfy the stronger logo-throughout-boot requirement unless a later compatible early-display mechanism is found.
- After the early-logo package, hook, and payload were removed and initramfs rebuilt, a no-`tty1` boot still remained black and never reached networking. The otherwise identical recovery boot with `console=tty1` repeatedly reached userspace, networking, LightDM, and the camera application. The next trial retains but silences and masks that console instead of removing it.
- The masked/silenced `tty1` recovery boot reached networking, LightDM, and an isolated labwc session containing only the logo background and camera application. Re-running the installer then regenerated an already-clean initramfs; the following boot again remained blank and never reached networking. Setting `auto_initramfs=0` produced a successful direct-kernel cold boot (boot ID `a8e32deb-1d79-4964-831a-abe4d1d63197`): system, networking, LightDM, and camera service were active, the 15 automated boot checks passed, and the process list contained only labwc, the logo background, Xwayland, and the camera app. Physical confirmation of the displayed boot sequence remains required before closing the visual exit gate.
- Physical observation of that successful boot found two remaining console lines: `Completed socket interaction for boot stage local` and `... network`. The boot journal traced both to Raspberry Pi Imager's completed NoCloud/cloud-init provisioning pipeline, which tees stage output directly to `/dev/console`. The next trial disables cloud-init through its marker file and kernel-command-line switch and removes the retired `ds=nocloud` selector; visual verification remains open.
- The cloud-init-suppressed reboot showed no operating-system or diagnostic text and the user described the boot presentation as perfect through the application logo. One compositor pointer remained visible over that logo before Tk's cursor setting took control. The next trial installs a transparent Xcursor theme loaded by labwc before its autostart clients; cursor-only visual verification remains open.
- Final cold boot `3b377b08-599e-434e-bc40-948f24710254` loaded the transparent cursor theme into the logo background, Xwayland, and application processes. All 20 then-current automated boot checks passed, the application was active, and the product owner confirmed the result looked good with no remaining pointer or OS/debug frame. The accepted behavior and replacement-Pi procedure are recorded in `docs/RASPBERRY_PI_BOOT_RUNBOOK.md`.
- The replacement-Pi audit expanded verification to 28 checks and made the installer provision its pinned Python environment and LightDM autologin keys. A real installer rerun created backup `20260717T123705Z`; subsequent cold boot `a067e50f-99de-4080-b2fa-3198eec8e80a` passed all 28 checks, ran only labwc, swaybg, the camera app, and Xwayland, and contained no cloud-init stage messages. Package installation now uses `--no-upgrade` to preserve the selected image's existing desktop/session versions.

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

1. Checkpoint 1: Pi and display bring-up (substantially demonstrated; documentation details remain)
2. Checkpoint 4: active one-node full-system bench test
3. Deferred Checkpoint 2 coverage needed for four-image GIF and partial-set behavior
4. Deferred Checkpoint 3 coverage not already proven by Checkpoint 4
5. Checkpoint 5: four-node grouping and failure handling
6. Checkpoint 6: integrated live flow
7. Checkpoint 7: performance and reliability pass

This order produces visible progress early, isolates failures, and avoids buying hardware before its requirements are known.

## Immediate Next Actions

1. Complete and record the unpowered multimeter checks in `TRIGGER_CIRCUIT.md`, then start the installed service and verify GPIO17 is output LOW without pulsing it.
2. Verify repeated physical-trigger-to-touchscreen and Pi-trigger-to-touchscreen captures, with exactly one `CAPTURE_STARTED` and one JPEG per connected node and no duplicate USB request.
3. Record timing and integrity evidence for both trigger sources before closing Checkpoint 4.
4. Optimize or deliberately accept the measured camera-acquisition and USB-transfer latency before projecting the soft two-second target onto four nodes.
5. Register Cameras 2 through 4 by stable UID and extend the Pi coordinator for concurrent connections, capture grouping, partial sets, and camera-specific errors.
6. Validate all four nodes through the available powered hub before purchasing replacement hub hardware or integrated cabling.
7. Implement and measure the live four-image back-and-forth GIF/touchscreen path, then complete the performance and reliability pass.
8. Defer electrical power conclusions until suitable instrumentation is available; one-node software resource measurements are not a substitute for aggregate power data.
