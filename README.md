# Handheld Four-Camera Bullet-Time Rig

<p align="center">
  <img src="assets/Logo_800x480.png" alt="Bullet-time camera project logo" width="480">
</p>

This repository contains the firmware, Raspberry Pi application, deployment
configuration, tests, and evidence for a handheld four-camera bullet-time rig.
Four Seeed Studio XIAO ESP32S3 Sense nodes capture synchronized viewpoints and
stream their original JPEGs to a Raspberry Pi. The Pi preserves the originals
on removable USB storage, creates the back-and-forth animation, and presents the
result on an integrated 800x480 touchscreen.

Version 1 deliberately prioritizes a reliable four-image capture-to-review path.
Alignment, appearance matching, interpolation, live preview, settings, battery
integration, and the enclosure advance only through the milestones defined in
the project roadmap.

## Repository Map

| Path | Purpose |
| --- | --- |
| `button_capture/` | Modular XIAO ESP32S3 camera, trigger, and BTC1 USB firmware |
| `pi_app/bullettime/` | Raspberry Pi capture runtime, receiver, grouping coordinator, media/GIF pipeline, UI, protocol, metrics, GPIO, and storage |
| `pi_app/evidence/` | Persisted capture-evidence validation library |
| `pi_app/tests/` | Deterministic unit, storage, protocol, GPIO, and environment-gated hardware tests |
| `pi_app/tools/` | Serial smoke, capture summaries, evidence validation, and local sample-data tools |
| `pi_app/scripts/`, `session/`, `systemd/` | Reproducible Raspberry Pi boot and product-session deployment |
| `photos/` | Local-only ignored camera/sample images; only its instructions are tracked |
| `docs/` | Canonical product context, roadmap, plans, decisions, runbooks, and indexed evidence |
| `.agents/skills/` | Repository-scoped Codex deployment workflow for attached camera nodes |

## Current State

Milestone 1 is active. Checkpoint 4—the one-node trigger-to-screen vertical
slice and four-node trigger/protocol integrity gates—is complete. Checkpoint 5,
product-level four-node grouping and partial-failure handling, is next.

The current firmware streams directly from each camera frame buffer without
node-local storage. The Pi runtime supports CRC-checked transfer, stable node
identity, atomic USB-media persistence, GPIO17 hardware triggering, timing and
resource instrumentation, reconnect recovery, and the accepted full-screen boot
presentation. The detailed evidence and remaining gates are maintained in the
roadmap and active milestone plan rather than duplicated here.

## Camera Firmware

The sketch target is `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`. With Arduino CLI and
the Espressif ESP32 core installed:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/build_firmware.ps1
arduino-cli upload -p COM3 --fqbn "esp32:esp32:XIAO_ESP32S3:PSRAM=opi" --input-dir ".build/button_capture" button_capture
```

Replace `COM3` with the discovered device. A deployment is not accepted until
serial output confirms camera readiness, BTC1 identity, and shared-trigger
readiness. The repository-scoped deployment skill under `.agents/skills/` also
implements those guarded checks.

The shared physical trigger uses XIAO `D1 / GPIO2`. Raspberry Pi BCM GPIO17 may
activate the same bus only through the documented 2N3904 open-collector circuit;
never connect a Pi output directly to the shared trigger bus. Follow
[`docs/TRIGGER_CIRCUIT.md`](docs/TRIGGER_CIRCUIT.md) before changing wiring.

## Raspberry Pi Application

Install the Python requirements in an environment that can also access the
pinned Raspberry Pi OS `python3-lgpio` package, then run from the repository
root:

```bash
python3 -m unittest discover -s pi_app/tests -v
python3 -m pi_app.bullettime.main --config pi_app/config.json
```

Use `--headless` for receiver/storage testing. Normal touchscreen capture pulses
GPIO17; the USB `CAPTURE_REQUEST` path is diagnostic scaffolding and requires the
explicit `--diagnostic-usb-trigger` option.

The product boot/session installer provisions `bullet-time-ui.service`:

```bash
sudo pi_app/scripts/install_boot_experience.sh
sudo reboot
pi_app/scripts/verify_boot_experience.sh
```

See [`pi_app/README.md`](pi_app/README.md) and the
[`Raspberry Pi boot runbook`](docs/RASPBERRY_PI_BOOT_RUNBOOK.md) for prerequisites,
recovery, and hardware-specific limitations.

## Development Quality Checks

Install the development tooling and both Git hooks from the repository root:

```bash
python -m pip install -r requirements-dev.txt
pre-commit install --install-hooks
```

The commit hook checks repository hygiene, detects accidentally committed private
keys and merge markers, lints and formats Python with Ruff, and formats the
Arduino/C++ firmware with ClangFormat. Hooks that rewrite a file stop the commit
so the resulting change can be reviewed and staged. The push hook runs the full
deterministic Python suite; the physical four-camera evidence test remains
environment-gated and skips unless its live evidence paths are supplied.

Run the same checks manually at any time:

```bash
pre-commit run --all-files
pre-commit run --hook-stage pre-push --all-files
```

GitHub Actions repeats formatting, linting, and deterministic tests for every
pull request and every push to `main`. Configure the `Formatting, linting, and
tests` check as required in the `main` branch protection rule to prevent a
failing change from being merged.

## Local Sample Images

Images under `photos/` are never tracked. Generate the deterministic local
offline dataset—including the deliberate Camera 4 missing-image scenario—with:

```bash
python -m pi_app.tools.prepare_sample_photos
```

See [`photos/README.md`](photos/README.md) for its layout and overwrite behavior.

## Project Documentation

Start with [`docs/README.md`](docs/README.md), which indexes document ownership
and evidence locations. The canonical changing project state lives in:

- [`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md) — product goal, architecture, decisions, and current state
- [`docs/ROADMAP.md`](docs/ROADMAP.md) — milestone ordering, status, and budget gates
- [`docs/MILESTONE_1_PLAN.md`](docs/MILESTONE_1_PLAN.md) — active checkpoint tests and exit criteria
- [`docs/CURRENT_SESSION.md`](docs/CURRENT_SESSION.md) — current Checkpoint 5 implementation handoff
- [`docs/INTERVIEW.md`](docs/INTERVIEW.md) — product-owner decision history

Successful hardware demonstrations are recorded under the indexed
`docs/evidence/` hierarchy. Historical session logs are under `docs/history/`.

## Storage Rule

The Raspberry Pi boots from a protected internal microSD card. User JPEGs,
manifests, and GIFs are written below `BulletTime/` on a writable USB-backed
filesystem. The application intentionally fails closed when suitable removable
USB storage is unavailable; it does not silently use the boot card.

## License

See [`LICENSE`](LICENSE).
