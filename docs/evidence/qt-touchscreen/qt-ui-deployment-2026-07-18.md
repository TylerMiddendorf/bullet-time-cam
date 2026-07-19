# Qt Touchscreen Deployment Evidence — 2026-07-18

Status: implementation and pre-reboot Pi validation passed; post-reboot
validation blocked because the Pi did not return to the network.

## Rollback and Git chain

- Pre-UI rollback baseline: `63420c1` (`Accept external V1 power arrangement`).
- Initial Pi commit: `1e6a6e70b2e4d2ce934463ad3c038eeddbd01391`.
- The Pi checkout was clean on `main` before deployment.
- The implementation was pushed to `origin/main`; the Pi used `git fetch` and
  `git pull --ff-only origin main`.
- First deployed UI commit: `de2efe863d52771a9bf392df4325291b95102ae8`.
- A QML bridge-lifetime warning found on the Pi was fixed, pushed, and pulled
  with another fast-forward-only update.
- Final deployed commit before reboot:
  `5d606ddd524f77493da8965b1c0b35011f148fb0`.
- Installer backup:
  `/var/lib/bullet-time-boot-backups/20260719T014137Z`.

## Scope implemented

- Native 800x480 Qt Quick/QML interface with seven routes: ready, progress,
  partial review, static preview placeholder, four-camera control center,
  removable-media library, and detached GIF viewer.
- The preview uses `assets/ui/preview-placeholder.png`, visibly says
  `DEMO PLACEHOLDER` and `PREVIEW NOT CONNECTED`, and has no camera transport.
- No battery UI/state/reserved region, hotspot claim, Qt Multimedia dependency,
  live stream, deletion command, or settings command was added.
- Library scanning is read-only, asynchronous, and limited to published capture
  sets below the selected removable drive's `BulletTime/` root. Selected GIFs
  are decoded away from the GUI thread and detached before viewer display.
- Unsupported camera settings are visibly disabled and have no bridge command.
- Tk/X11 packages remain installed only as a rollback path. The deployed Qt
  service forces `QT_QPA_PLATFORM=wayland` and has no `DISPLAY` fallback.

## Local validation

- `python -m unittest discover -s pi_app/tests -v`: 112 tests passed with one
  expected hardware-evidence skip.
- `python -m pi_app.tools.validate_qt_ux_contract --json`: PASS, contract v2,
  seven routes, zero errors.
- Pre-push hook: end-of-file, trailing-whitespace, and Python unit-test checks
  passed.
- Repository-wide hooks passed except `mixed-line-ending` repeatedly rewrote
  the product owner's unrelated, unstaged `docs/MILESTONE_4_PLAN.md`; that file
  was intentionally excluded from every UI commit and its substantive edits
  remain present.

## Pi validation before reboot

- Debian Trixie arm64 installed Qt 6.8.2 and PySide6 6.8.2.1 from Debian
  packages. The five requested direct runtime packages were installed:
  `python3-pyside6.qtquick`, `qml6-module-qtquick-controls`,
  `qml6-module-qtquick-layouts`, `qml6-module-qtqml-workerscript`, and
  `qt6-wayland`. No Qt Multimedia or Qt Quick Effects package was requested.
- Pi deterministic suite: 112 tests passed with the single expected
  hardware-evidence skip.
- Pi UX contract: PASS, seven routes, zero errors.
- The complete production `Main.qml` route tree loaded with the offscreen Qt
  platform. Teardown initially reported that the context bridge became null;
  commit `5d606dd` parented the bridge to the QML engine. The Pi pulled that
  commit and the same load check then exited zero without those warnings.

## Reboot failure and remaining gates

- `sudo reboot` was issued after the Pi had pulled `5d606dd`.
- From approximately 21:45 through 21:49 EDT, repeated bounded SSH attempts to
  the verified `10.0.0.136` address timed out. LAN ping reported the destination
  unreachable from the development host. `camerapi.local` did not resolve.
- This resembles the project's known Pi boot/userspace recovery hazard, but no
  cause can be assigned without the Pi returning or local console evidence.
- A physical power cycle is now required. After recovery, do not change Git
  state: first record the boot journal and service failure, if any.
- Still pending: boot verifier, native-Wayland/no-Xwayland confirmation,
  seven-route 800x480 Pi screenshots, real removable-media library/viewer check,
  touch interaction, normal four-camera capture, GPIO17 LOW confirmation,
  camera UID/serial-ownership checks, and post-reboot USB `error -71` review.

