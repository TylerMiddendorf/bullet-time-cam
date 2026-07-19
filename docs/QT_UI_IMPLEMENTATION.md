# Qt Quick Touchscreen UI Implementation

Status: implementation in progress from baseline `1ef1ba6`

This document is the dedicated engineering record for replacing the Raspberry
Pi application's Tk presentation layer with Qt Quick/QML and PySide6. It records
the implementation boundary and local verification without changing Milestone
4 enclosure scope or claiming Raspberry Pi deployment evidence.

## Scope

- Preserve the existing receiver, capture coordinator, GPIO17 trigger, media
  pipeline, and removable-USB fail-closed behavior.
- Replace the Tk touchscreen loop with a PySide6 bridge and an 800x480 Qt Quick
  interface based on the supplied UX mockups.
- Treat the tracked 1619x971 PNG mockups as composition references only. Build
  every runtime screen natively at 800x480; do not scale or display the mockup
  rasters in the application.
- Implement ready, capture-progress, review/error, camera, control-center,
  media-library, and viewer compositions with touchscreen navigation.
- Use `assets/ui/preview-placeholder.png` on preview surfaces and label it
  `DEMO · PLACEHOLDER`. Never label the placeholder `LIVE`; no live camera
  stream is opened or requested by this UI.
- Do not display battery level, charge, or battery status. The selected external
  pack remains the independent V1 charge indication. No layout space is
  reserved for a battery control or indicator.
- Keep headless receiver operation independent of PySide6 and a display server.
- Do not deploy to the Raspberry Pi during this implementation task.

## Compatibility Contract

Receiver events remain queue-based. The UI reducer accepts the established
`READY`, `LOADING`, `REVIEW`, `REVIEW_WITH_ERROR`, and `ERROR` states and now
also consumes optional structured fields for connected cameras, per-camera
progress, capture phase, completed cameras, and failed cameras. Existing event
consumers can ignore those additive fields.

Review media must be detached from removable storage before presentation so an
idle USB removal does not terminate event polling. Touch capture remains
restricted to ready, review, partial-review, and error states, and the receiver
still resolves writable USB storage before pulsing GPIO17.

## Progress

### State-model foundation

- Added a platform-neutral immutable UI snapshot and reducer in
  `pi_app/bullettime/ui_model.py`.
- Preserved the legacy `PresentationState` import surface while moving its logic
  out of the presentation toolkit module.
- Added structured receiver progress fields without changing capture,
  persistence, or trigger coordination.
- Added deterministic reducer coverage for four-camera readiness, transfer
  progress, partial-view counts, failed-camera indicators, storage faults, and
  removed review media.

## Verification Record

Hardware and Raspberry Pi deployment are intentionally not part of this record.
Commands and results will be appended as coherent implementation increments are
completed.
