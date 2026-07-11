# Current Session - Milestone 1 Checkpoint 4

Date: July 10, 2026

Objective: implement and verify the one-node physical-trigger-to-touchscreen path through the powered USB hub, while collecting the evidence required by Checkpoint 4.

## Status

Overall: in progress

Current phase: add and verify temporary USB-triggered end-to-end capture

## Progress Log

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

## Evidence Collected

- Pi environment and USB topology evidence is listed in the progress log above.
- Local protocol test result: 3 tests passed, 0 failed.
- Firmware compile, application-partition upload, flash hash, camera startup, microSD startup, and trigger-ready verification passed.
- Trigger-to-screen behavior is not yet verified.
- The retained `docs/evidence/checkpoint4-idle-error.png` documents the initial idle-timeout defect and is not READY-state evidence.

## Active Work

- Deploy the compiled firmware to the node attached to the Pi.
- Deploy the Pi application and run remote tests.
- Verify firmware startup and execute physical trigger tests.
- Commit and push the PING/HELLO correction, pull it on the Pi, rebuild/flash from that checkout, and repeat the temporary USB-trigger test.

## Blockers and Limitations

- A physical trigger press may require the product owner if it cannot be initiated safely through existing hardware.
- Electrical power analytics require suitable measurement hardware and are outside this software-only session unless such hardware is already attached and accessible.
- One-node measurements cannot validate four-node USB contention or aggregate power behavior.

## Next Actions

1. Record Pi system, USB, serial-device, display-session, and dependency details.
2. Implement and locally validate the firmware and Pi application.
3. Deploy the firmware to the single connected node and verify startup.
4. Deploy/run the Pi application and execute the available end-to-end tests.
5. Record concrete results in this session log and the milestone documents.
