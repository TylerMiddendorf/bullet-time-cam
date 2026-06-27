---
name: deploy-xiao-esp32s3-sense
description: Build, flash, and verify this repository's Arduino camera firmware on a connected Seeed Studio XIAO ESP32S3 Sense. Use when Codex is asked to deploy, upload, flash, reinstall, or smoke-test `button_capture` firmware; diagnose board/port discovery; or confirm PSRAM, OV3660 camera, and microSD startup over serial after an upload.
---

# Deploy XIAO ESP32S3 Sense

Deploy with the bundled `scripts/deploy_xiao.ps1` helper. Treat a successful upload as incomplete until the bounded serial smoke test also passes.

## Workflow

1. Read the repository `AGENTS.md` and its required context before changing firmware.
2. Inspect `git status --short` and preserve unrelated user changes.
3. Confirm the intended sketch and board. Default to:
   - Sketch: `button_capture`
   - FQBN: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`
4. Discover the connected board. Let the helper select the port only when exactly one ESP32 serial device is present; otherwise pass `-Port COMx`.
5. Run the helper from the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".agents\skills\deploy-xiao-esp32s3-sense\scripts\deploy_xiao.ps1"
```

6. Report the selected port, compile result, upload result, and serial verification result. Do not claim the camera node works when only compilation or flashing succeeded.

## Options

Pass an explicit port when multiple ESP32 devices are attached:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".agents\skills\deploy-xiao-esp32s3-sense\scripts\deploy_xiao.ps1" -Port COM6
```

Use `-CompileOnly` to validate firmware without touching hardware. Use `-SkipVerify` only when serial access is intentionally unavailable, and state that hardware startup remains unverified. Use `-ArduinoCli <path>` when Arduino CLI is neither on `PATH` nor at the project's usual user-local CodexTools location.

## Guardrails

- Keep OPI PSRAM enabled. High-resolution capture depends on it.
- Pin the XIAO FQBN; do not replace it with the generic FQBN reported by USB discovery.
- Do not update or install the ESP32 core automatically. If compilation reports a missing core, explain the exact prerequisite and ask before using the network.
- Do not erase flash, alter partitions, clear microSD contents, or deploy to multiple boards unless the user explicitly asks.
- Expect the upload port to disappear and return during reset.
- Verify all three startup markers: camera ready, microSD ready, and trigger ready. Treat `Stopped.`, PSRAM errors, camera initialization errors, and card errors as failures.
- If no port appears, ask the user to enter bootloader mode: unplug USB, hold `BOOT`, reconnect USB, release `BOOT`, then retry discovery.

## Troubleshooting

- Port missing: check the USB cable carries data, retry bootloader mode, and rerun discovery.
- Port busy: close Arduino Serial Monitor or any other process using the COM port.
- Compile failure: preserve the full compiler diagnostic; verify the ESP32 core and exact FQBN before changing source.
- Upload failure after connecting: retry once in bootloader mode. Do not start changing camera code to solve a transport problem.
- Serial timeout: press reset once and rerun verification; report whether upload was successful but runtime startup was not observed.
- Camera or card failure: preserve the exact serial message and inspect hardware seating, FAT32 card presence, and power before modifying firmware.
