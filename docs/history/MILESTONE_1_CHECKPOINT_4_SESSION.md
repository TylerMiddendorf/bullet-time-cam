# Archived Session - Milestone 1 Checkpoint 4

Implementation dates: July 10-11, 2026

Status reviewed: July 17, 2026

Archive notice: this file preserves the Checkpoint 4 handoff as it existed on
July 17. Its present-tense work and next-action lists are historical; current
work is owned by `docs/CURRENT_SESSION.md` and the active milestone plan.

Objective: implement and verify the one-node trigger-to-touchscreen path through the powered USB hub, then replace the temporary normal USB request with the approved shared hardware-trigger path and collect the evidence required by Checkpoint 4.

## Status

Overall: Checkpoint 4 complete; handoff to Checkpoint 5 prepared

Current phase: simplified firmware and GPIO17 runtime are deployed; one-node physical/Pi trigger-to-screen, four-node single/repeated trigger functions, and the prescribed unpowered multimeter inspection are verified. Four-node product grouping is next.

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
- Created local implementation commit `416cb91` and evidence/documentation commit `e365a0a`. After explicit product-owner approval, pushed `main` to `origin/main` and fast-forwarded the Pi checkout from `d0e735a` to `e365a0a`.
- Reran the Pi test suite at `e365a0a`: 13 passed, 0 failed. Shell syntax checks for the installer, verifier, and session launcher also passed.
- Ran the pinned installer successfully. It preserved backup `/var/lib/bullet-time-boot-backups/20260717T194902Z`, found `python3-lgpio` 0.2.2 already installed, and changed the application venv to expose system packages. The venv now imports `/usr/lib/python3/dist-packages/lgpio.py`.
- The persistent verifier passed 30 configuration checks; its sole expected failure was `camera app is active` because the service remains deliberately stopped pending the circuit check. Read-only `pinctrl get 17` showed GPIO17 as an input with pull-down and LOW; the application has not claimed or pulsed it.
- Pushed documentation commit `0144180` to `origin/main` and fast-forwarded the Pi checkout to the same commit. The normal service was then started; `pinctrl get 17` showed output/pull-down/LOW, and the unchanged count of 61 manifests proved initialization did not create a capture.
- The product owner initially connected Pi ground/trigger and all four cameras while powered before the prescribed multimeter inspection. Functional tests proceeded; later on July 17 the product owner completed the full unpowered checklist and reported all continuity, resistance, button, isolation, and no-direct-short checks passing. Individual readings were not retained.
- One physical press through the normal Camera 1 service produced exactly one committed/displayed capture (`20260717T201911Z_e47521f8`, source `physical_shared_bus`, UID `E072A1F9A190`, sequence 2, 294,614 bytes, CRC32 `a63e9f12`, no errors, 2,073.317 ms event-to-display).
- One normal touchscreen tap produced exactly one committed/displayed capture (`20260717T202133Z_c08c476d`, source `pi_gpio17`, sequence 3, 299,828 bytes, CRC32 `83b39e3c`, no errors, 2,065.389 ms event-to-display). The path used one 100 ms GPIO17 pulse and no USB `CAPTURE_REQUEST`.
- A bounded four-port observer verified one physical press and, separately, one real 100 ms GPIO17 pulse. Each action produced exactly one `CAPTURE_STARTED`, one CRC/length/SOI/EOI-valid JPEG, and one `TRANSFER_COMPLETE` on all four stable UIDs, with zero errors and zero duplicates.
- The first repeated GPIO probe pulsed again immediately after the last transfer completed. Only the node that had already spent over 40 ms back in its trigger loop rearmed; the other three correctly ignored the pulse. This measured the existing release-debounce boundary, so the firmware debounce was preserved and the probe added a 150 ms post-completion rearm interval.
- The final 10-cycle four-node GPIO17 run passed 40/40 starts, valid JPEGs, and completions with zero errors and zero duplicates. Pulse-to-all-completions was 2,455.029 ms median and 2,496.740 ms p95/maximum; four-node start spread was 3.837 ms median and 4.930 ms p95/maximum. Every UID completed sequences 1-10. The service was restored active and GPIO17 output LOW.
- Replaced the planned separate removable media-card path with the product owner's added USB drive. The application now parses mountinfo/sysfs to require a writable USB-backed filesystem, can request an automatic `udisks2` mount, creates `BulletTime/`, records storage details in manifests, supports a preferred mount name, and never falls back to the boot microSD. Local tests now pass 19/19.
- Read-only Pi inspection found `/dev/sda1`, a removable 231 GB FAT partition labeled `USB DISK`, initially unmounted. A direct SSH `udisksctl` call was denied as expected for a non-local session; the exact non-interactive command then succeeded from the camera user-service context, mounting at `/media/username/USB DISK`. The mount is writable by `username`, and `/sys/dev/block/8:1` resolves through the Pi's USB topology. No application JPEG/GIF commit has yet been deployed or run against it.
- A later live SSH inventory confirmed the product owner's final V1 hub/cabling is installed: VIA Labs `2109:3431` feeds Terminus `1a40:0101`, with all four stable ESP32 identities on the downstream hub at 12 Mb/s. The touchscreen and removable USB drive also enumerate on this chain.
- The same inventory reports HDMI-A-2 at 800x480 and 65.681 Hz, a 150x100 mm physical area, generic EDID make/model `Addi-Data GmbH 0x0004`, and USB touch controller `8888:6666`. The USB interface advertises 5 V / 100 mA maximum; this is not a measured whole-display/backlight load.
- Added the four-node persisted-evidence validator, CLI, ledger template, deterministic scenario tests, environment-gated physical-rig test, and `FOUR_NODE_E2E_TEST_PLAN.md`. The full local suite passes 23 tests with the one live-hardware test skipped until capture-root and ledger paths are supplied.

