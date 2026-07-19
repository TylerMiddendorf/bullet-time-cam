# Qt Quick Touchscreen UI Implementation

Status: local implementation complete; Raspberry Pi deployment validation pending

This record covers the Tk-to-Qt Quick/PySide6 touchscreen migration. It does
not change Milestone 4 enclosure scope or claim Raspberry Pi deployment.

## Implemented Boundary

- Existing receiver, coordinator, GPIO17 trigger, media pipeline, removable-USB
  fail-closed behavior, and headless operation remain intact.
- Seven tracked compositions are native 800x480 QML pages: ready, capture
  progress, review/error, preview placeholder, control center, removable-media
  library, and viewer. Runtime QML never displays the mockup PNGs.
- Preview surfaces use the finalized `assets/ui/preview-placeholder.png` and
  visibly say `PREVIEW PLACEHOLDER` and `DEMO`; there is no preview transport,
  Qt Multimedia import, or `LIVE` claim.
- The UI contains no battery presentation, hotspot/network status, or layout
  space for either. Future camera settings are visibly disabled and have no
  bridge command.
- Navigation/catalog state is separate from the immutable capture-workflow
  snapshot. The only product command emitted by the UI is the existing
  `CAPTURE` command, from allowed capture routes and states.

## Media Safety and Library

Current review GIFs are decoded and converted to in-memory PNG data URLs before
QML sees them. QML never binds to the removable USB path, so removal after
review does not invalidate displayed frames or stop polling.

The library is read-only. Worker threads catalog actual schema-2 published
capture directories under the selected removable USB `BulletTime/` root and
decode a selected animation before switching to Viewer. Staging, corrupt,
incomplete, and unreadable entries are skipped. Empty and removed-media states
are nonfatal. The library never deletes or rewrites media, and selection/back
state survives refreshes where the selected capture still exists.

## Lifecycle and Debian Runtime

- Debian requirements include `python3-pyside6.qtquick`,
  `qml6-module-qtquick-controls`, `qml6-module-qtquick-layouts`,
  `qml6-module-qtqml-workerscript`, and `qt6-wayland`. Effects is not installed
  because no QML file imports it.
- The service forces `QT_QPA_PLATFORM=wayland`. PySide6 imports remain lazy so
  headless receiver operation does not need Qt or a display server.
- QML load failure raises and exits nonzero. The receiver starts only after the
  first logo `frameSwapped`; review timing is recorded from a subsequent
  `frameSwapped`; shutdown stops and joins a started receiver.
- Tk/X11 packages remain installed only for rollback. This task does not deploy
  to or restart the Raspberry Pi.

## Local Verification

Implementation commit `d413604` contains the native runtime, state fixes,
read-only catalog, seven QML routes, and deterministic tests.

- `python -m unittest discover -s pi_app/tests -v`: 97 discovered, 96 passed,
  one expected live-hardware skip.
- Repository Ruff check and format hooks: passed.
- Local Qt 5.15 `qmllint` compatibility parse of every runtime QML file:
  passed. This is syntax evidence, not Raspberry Pi Qt 6 rendering evidence.

## Deployment Gate

| Gate | Status |
| --- | --- |
| Coherent local implementation commit | Complete at `d413604` |
| Branch pushed to the remote | Not performed in this task |
| Exact pushed commit pulled by the Pi | Not performed |
| Installer/verifier run on the Pi | Not performed |
| Cold-boot visual, touch, catalog, and capture validation | Not performed |

Hardware validation must occur in order: commit, push the branch, pull that
exact hash on the Pi, run the installer, reboot, run the verifier, then record
visual/touch/catalog/capture evidence. A copied file or local checkout is not
deployment evidence.
