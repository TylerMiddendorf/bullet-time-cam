# Qt Touchscreen Deployment Evidence - 2026-07-18

Status: implementation, deployment, power-cycle recovery, and SSH-accessible Pi
validation complete. Human touch-feel observation remains enclosure-stage
feedback and is not claimed as SSH evidence.

## Rollback and Git chain

- Pre-UI rollback baseline: `63420c1` (`Accept external V1 power arrangement`).
- No files were staged when the migration began. The pre-UI baseline was
  documented before implementation, and the unrelated unstaged Milestone 4 edit
  was preserved throughout.
- Initial Pi commit: `1e6a6e70b2e4d2ce934463ad3c038eeddbd01391` on a clean
  `main` checkout.
- Every Pi update used a pushed `origin/main` commit and
  `git pull --ff-only origin main`; files were not copied around Git.
- First deployed route-harness commit: `de2efe8`.
- QML bridge lifetime fix: `5d606dd`.
- Final validated runtime commit: `fb1d1e7`.
- Installer backup: `/var/lib/bullet-time-boot-backups/20260719T014137Z`.
- Tk/X11, pre-UI commit `63420c1`, and the installer backup remain available as
  a documented recovery path; an end-to-end rollback drill was not executed.
  The active service is Qt on native Wayland.

## Scope implemented

- Native 800x480 Qt Quick/QML interface with seven routes: ready, progress,
  partial review, static preview placeholder, four-camera control center,
  removable-media library, and detached GIF viewer.
- The preview uses `assets/ui/preview-placeholder.png`, visibly says
  `DEMO PLACEHOLDER` and `PREVIEW NOT CONNECTED`, and has no camera transport.
- No battery UI/state/reserved region, hotspot claim, Qt Multimedia dependency,
  live stream, deletion command, or settings command was added.
- Library scanning is read-only and asynchronous. It validates published
  schema-2 capture sets below the selected removable drive's `BulletTime/`
  root. Only the first six visible thumbnails are decoded eagerly; selecting a
  capture decodes and detaches its actual GIF before viewer display.
- Unsupported camera settings are visibly disabled and have no bridge command.
- The service forces `QT_QPA_PLATFORM=wayland` and has no `DISPLAY` fallback.

## Deterministic validation

- Local and Pi `python -m unittest discover -s pi_app/tests -v`: 112 tests
  passed with one expected hardware-evidence skip.
- `python -m pi_app.tools.validate_qt_ux_contract --json`: PASS, contract v2,
  seven routes, zero errors.
- The complete production `Main.qml` tree loaded and tore down without QML
  warnings after the Pi pulled `5d606dd`.
- Commit and pre-push hooks passed for the UI changes. The product owner's
  unrelated, unstaged `docs/MILESTONE_4_PLAN.md` change was excluded from all
  commits and remains preserved.

## Runtime installation and recovery

- Debian Trixie arm64 installed Qt 6.8.2 and PySide6 6.8.2.1 from Debian
  packages: `python3-pyside6.qtquick`, `qml6-module-qtquick-controls`,
  `qml6-module-qtquick-layouts`, `qml6-module-qtqml-workerscript`, and
  `qt6-wayland`.
- No Qt Multimedia or Qt Quick Effects package was requested.
- The first issued `sudo reboot` did not return to the LAN within the bounded
  observation period. The product owner physically power-cycled the Pi, after
  which it returned normally. Persistent journal data was unavailable, so the
  failed soft reboot is recorded without assigning a cause.
- After recovery, the boot verifier passed every gate. The running graphical
  session contained `labwc` and the Qt application without Xwayland. The UI
  service was active with zero restarts and no current warnings or errors.

## Route render evidence

All route captures were rendered by Qt on the Pi's native Wayland display.
Every PNG is exactly 800x480, observed `frameSwapped`, and emitted zero QML
warnings. They were produced across `d502fff` and `828831b`, as attributed in
the table and manifest; they are not represented as renders from the later
`fb1d1e7` library-optimization commit. That final runtime was separately tested
against the real product library. The image files and machine-readable manifest are in
[`2026-07-18-pi-routes/`](2026-07-18-pi-routes/).
The harness's named published GIF was capture
`20260718T222606Z_30cf8e02`, SHA-256
`e69ae83481b639c4260b170da9f026a2b672ce14ec1f2771f4e96e4c35b18f9f`;
the manifest labels which route states use fixture data.

