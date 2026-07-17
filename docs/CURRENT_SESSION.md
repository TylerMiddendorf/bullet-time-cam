# Current Session - Milestone 1 Checkpoint 4

Implementation dates: July 10-11, 2026

Status reviewed: July 17, 2026

Objective: implement and verify the one-node trigger-to-touchscreen path through the powered USB hub, then replace the temporary normal USB request with the approved shared hardware-trigger path and collect the evidence required by Checkpoint 4.

## Status

Overall: in progress

Current phase: simplified firmware is flashed and startup-verified on four nodes; Raspberry Pi GPIO code is implemented and fake-backend tested, but Git deployment, unpowered circuit inspection, and both real trigger demonstrations remain open

## Progress Log

Entries through the live-NACK work describe the historical pre-revision firmware and its then-valid card/LED deployment gates. They are preserved as dated evidence and superseded by the July 17 implementation entries below.

- Started the Checkpoint 4 implementation session.
- Read the canonical project documents, Raspberry Pi SSH guide, current firmware, and repository deployment skill.
- Confirmed the documented SSH target is `camerapi` and that key-based access is intended for non-interactive development.
- Confirmed the firmware must retain the XIAO ESP32S3 target with OPI PSRAM and that deployment is not complete until camera, microSD, and trigger startup markers pass.
- Began Raspberry Pi OS, USB topology, display-session, Python, and dependency inventory before implementation.
- Verified SSH access to `camerapi` and recorded Debian 13, kernel 6.18.34, Python 3.13.5, 6.7 GiB free root storage, and approximately 1.5 GiB available RAM.
- Recorded the XIAO as Espressif `303a:1001`, serial `E0:72:A1:F9:A1:90`, at `/dev/ttyACM0` through the powered hub chain. `lsusb -t` reports a 12 Mb/s full-speed USB link.
- Confirmed the Pi already has pyserial 3.5, Pillow 11.1.0, psutil 7.0.0, and Tkinter; no application dependency purchase or installation is required.
- Implemented the `BTC1` CRC-protected binary framing protocol, direct frame-buffer JPEG transfer, stable eFuse UID and boot identity, Pi ACK/NACK, atomic original persistence, manifest generation, resource/timing capture, reconnect discovery, and fullscreen loading/review/error UI.
- Added protocol tests for binary round-trip, startup-text resynchronization, and corrupt-payload rejection; all three pass.
- Compiled the modified firmware successfully for `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`: 427,761 bytes flash and 33,632 bytes dynamic memory.
- Installed `esptool` 5.3.1 into an isolated Pi user virtual environment because the node is physically attached to the Pi and no flashing tool was already available there.
- Flashed only the application partition at `0x10000`; 427,904 bytes were written and the flash hash verified. The bootloader and partition table were not erased or replaced.
- Passed bounded post-flash startup verification: ESP32-S3 with 8 MB PSRAM, 2048x1536 camera ready, microSD ready, and shared trigger ready.
- Recorded stable node UID `E072A1F9A190` and mapped it to logical Camera 1 in Pi configuration.
- Launched the application in the active Pi Wayland session and captured its visible state. The first screenshot exposed that an idle serial timeout was incorrectly surfaced as an end-of-stream error; the corrected parser now distinguishes idle waits from partial-frame failures.
- Product owner clarified that the physical button is not currently set up. Implementing a temporary framed USB capture request from the touchscreen/Pi while retaining the physical trigger path.
- Added the Pi runtime requirements and user-service definition to the repository so the running code can be deployed through Git.
- Added temporary touchscreen/USB `CAPTURE_REQUEST` support, bounded HELLO/UID discovery, matching capture ACK validation, IMAGE-to-TRANSFER_COMPLETE transaction finalization, explicit integrity evidence, and corrected payload-only USB timing.
- Made USB capture success independent of optional node microSD backup; missing/failed backup no longer blocks or changes a Pi-committed USB result.
- Expanded protocol tests to five passing cases, including capture request framing and partial-frame failure classification. Reviewed firmware compiles successfully at 428,677 bytes flash and 33,632 bytes dynamic memory.
- Created and pushed the reviewed one-node implementation commit; see the following Git deployment entry for the final amended hash.
- Session-scoped GitHub authorization was granted. Commit `80cb048` was pushed to `origin/main`, cloned to `/home/username/bullet-time-cam`, explicitly pulled and verified clean at the same hash, then built and flashed from that committed source.
- Pi-side tests and the post-flash camera/microSD/trigger startup smoke test passed. The first committed-source USB-trigger run exposed a HELLO timeout because the earlier smoke test consumed the one boot-time HELLO and later serial opens did not reset the node. Added an explicit framed PING/HELLO response handshake; verification is in progress.
- After the PING/HELLO fix, one USB request successfully produced a verified 552,763-byte 2048x1536 JPEG and complete manifest. Measured capture-event-to-display-callback was 2,536.8 ms; node transfer was 763.3 ms and Pi payload receive was 633.9 ms. The screenshot then exposed that the later optional `SD_BACKUP_SAVED` LOG replaced the review image. LOG messages are now prevented from changing UI state, and a Git-tracked sequential trigger-count mode is being added for the 20-run test.
- The first repeated-run attempt committed its first image but the node reported `HOST_ACK_TIMEOUT`. The ACK unnecessarily repeated all image metadata (about 387 framed bytes), risking ESP32 CDC RX-buffer overflow during the transmit-to-receive transition. ACK/NACK responses are being reduced to only the validated transaction identity and short status/error fields before repeating the 20-run test.
- Compact transaction-identity ACK/NACK messages eliminated the repeated-run stall.
- Completed a clean 20-capture run, then repeated a final 20-capture run after correcting CPU instrumentation. The final run completed 20/20 with zero checksum failures, zero recorded errors, and no `.part` files.
- Final-run median/p95: capture event to display 2,493.8/2,580.0 ms; node acquisition 1,373.5/1,407.0 ms; node transfer 773.1/783.5 ms; Pi payload receive 643.2/651.1 ms; commit 35.9/41.7 ms; process CPU 220/270 ms. Peak application RSS was 61.5 MB maximum.
- Terminated the receiver during transfer: no manifest or partial file was committed. A fresh service then rediscovered logical Camera 1 and completed another reviewed capture without a Pi reboot.
- Confirmed a literal software USB disconnect is unavailable to the unprivileged Pi user: the device `authorized` sysfs control is root-owned and `uhubctl` is not installed.
- Linked the Git-tracked `checkpoint4-ui.service` into the Pi user service manager, enabled it for the user default target, and verified it active from `/home/username/bullet-time-cam`. Retained visible READY-state evidence showing Camera 1 at `/dev/ttyACM0` with touchscreen capture available.
- Verified two physical unplug/replug cycles through the hub. The XIAO re-enumerated from USB device 7 to 8 to 9 with the same serial number; the same service process returned to logical Camera 1 without a Pi reboot or configuration edit.
- During a later live disconnect, retained visible `No camera node found` error evidence and visible Camera 1 recovery evidence. The tapped capture completed before unplug, so this test is not classified as an in-flight interruption.
- Added an inert-until-commanded, one-shot corrupt-payload test path. Firmware computes the IMAGE CRC over the original JPEG and changes one payload byte only on the wire; the Pi retains header metadata, independently detects the mismatch, sends a targeted NACK, and keeps the UI alive.
- Built the updated XIAO firmware for `esp32:esp32:XIAO_ESP32S3:PSRAM=opi` at 428,965 bytes flash and 33,632 bytes dynamic memory. Flashed the 429,120-byte application image only at `0x10000`; the write hash verified. Post-flash camera, microSD, and shared-trigger startup checks passed with 8 MB PSRAM detected.
- Ran the live fault test through the powered hub. The Pi reported `NACK sent: JPEG metadata checksum mismatch`, the touchscreen visibly displayed the error, and counts remained 44 manifests, 44 Camera 1 originals, and zero `.part` files.
- Ran an immediate normal recovery request. It committed and displayed capture 45 with zero `.part` files. Stopped the transient test unit and restored the normal `checkpoint4-ui.service` active.
- Independently completed and visually accepted the product-boot presentation on July 17: reliable direct-kernel boot, cloud-init disabled after provisioning, isolated labwc session, matched compositor/application logo frames, no visible OS/debug content, and a transparent compositor cursor. The replacement-Pi process is recorded in `docs/RASPBERRY_PI_BOOT_RUNBOOK.md`.
- Audited replacement-Pi reproducibility, expanded the installer to provision runtime dependencies and deterministic LightDM autologin, expanded verification from 20 to 28 checks, and completed a successful post-install cold boot. The installer preserves existing image package versions with `apt-get install --no-upgrade`.
- Inspected the Pi GPIO environment before implementation: Raspberry Pi OS Trixie, kernel `6.18.34+rpt-rpi-v8`, Python 3.13.5, `/dev/gpiochip0`, the application user in `gpio`, and maintained Raspberry Pi package `python3-lgpio` 0.2.2 installed.
- Removed every firmware status-LED and node-storage path. `D0 / GPIO1` is unused; `D1 / GPIO2` remains `INPUT_PULLUP` with the existing 40 ms debounce; BTC1 transfer, stable eFuse UID, ACK/NACK, corruption test, and reconnect behavior remain.
- Added an injectable direct-`lgpio` GPIO17 controller with configured BCM pin 17 and 100 ms pulse. Initialization, idle, pulse-finally, and shutdown cleanup all drive LOW. Normal actions produce one hardware pulse and no USB `CAPTURE_REQUEST`; diagnostic USB triggering requires an explicit flag.
- Added manifest/summary trigger-source analytics so later evidence distinguishes `pi_gpio17`, `physical_shared_bus`, and explicit `diagnostic_usb` captures instead of assuming every capture was USB-requested.
- Local test command `python -m unittest discover -s pi_app/tests -v` passed 13 tests with zero failures. This includes normal-versus-diagnostic selection, GPIO initialization, one pulse, repeated pulses, and cleanup after an injected exception.
- Repository deployment helper compile succeeded for `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`: 371,077 bytes flash, 33,368 bytes dynamic memory, and 371,232-byte application image with SHA-256 `275f9a9c5e18c7383cf1f4b1b4d55280c7070fac40ff1089fcc6f5f20d3f9ab0`.
- Flashed the same non-erase image set to all four attached identities with esptool 5.3.1. Every write hash verified, and all four boards reported ESP32-S3 revision 0.2 with 8 MB PSRAM.
- Bounded post-flash serial output passed camera-ready, BTC1/matching eFuse identity, and trigger-ready gates on `E072A1F99CF8`, `E072A1F99CC0`, `E072A1F9A190`, and `E072A1F9B3E4`. No node-storage marker was expected or emitted.
- Created local implementation commit `416cb91`. Direct push to `origin/main` was blocked pending explicit product-owner approval, so the Pi checkout/service has not been updated and the stopped service has not touched GPIO17.

