# Qt Quick Touchscreen UI Implementation

Status: implemented, deployed, and validated on the Raspberry Pi

This record covers the Tk-to-Qt Quick/PySide6 touchscreen migration. It does
not change Milestone 4 enclosure scope. Live preview transport and operative
camera settings remain deferred.

## Implemented boundary

- Existing receiver, coordinator, GPIO17 trigger, media pipeline, removable-USB
  fail-closed behavior, and headless operation remain intact.
- Seven tracked compositions are native 800x480 QML pages: ready, capture
  progress, partial review, static preview placeholder, four-camera control
  center, removable-media library, and viewer. Runtime QML never displays the
  mockup PNGs.
- Preview surfaces use `assets/ui/preview-placeholder.png` and visibly say
  `DEMO PLACEHOLDER` and `PREVIEW NOT CONNECTED`; there is no preview transport,
  Qt Multimedia import, or `LIVE` claim.
- The UI contains no battery presentation, battery state, hotspot/network
  status, or reserved layout region for them. Future camera settings are
  visibly disabled and have no bridge command.
- Navigation/catalog state is separate from the immutable capture-workflow
  snapshot. The only product command emitted by the UI is the existing
  `CAPTURE` command, from allowed capture routes and states.

## Media safety and library

Current review GIFs are decoded and converted to in-memory PNG data URLs before
QML sees them. QML never binds to the removable USB path, so removal after
review does not invalidate displayed frames or stop polling.

The library is read-only. Worker threads validate every actual schema-2
published capture directory under the selected removable USB `BulletTime/`
root. Initial display eagerly decodes only the first six visible thumbnails;
later cards use a lightweight placeholder until selected. Selection decodes the
actual animation before switching to Viewer. Staging, corrupt, incomplete, and
unreadable entries are skipped. Empty and removed-media states are nonfatal.
The library never deletes or rewrites media, and selection/back state survives
refreshes where the selected capture still exists.

## Lifecycle and Debian runtime

- Debian requirements are `python3-pyside6.qtquick`,
  `qml6-module-qtquick-controls`, `qml6-module-qtquick-layouts`,
  `qml6-module-qtqml-workerscript`, and `qt6-wayland`. Effects and Multimedia
  are not installed because no QML file imports them.
- The service forces `QT_QPA_PLATFORM=wayland` and does not set `DISPLAY`.
  PySide6 imports remain lazy so headless receiver operation does not need Qt or
  a display server.
- QML load failure raises and exits nonzero. The receiver starts only after the
  first logo `frameSwapped`; review timing is recorded from a subsequent
  `frameSwapped`; shutdown stops and joins a started receiver.
- Tk/X11 packages remain installed only as a rollback path. The installer
  backup for this deployment is
  `/var/lib/bullet-time-boot-backups/20260719T014137Z`.

## Verification

The implementation evolved through small tracked commits and was deployed by
push to `origin/main` followed by fast-forward-only pulls on the Pi. The final
validated runtime commit is `fb1d1e7`.

- Local and Pi deterministic suite: 112 tests passed, with one expected
  live-hardware-evidence skip.
- UX contract validator: PASS, contract v2, seven routes, zero errors.
- Production QML tree: loads and tears down without warnings.
- Native Pi Wayland route harness: seven 800x480 screenshots, each with
  `frameSwapped` observed and zero QML warnings.
- Boot/session verifier: every check passed; no Xwayland or X11 fallback was
  active.
- Bounded real-UI capture: complete four-camera set
  `20260719T021211Z_4be2d832`, four originals and ordered GIF, followed by an
  active service and GPIO17 LOW.
- Real product library: 214 valid entries, three skipped invalid entries, six
  eagerly decoded thumbnails, 0.527-second initial catalog/load time. The
  earlier all-thumbnail implementation took 21.101 seconds on the same media.

The one-shot process-start-to-display callback diagnostic measured 10.837
seconds. That includes bounded one-shot application startup and is not claimed
as steady-state touch latency; the existing four-camera 3.250-second median
review-path limitation also remains documented. Physical human touch feel was
not observed over SSH. Automated controller interactions and native display
rendering passed, but a person using the installed panel should still provide
enclosure-stage touch feedback.

Full hardware evidence and route hashes are recorded in
[`evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md`](evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md).
