# Four-Node Firmware Flash - July 16, 2026

Firmware source: repository commit `f9729eab21bc7fa171870fa1e165af505706916b` with a clean firmware diff at build time.

Build target: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi` using Espressif Arduino core 3.3.10.

Build result:

- Application flash: 428,965 bytes
- Dynamic memory: 33,632 bytes
- Bootloader SHA-256: `3a06e81d78e928687d7acd8abcd069543a4413de4398e2e2940a97b3fc739fd8`
- Partition table SHA-256: `1d9cca96de0fe07ad7fc0648b9878ddecd9ce565e38b589ad20fea698ed4c80c`
- Boot app SHA-256: `f94c5d786a7a8fab06ac5d10e33bf37711a6697636dc037559ea19cc410a17f0`
- Application SHA-256: `6116f965577d7dbd52159953cda3528ed12cd5dc85cd21c210ad419cb58f1e1d`

The four images were copied to the Raspberry Pi and their hashes matched before flashing. `esptool` 5.3.1 wrote and verified the standard non-erase image set at offsets `0x0`, `0x8000`, `0xe000`, and `0x10000` on all four stable USB identities:

- `E072A1F99CF8`
- `E072A1F99CC0`
- `E072A1F9A190`
- `E072A1F9B3E4`

All four uploads succeeded. On bounded serial startup checks, every node initialized its OV3660 camera at 2048x1536 JPEG and reached `Ready. Pull the shared trigger LOW to capture.` Every node also reported `microSD unavailable: card mount failed; USB capture remains enabled.` Node `E072A1F99CF8` produced the same card-mount failure after one reset-and-recheck.

Result: firmware deployment succeeded on all four boards, but the deployment is not fully verified because none passed the required microSD-ready marker. Card seating, FAT32 card presence/condition, Sense expansion-board seating, and shared USB power should be inspected before changing firmware. No physical-trigger capture was performed during this deployment.

The Pi `checkpoint4-ui.service` was restored after flashing and was active at postflight. All four stable `/dev/serial/by-id` links were present.
