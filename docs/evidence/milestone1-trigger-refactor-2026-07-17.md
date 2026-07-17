# Milestone 1 Node Simplification and Trigger Refactor - July 17, 2026

Status: firmware implementation, compile, four-node flash/startup smoke verification, Raspberry Pi deployment, one-node trigger-to-screen demonstrations, and four-node physical/Pi/repeated functional trigger tests complete. The required unpowered multimeter inspection was skipped by product-owner choice, so the electrical-inspection gate remains unresolved.

## Implementation

- Removed the camera-node status LED, all `D0 / GPIO1` use, its self-test, writes, messages, and LED-only minimum-on delay.
- Removed node microSD includes, constants, initialization, filenames, card checks, writes, backup messages, and result coupling.
- Preserved `D1 / GPIO2` `INPUT_PULLUP`, the 40 ms debounce, direct OV3660 frame-buffer JPEG transfer, stable eFuse UID, `CAPTURE_STARTED`, `IMAGE`, `TRANSFER_COMPLETE`, ACK/NACK, reconnect discovery, and the deliberately corrupted-payload command.
- Added an injectable Raspberry Pi `lgpio` abstraction that claims BCM GPIO17 LOW, pulses HIGH for the configured 100 ms, returns LOW in a `finally` block, and writes LOW again before cleanup.
- Normal Pi/touchscreen capture selects one hardware pulse and sends no USB `CAPTURE_REQUEST`. The USB request remains available only with `--diagnostic-usb-trigger`.
- Capture manifests classify the initiating path as `pi_gpio17`, `physical_shared_bus`, or explicit `diagnostic_usb`; the analytics summarizer reports counts by trigger source.
- Selected Raspberry Pi OS Trixie's installed `python3-lgpio` 0.2.2 package. The Pi reports Debian 13, kernel `6.18.34+rpt-rpi-v8`, Python 3.13.5, `/dev/gpiochip0`, and membership of the application user in the `gpio` group.

Local test command:

```powershell
python -m unittest discover -s pi_app/tests -v
```

Result: 13 passed, 0 failed. Coverage includes BTC1 framing/integrity, normal hardware-only versus explicit diagnostic USB selection, GPIO initialization LOW, one 100 ms pulse, repeated pulses, and LOW/close cleanup after an injected exception.

## Firmware Build

Command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".agents\skills\deploy-xiao-esp32s3-sense\scripts\deploy_xiao.ps1" -CompileOnly -KeepBuild
```

Target: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`

- Application flash use: 371,077 bytes (11%)
- Dynamic memory use: 33,368 bytes (10%), leaving 294,312 bytes
- Application image: 371,232 bytes
- Application SHA-256: `275f9a9c5e18c7383cf1f4b1b4d55280c7070fac40ff1089fcc6f5f20d3f9ab0`
- Bootloader SHA-256: `3a06e81d78e928687d7acd8abcd069543a4413de4398e2e2940a97b3fc739fd8`
- Partition-table SHA-256: `1d9cca96de0fe07ad7fc0648b9878ddecd9ce565e38b589ad20fea698ed4c80c`
- Boot-app SHA-256: `f94c5d786a7a8fab06ac5d10e33bf37711a6697636dc037559ea19cc410a17f0`

## Four-Node Flash and Startup Smoke Test

The same non-erase image set was copied to `/tmp/esp32cam-deploy-20260717` on `camerapi`; Pi-side `sha256sum` matched the Windows build. `esptool` 5.3.1 wrote the standard images at `0x0`, `0x8000`, `0xe000`, and `0x10000` to all four stable `/dev/serial/by-id` devices. Every write reported `Hash of data verified`; each board identified as ESP32-S3 revision 0.2 with 8 MB embedded PSRAM.

Bounded post-flash serial reads observed all three revised deployment gates on every node:

| Stable eFuse UID | Camera ready | BTC1/identity ready | Trigger ready |
| --- | --- | --- | --- |
| `E072A1F99CF8` | 2048x1536 JPEG quality 8 | BTC1 v1, matching UID | shared active-low trigger ready |
| `E072A1F99CC0` | 2048x1536 JPEG quality 8 | BTC1 v1, matching UID | shared active-low trigger ready |
| `E072A1F9A190` | 2048x1536 JPEG quality 8 | BTC1 v1, matching UID | shared active-low trigger ready |
| `E072A1F9B3E4` | 2048x1536 JPEG quality 8 | BTC1 v1, matching UID | shared active-low trigger ready |

No node printed or required a card marker. This proves startup without node-card access; it does not by itself prove capture, transfer, physical-trigger behavior, Pi GPIO behavior, or four-node concurrency.

## Raspberry Pi Git Deployment

