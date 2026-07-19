# Touchscreen UX Mockups

These images are provisional visual references for the rig's 800x480-aspect
touchscreen. They communicate possible layout and visual direction; they are
not executable UI, hardware evidence, or confirmed product requirements.
All seven PNG source renders are exactly 1619x971 and must be re-laid out as
native 800x480 UI objects rather than used as scaled raster backgrounds.

## Version 1 Concepts

- [`01-v1-ready.png`](01-v1-ready.png) — four-camera and USB readiness with the
  physical/touch capture affordance
- [`02-v1-capture-progress.png`](02-v1-capture-progress.png) — per-camera
  capture/transfer progress and animation-building state
- [`03-v1-review-partial.png`](03-v1-review-partial.png) — saved three-view result
  with a camera-specific failure message

Version 1 remains limited to essential status, loading, latest-result review,
and camera-specific errors. The images are not proof that the implemented UI
matches these compositions.

## Fast-Follow Concept

- [`04-fast-follow-live-preview.png`](04-fast-follow-live-preview.png) — a
  possible live-preview and capture screen after V1 integration

## Later Product Concepts

- [`05-ideal-future-control-center.png`](05-ideal-future-control-center.png) — a
  12-camera control/settings and processing concept
- [`06-library-navigation.png`](06-library-navigation.png) — a future media
  library concept
- [`07-gif-viewer.png`](07-gif-viewer.png) — a future animation viewer concept

The later concepts include features explicitly outside V1, including live
preview, synchronized settings, a gallery, enhanced processing, 12-camera
operation, and hotspot status. Canonical scope and sequencing remain in
[`docs/PROJECT_CONTEXT.md`](../../docs/PROJECT_CONTEXT.md) and
[`docs/ROADMAP.md`](../../docs/ROADMAP.md).

The independent [`Qt validation track`](../../docs/qt-touchscreen/README.md)
defines bounded test-route adaptations for all seven compositions. In that
track Design 4 is a labeled static placeholder, Design 5 is four-camera-only
with settings disabled and no node commands, Design 6 is a read-only
removable-USB catalog, and Design 7 uses a real GIF without Qt Multimedia.
Those test routes do not promote the later concepts into shipped V1 scope.