## Evidence Collected

- Pi environment and USB topology evidence is listed in the progress log above.
- Current Pi/protocol/fake-GPIO test result: 13 tests passed, 0 failed.
- Revised firmware compile, four-node non-erase upload, flash hashes, camera startup, BTC1 protocol/stable identity, and trigger-ready verification passed.
- The retained `docs/evidence/checkpoint4-idle-error.png` documents the initial idle-timeout defect and is not READY-state evidence.
- USB-request-to-screen behavior and recovery are verified. Physical-button behavior is not verified because the button is not connected.
- Literal hub unplug/replug, general missing-node UI recovery, and the live corrupt-payload/NACK/no-commit/recovery path are verified. Electrical power and concurrent four-node behavior were not measured.
- Live NACK evidence is retained in `docs/evidence/checkpoint4-live-nack.txt`, `checkpoint4-live-nack.png`, and `checkpoint4-live-nack-recovered.png`.

## Active Work

- Keep the Pi user service stopped until commit `416cb91` is explicitly approved for push/pull and the revised runtime is installed.
- After deployment, initialize GPIO17 LOW but do not pulse until the unpowered breadboard checks are confirmed.
- Then demonstrate physical-button and Pi-initiated capture separately and run the repeated integrity/timing/duplicate test.

## Blockers and Limitations

- Publishing commit `416cb91` to `origin/main` requires explicit product-owner approval.
- Unpowered multimeter validation and a physical trigger press require the product owner at the bench.
- Electrical power analytics require suitable measurement hardware and are outside this software-only session unless such hardware is already attached and accessible.
- One-node measurements cannot validate four-node USB contention or aggregate power behavior.

## Next Actions

1. Approve pushing `416cb91`, then pull/install/verify the Pi runtime and confirm GPIO17 initializes LOW.
2. Record the unpowered circuit measurements and validate the physical shared button plus one Pi hardware pulse without duplicates.
3. Run repeated captures and record timing, integrity, node identity, failures, and duplicate count.
4. Use suitable external instrumentation for electrical power measurements when available.
5. Optimize the measured acquisition and USB-transfer bottlenecks before assuming the four-node path can meet the soft two-second target.
