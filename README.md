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
| `designs/ux-mockups/` | Non-binding V1, fast-follow, and future touchscreen design concepts |
| `docs/` | Canonical product context, roadmap, plans, decisions, runbooks, and indexed evidence |
| `.agents/skills/` | Repository-scoped Codex deployment workflow for attached camera nodes |

## Current State

Milestone 1 is complete. The physical shared shutter and normal touchscreen
trigger both drive the integrated four-node path through validated originals,
atomic manifests, ordered six-frame GIF generation, and full-screen review.
Camera-specific partial captures preserve and display the successful views.

Firmware 0.2.3 streams directly from each camera frame buffer without node-local
storage. The Pi runtime supports concurrent CRC-checked transfer, stable node
identity, atomic USB-media persistence, GPIO17 hardware triggering, ordered GIFs,
camera-specific partial review, timing/resource instrumentation, reconnect
recovery, and the accepted full-screen boot presentation. A qualifying 25-cycle
run completed 25/25 four-camera sets; artifact-level fault/recovery and reboot
identity tests also passed. Median complete-set review latency was 3.250 seconds,
so the soft two-second target remains an optimization item. The completed
Milestone 2 removable-media procedures and exit evidence are in
[`docs/MILESTONE_2_PLAN.md`](docs/MILESTONE_2_PLAN.md).

Milestone 2 removable-media qualification is complete. The real-Pi matrix
exercised normal, reboot, idle-reinsert, automatic-remount, missing, full,
read-only, corrupt/unmountable, active-write removal, and two-drive selection.
App 0.2.1 keeps Tk polling alive when reviewed media disappears, presents
bounded storage errors on the 800x480 display, and cleans expired capture
staging safely. The fully backed-up product FAT was repaired and remained clean
after final byte-valid four-camera capture `20260718T175104Z_04b69c0b`.
The product owner accepted an external battery pack with separate rated
5 V / 2 A feeds for the Raspberry Pi and powered USB hub plus its own percentage
display. Aggregate measurement and internal battery/safe-power integration are
retired as V1 gates.

The physical Pi now runs the native Qt Quick/PySide6 touchscreen at 800x480 on
Wayland. Seven mockup-derived routes cover ready, progress, partial review, a
logo-based static preview placeholder, four-camera controls, a removable-USB
library, and a detached GIF viewer. The library and viewer can permanently
delete a confirmed capture set, including its JPEG originals, GIF, and manifest.
The application includes no live-preview
backend and no battery UI. The library supports touch flicking plus visible
right-side page navigation with a current/total page indicator. The `fb1d1e7` runtime passed native-Wayland,
capture, and real-library validation; seven route renders produced across
`d502fff` and `828831b` are preserved with their exact commit attribution and
zero QML warnings. The final runtime completed capture
`20260719T021211Z_4be2d832`, and loaded the real 214-entry library in 0.527
seconds. Follow-up UI code at `ce5871f` corrected the ready and USB-label
overflows and passed native Pi rendering plus functional pagination checks. See the
[`Qt deployment evidence`](docs/evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md).
The first Qt soft reboot did not return to the LAN and required a physical
power cycle; its cause is unknown because no persistent journal was available.
Compact enclosure work remains the active milestone.

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
- [`docs/MILESTONE_1_PLAN.md`](docs/MILESTONE_1_PLAN.md) — completed bench milestone plan and measured exit evidence
- [`docs/MILESTONE_2_PLAN.md`](docs/MILESTONE_2_PLAN.md) — completed removable-media fault-qualification procedures and exit evidence
- [`docs/MILESTONE_3_PLAN.md`](docs/MILESTONE_3_PLAN.md) — closed/retired aggregate-power and safe battery-integration plan
- [`docs/MILESTONE_4_PLAN.md`](docs/MILESTONE_4_PLAN.md) — active compact-enclosure layout, print, and acceptance plan
- [`docs/CURRENT_SESSION.md`](docs/CURRENT_SESSION.md) — concise handoff for the active work
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
