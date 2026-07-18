# Refactor Hardware Regression - July 17, 2026

## Scope and revision ordering

This run verifies the repository-organization and Arduino/Pi module split at
commit `b950740892766477674ce35215a474b7939a1906` on the physical four-camera
bench. The local checkout was clean, `origin/main` was independently resolved
to the same commit, and the commit was already pushed before the Raspberry Pi
ran `git pull --ff-only origin main`. The Pi checkout was then clean at that
exact revision before any device-side test or installation.

This is regression evidence for the completed Checkpoint 4 hardware path. It
does not demonstrate the Checkpoint 5 four-image coordinator, grouped atomic
persistence, or GIF review.

## Automated tests and firmware build

- On the Pi, the 24 normal tests under `pi_app/tests` passed; the one
  environment-gated physical-rig E2E test was intentionally skipped because its
  evidence inputs were not supplied.
- The repository deployment helper compiled
  `button_capture/button_capture.ino` for
  `esp32:esp32:XIAO_ESP32S3:PSRAM=opi` without erase or partition changes.
- Flash usage was 371,157 bytes and dynamic-memory usage was 33,368 bytes.
- The application image was 371,312 bytes with SHA-256
  `d359ecb0cfbc738cf28250404ebc12d92a756a05e36a885d5ea7a243712e668c`.
- The exact retained images were copied to the Pi and hash-checked before use.

## Four-node deployment and startup gates

The application image was written at `0x10000` through each stable
`/dev/serial/by-id` path with esptool 5.3.1 at 460800 baud. Every write reported
`Hash of data verified`; every node reported an ESP32-S3 revision 0.2 with 8 MB
PSRAM. No flash erase or bootloader/partition rewrite was performed.

| Node UID | Pi device during verification | Camera gate | Protocol/identity gate | Trigger gate |
| --- | --- | --- | --- | --- |
| `E072A1F99CF8` | `/dev/ttyACM0` | 2048x1536, JPEG quality 8 | BTC1 v1, matching UID | shared trigger ready |
| `E072A1F99CC0` | `/dev/ttyACM1` | 2048x1536, JPEG quality 8 | BTC1 v1, matching UID | shared trigger ready |
| `E072A1F9A190` | `/dev/ttyACM2` | 2048x1536, JPEG quality 8 | BTC1 v1, matching UID | shared trigger ready |
| `E072A1F9B3E4` | `/dev/ttyACM3` | 2048x1536, JPEG quality 8 | BTC1 v1, matching UID | shared trigger ready |

Each node passed a bounded 20-second post-flash serial smoke test. No stopped or
error state was observed.

## Repeated physical-rig regression

With the application service stopped and all four ports observed concurrently,
10 real GPIO17 pulses were issued with a 150 ms rearm interval after each
completed cycle:

- 40/40 expected capture starts, valid images, and completions were observed.
- All JPEGs passed length, CRC, SOI, and EOI validation.
- Every node advanced through sequences 1-10.
- Duplicate captures: 0; protocol/capture errors: 0.
- Pulse-to-all-completions ranged from approximately 2,974 to 3,067 ms; maximum
  was 3,066.976 ms.
- Maximum first-start spread across the four nodes was 4.660 ms.

This observer validates concurrent firmware trigger/transfer integrity only; it
does not substitute for the product-level four-image grouping required by
Checkpoint 5.

## Pi installation, storage capture, and reboot

The pulled installer migrated the user service from `checkpoint4-ui.service` to
`bullet-time-ui.service` and created backup
`/var/lib/bullet-time-boot-backups/20260718T000535Z`. Before reboot, the complete
boot verifier passed all 33 checks. A normal GPIO-triggered application capture
then committed a valid Camera 1 JPEG to `/dev/sda1` below the mounted `USB DISK`
`BulletTime/` directory.

The Pi was rebooted after this validation. Its boot ID changed from
`a067e50f-99de-4080-b2fa-3198eec8e80a` to
`6731d5a8-0c0d-4e36-ac99-ff132d04f967`; SSH was observed unavailable during the
restart before the new boot became reachable. After reboot:

- `verify_boot_experience.sh` again passed all 33 checks.
- The Pi checkout remained clean at `b950740892766477674ce35215a474b7939a1906`.
- `bullet-time-ui.service` was active and the legacy unit was absent.
- GPIO17 was output, pull-down, LOW.
- All four stable serial identities were present.
- `/dev/sda1` was mounted read/write at `/media/username/USB DISK`.
- The expected `labwc`, `swaybg`, application, and Xwayland processes were
  present; desktop panel/file-manager processes were absent.

A second normal application capture was deliberately run after that reboot:

- Capture ID: `20260718T001318Z_c1fafcf3`
- Trigger: `pi_gpio17`
- Node: logical Camera 1, UID `E072A1F9A190`
- Image: 2048x1536 JPEG, 428,435 bytes
- Manifest status/errors: `complete` / none
- Expected and computed CRC32: `d6bfb4b6`
- JPEG SHA-256:
  `97cf873ff75c64dd3a7b4d4b777c574e7c4a6fe902e8278cbdc341ae35fc5187`
- Storage: USB transport, `/dev/sda1`
- Capture-event-to-payload: 2,048.352 ms
- Host payload receive: 481.272 ms
- Node transfer: 581.254 ms
- Payload-to-commit: 329.006 ms

After the test the product service was restored active and GPIO17 was again
confirmed output LOW.

## Limitations

The automated boot configuration, service, process, device, storage, GPIO, and
post-reboot capture gates all passed. The physical touchscreen itself was not
visible over SSH during this run, so this regression does not add a new visual
claim about transient frames on the display; the separately recorded July 17
physical product-boot acceptance remains the visual evidence for that behavior.