| Route | Render commit | Artifact | SHA-256 |
| --- | --- | --- | --- |
| Ready | `d502fff` | `01-ready-800x480.png` | `47725a420ad512700d81eca3c3c1cf209cd2f517531d7f8f4a030f825b634dde` |
| Progress | `d502fff` | `02-progress-800x480.png` | `21a904b69423df38c7e28e5727e70bb2b52bc0a651d8376e22ff01b2d7d7da6c` |
| Partial review | `d502fff` | `03-partial-review-800x480.png` | `6413432cc4bcb978a73d7bf11cc965708728d3adc10b16f86d498dfcd0ea6ab9` |
| Static placeholder | `828831b` | `04-static-preview-placeholder-800x480.png` | `8536de5e175b752039444ee7e4cf67f1815a6f9f49005e50cf30f3e556288e77` |
| Control center | `d502fff` | `05-four-camera-control-center-800x480.png` | `0d5d6d6dd6274df975686b5fd414be80a4f0a0cb3e3765f3f26f72471e5aa528` |
| USB library | `828831b` | `06-removable-media-library-800x480.png` | `b994a0c55e6c1fd40dbeb2a336fc375171588ac3b93dff979444ef3100f719ba` |
| GIF viewer | `828831b` | `07-gif-viewer-800x480.png` | `58bbd8e5fd213ef09e2d1a99b34e57d1e7c4d62644ad9412062a128e6751d64a` |

Visual review found and corrected a hidden preview disclaimer, overlapping
control settings, library identifier overflow, and review/viewer footer
collisions before the final artifacts above were accepted.

## Real capture and media validation

- A bounded `--trigger-once` run stopped the normal service, performed one
  automatic Qt UI capture, exited one second after completion, and then restored
  the service.
- New capture `20260719T021211Z_4be2d832` published a complete schema-2 manifest,
  four complete camera records, four originals, and an ordered GIF with SHA-256
  `62870c11068dbbcf9ec6dbf7eed9627e6a88073b31a18e1151693b668608b872`.
- GPIO17 was LOW before and after the bounded run. The service returned active
  with zero restarts.
- The one-shot process-start-to-display callback was 10,836.753 ms. This
  includes process startup and is retained as a diagnostic rather than
  represented as steady-state touch latency.
- The real drive contained 214 valid published entries and three skipped
  invalid entries. Eagerly decoding every thumbnail took 21,101.496 ms. The
  manifest-validation-only baseline was 72.722 ms. After bounding eager decode
  to the six initially visible thumbnails, full initial load took 526.919 ms,
  approximately 40 times faster than the first implementation.
- A real selected GIF decoded as six 640x480 frames at 150 ms each in 256.102
  ms, detached from the removable path before display.

## Final hardware state

- Four stable camera identities were present:
  `E072A1F99CF8`, `E072A1F99CC0`, `E072A1F9A190`, and `E072A1F9B3E4`.
- Only the UI process owned all four serial devices.
- GPIO17 was configured output LOW.
- Product media was a writable VFAT mount at `/media/username/USB DISK`, with
  approximately 230 GiB free.
- The Pi reported approximately 1.5 GiB available RAM, 37 C, and
  `get_throttled=0x0`.
- No new kernel USB `error -71` event was observed after recovery.

Automated controller interactions, route transitions, and native rendering
passed. Because validation was conducted over SSH, this record does not claim a
person physically tapped every target or judged the installed panel's tactile
feel; that observation should be collected during enclosure fitting.

## Final tracked closure check

Evidence/documentation commit `5ba709b74390839ad471f7ee605a3358d2c330fe`
was pushed to `origin/main` and fast-forward pulled by the Pi. At that exact
checkout, 113 deterministic tests ran: 112 passed and the one environment-gated
live-evidence test skipped. The contract validator passed seven routes with zero
errors, every boot-experience verifier check passed, and the service was active
at PID 2116 with `NRestarts=0`. GPIO17 was output LOW, all four stable serial
devices were present, product VFAT media was writable with 230 GiB free, no
Xwayland or current service warning was present, temperature was 38.9 C, and
`get_throttled=0x0`.