- Product-owner approval was received to push to `origin/main`.
- Local `main`, `origin/main`, and `/home/username/bullet-time-cam` were aligned at `0144180` by `git push origin main` and `git pull --ff-only origin main`.
- The Pi reran `python -m unittest discover -s pi_app/tests -v`: 13 passed, 0 failed.
- `sudo -n pi_app/scripts/install_boot_experience.sh` completed with backup `/var/lib/bullet-time-boot-backups/20260717T194902Z`.
- The pinned `python3-lgpio` package was already installed; the app venv now reports `include-system-site-packages = true` and imports `/usr/lib/python3/dist-packages/lgpio.py`.
- The persistent verifier passed all 30 setup checks after the service was started.
- Before activation, `pinctrl get 17` reported GPIO17 input/pull-down/LOW. After service start and after every later probe, it reported `GPIO17 = output`, pull-down, LOW. Starting the service did not change the capture-manifest count, so LOW initialization did not trigger a capture.

## Hardware Trigger Evidence

The product owner reported that the ground and trigger wiring was connected to the Pi and all four cameras while powered, explicitly declined the required unpowered inspection, and directed the functional testing to continue. Therefore these results validate observed function but not resistor values, transistor pinout, absence of hidden shorts, or the unpowered continuity/resistance gate.

### One-node storage/display workflow

- Starting the normal service claimed GPIO17 output LOW and produced no capture (`61` manifests before and after startup).
- One physical-button press produced exactly one committed/displayed capture: manifest `20260717T201911Z_e47521f8`, source `physical_shared_bus`, UID `E072A1F9A190`, sequence 2, 294,614 bytes, CRC32 `a63e9f12`, no errors, and 2,073.317 ms capture-event-to-display.
- One normal touchscreen tap produced exactly one committed/displayed capture and no diagnostic USB request: manifest `20260717T202133Z_c08c476d`, source `pi_gpio17`, UID `E072A1F9A190`, sequence 3, 299,828 bytes, CRC32 `83b39e3c`, no errors, and 2,065.389 ms capture-event-to-display.
- GPIO17 was output LOW after both actions, and the manifest count increased by exactly one for each action (`61 -> 62 -> 63`).

### Four-node single-action checks

Temporary bounded probes opened all four stable `/dev/serial/by-id` ports, issued `PING`, waited for matching `HELLO`, observed `CAPTURE_STARTED`, validated JPEG length/CRC/SOI/EOI, ACKed the image, and required `TRANSFER_COMPLETE` from every node.

- One physical-button press produced exactly one start, one valid image, and one completion on each of `E072A1F99CF8`, `E072A1F99CC0`, `E072A1F9A190`, and `E072A1F9B3E4`; duplicate count 0 and error count 0. Sizes/CRCs were 256,768/`95b5a08c`, 255,439/`62943c7e`, 300,023/`3332de57`, and 255,374/`4057ab3d`, respectively.
- One call to the real `HardwareTrigger(17, 0.1)` produced exactly one start, one valid image, and one completion per node; duplicate count 0 and error count 0. Sizes/CRCs were 240,549/`5e9ee49f`, 229,150/`793ed50e`, 286,761/`70607d59`, and 228,034/`cfb142e4`, respectively.
- The normal UI service was restored active after each bounded probe and GPIO17 was output LOW.

### Repeated four-node GPIO17 run

Command pattern used on the Pi:

```bash
systemctl --user stop checkpoint4-ui.service
/home/username/esp32cam-tools/bin/python /tmp/four_node_repeated_gpio_probe.py
systemctl --user start checkpoint4-ui.service
pinctrl get 17
```

An initial immediate second pulse, issued as soon as the last cycle-1 completion arrived, was intentionally not counted as a successful repeated run: only the node that had already been idle for more than the existing 40 ms release debounce accepted it. This measured the need for a post-transfer rearm interval; firmware debounce was not changed. The final probe waited 150 ms after all four completions before the next pulse.

Final result: 10/10 cycles completed, 40/40 `CAPTURE_STARTED` events, 40/40 CRC-valid JPEGs, and 40/40 `TRANSFER_COMPLETE` events; duplicate count 0 and error count 0. Every UID advanced through sequences 1-10. Pulse-to-all-completions was 2,455.029 ms median, 2,496.740 ms p95/maximum, and 2,436.666 ms minimum. Four-node `CAPTURE_STARTED` spread was 3.837 ms median and 4.930 ms p95/maximum. GPIO17 returned output LOW and the UI service returned active.

Named raw artifacts:

- `four-node-physical-trigger-2026-07-17.txt`
- `four-node-pi-trigger-2026-07-17.txt`
- `four-node-immediate-rearm-boundary-2026-07-17.txt`
- `four-node-repeated-gpio-2026-07-17.txt`

## Remaining Limitations

- The required unpowered multimeter inspection was not performed. Functional success does not substitute for that electrical-safety evidence, so Checkpoint 4 remains open on this explicit gate.
- The checked-in UI still commits/displays one configured camera. The four-node probes validate concurrent trigger/protocol/integrity behavior, not four-image atomic grouping, consolidated storage, animation creation, or four-image display; those remain later checkpoint work.
- No aggregate electrical power measurement was taken.
