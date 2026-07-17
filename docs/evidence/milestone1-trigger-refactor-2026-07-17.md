# Milestone 1 Node Simplification and Trigger Refactor - July 17, 2026

Status: firmware implementation, compile, four-node flash/startup smoke verification, and stopped-service Raspberry Pi deployment complete; electrical trigger demonstrations pending.

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
- Local `main`, `origin/main`, and `/home/username/bullet-time-cam` were aligned at `e365a0a` by `git push origin main` and `git pull --ff-only origin main`.
- The Pi reran `python -m unittest discover -s pi_app/tests -v`: 13 passed, 0 failed.
- `sudo -n pi_app/scripts/install_boot_experience.sh` completed with backup `/var/lib/bullet-time-boot-backups/20260717T194902Z`.
- The pinned `python3-lgpio` package was already installed; the app venv now reports `include-system-site-packages = true` and imports `/usr/lib/python3/dist-packages/lgpio.py`.
- The persistent verifier passed 30 setup checks. Its only failure was the deliberately stopped `checkpoint4-ui.service`.
- `pinctrl get 17` reported `GPIO17 = input`, pull-down, LOW. This is a read-only pre-activation observation, not proof that the application claimed the pin LOW.

## Pending Hardware Gates

- The product owner must confirm the unpowered multimeter checks in `docs/TRIGGER_CIRCUIT.md` before GPIO17 is pulsed.
- The revised service is installed but intentionally stopped until the unpowered circuit checks are confirmed. GPIO17 has not been claimed or pulsed by the application.
- No physical-button capture or Pi-initiated hardware capture has been performed with this revision.
- No repeated hardware-trigger timing/integrity run or duplicate-capture count exists yet.
- Checkpoint 4 remains active, and this startup evidence is not four-node capture-concurrency proof.