## Evidence Collected

- Pi environment and USB topology evidence is listed in the progress log above.
- Current local Pi/protocol/fake-GPIO/storage/E2E-validator result: 23 tests passed, 0 failed, with one physical-rig evidence test skipped until live paths are supplied.
- Revised firmware compile, four-node non-erase upload, flash hashes, camera startup, BTC1 protocol/stable identity, and trigger-ready verification passed.
- The retained `docs/evidence/milestone-1/checkpoint-4/checkpoint4-idle-error.png` documents the initial idle-timeout defect and is not READY-state evidence.
- USB-diagnostic, physical-button, and Pi-GPIO trigger-to-screen behavior are verified on Camera 1. Literal hub unplug/replug, missing-node UI recovery, and live corrupt-payload/NACK/no-commit/recovery are also verified.
- Concurrent four-node physical, Pi, and 10-cycle repeated trigger/protocol/integrity behavior is verified by bounded observers. Raw logs are `docs/evidence/milestone-1/checkpoint-4/four-node-physical-trigger-2026-07-17.txt`, `four-node-pi-trigger-2026-07-17.txt`, `four-node-immediate-rearm-boundary-2026-07-17.txt`, and `four-node-repeated-gpio-2026-07-17.txt`.
- Live NACK evidence is retained in `docs/evidence/milestone-1/checkpoint-4/checkpoint4-live-nack.txt`, `checkpoint4-live-nack.png`, and `checkpoint4-live-nack-recovered.png`.

## Historical Handoff Work

- Keep the normal Pi user service active; it currently owns GPIO17 as output LOW while idle.
- Git-deploy and validate the USB-only storage implementation against the mounted drive, including a real capture and removal/failure behavior.
- Continue next with four-image grouping/atomic commit/display; the temporary observers are not the product four-camera workflow.
- Use `FOUR_NODE_E2E_TEST_PLAN.md` and its ledger after the four-node coordinator exists.

## Blockers and Limitations

- Electrical power analytics require suitable measurement hardware and are outside this software-only session unless such hardware is already attached and accessible.
- The four-node observers validate concurrent USB transfer integrity, but the checked-in UI still processes one configured node and does not yet atomically group four images or create/display the final animation.
- The USB drive's enumeration, service-context mount, and write permission are verified, but the new code has not been deployed to the Pi and no JPEG/GIF application commit, unplug/replug, full, read-only, corrupt, or mid-write removal test has been recorded.

## Historical Next Actions

1. Git-deploy the USB storage code and record one real capture plus missing-drive/unplug-replug behavior on the Pi.
2. Build the checked-in four-node capture grouping, atomic persistence, animation, and touchscreen review path using the validated shared-trigger/protocol behavior.
3. Run the comprehensive physical-rig E2E sequence and validator, then retain its ledger and evidence.
4. Use suitable external instrumentation for electrical power measurements when available.
5. Optimize the measured acquisition and USB-transfer bottlenecks; the repeated four-node run remains above the soft two-second target.
