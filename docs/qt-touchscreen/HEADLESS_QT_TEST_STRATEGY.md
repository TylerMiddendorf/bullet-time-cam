# Headless Qt Test Strategy

Status: deterministic validation strategy for the independent Qt touchscreen
track. Passing these layers does not claim physical-touchscreen or Pi acceptance.

## Fixed inputs

- Logical render size: native 800x480 landscape
- Visual references: all seven 1619x971 PNGs under `designs/ux-mockups/`
- Contract: `pi_app/qt_validation/ux_contract.json`
- Route order: ready, progress, partial review, static preview placeholder,
  four-camera control center, removable-media library, GIF viewer
- Headless seed/timezone/locale: fixed test seed, UTC, `C.UTF-8`
- Headless renderer: `QT_QPA_PLATFORM=offscreen`, software RHI, basic render
  loop, Basic Controls style
- Product renderer: `QT_QPA_PLATFORM=wayland`; offscreen results never satisfy
  the product Wayland gate

Set the Qt variables before importing PySide6. Tests may call
`pi_app.qt_validation.headless.qt_environment()` to avoid import-order drift.

## Layer 0 - dependency-free contract checks

This layer runs on any supported Python and imports neither Qt nor Pillow:

```bash
python3 -m pi_app.tools.validate_qt_ux_contract --json
python3 -m unittest pi_app.tests.test_qt_ux_contract -v
```

It validates the seven route IDs and paths, native viewport, all source PNG IHDR
dimensions, named bounds, the five-package Trixie minimum, safety flags,
forbidden rendered terms, disabled control-center settings, empty node command
surface, read-only removable-media library, detached-frame real-GIF viewer,
and the ordered UX-001..UX-022 scenario list.

## Layer 1 - bounded QML load and first frame

Use the generic smoke utility against the implementation's root QML:

```bash
python3 -m pi_app.tools.smoke_qt_qml \
  --qml pi_app/bullettime/qml/Main.qml \
  --platform offscreen \
  --timeout-ms 5000 \
  --required-object startupLogo \
  --screenshot build/qt-evidence/first-frame.png
```

The smoke fails if PySide6 cannot import, the QML file is absent, the timeout is
outside 100-60000 ms, the load emits a Qt warning/critical/fatal message,
`rootObjects()` is empty, `startupLogo` is absent, the root lacks
`frameSwapped`, no frame arrives before the timeout, geometry differs from
800x480, or the screenshot cannot be saved. A passing `frameSwapped` metric
proves that Qt presented a frame; the screenshot and visual evidence separately
prove that the frame is the opaque product logo.

Run the same bounded smoke on the Pi with `--platform wayland` from the service
environment. Do not substitute `minimal`, X11, or Xwayland for that gate.

## Layer 2 - model and command tests

Drive the view model with a fake receiver, fake capture command sink, fake
storage catalog, monotonic fake clock, and deterministic real GIF fixture.
Assertions cover:

1. State/event transitions and non-regressing capture phases.
2. Ten rapid/multi-touch inputs producing one capture command.
3. No command from progress or static-preview routes.
4. No node command from any disabled control-center setting.
5. Library enumeration limited to committed removable-USB capture directories,
   with no mutation or boot-card fallback.
6. Real GIF decode to detached PNG data-URL frames, frame advancement, and
   duration preservation without Qt Multimedia. QTimer scheduling itself is a
   runtime observation, not a deterministic unit-test claim.
7. Review bytes/frames detached before the source drive is removed.
8. Receiver stop request, bounded worker join, serial close, and GPIO17 LOW
   cleanup on normal exit and exception exit.

No test may call a real serial port, GPIO backend, mount service, or node
command at this layer.

## Layer 3 - seven-route render matrix

Render routes in canonical order after fonts and fixtures are ready.

The tracked `RouteHarness.qml` supplies deterministic, command-free state for
each native route. On the Pi, render one route per bounded process, optionally
pointing review/viewer at a real published GIF:

```bash
python3 -m pi_app.tools.smoke_qt_qml \
  --qml pi_app/bullettime/qml/RouteHarness.qml \
  --platform wayland --route ready \
  --screenshot build/qt-evidence/01-ready-800x480.png
```

Use these filenames exactly:

```text
01-ready-800x480.png
02-progress-800x480.png
03-partial-review-800x480.png
04-static-preview-placeholder-800x480.png
05-four-camera-control-center-800x480.png
06-removable-media-library-800x480.png
07-gif-viewer-800x480.png
```

`collect_screenshot_evidence()` checks presence, native dimensions, and SHA-256.
The bounded route smoke records root-object presence, `frameSwapped`, geometry,
and QML warnings. Contract/unit tests separately enforce route and command
scope. Visual review checks visible text, target sizing, clipping, missing
assets, and overflow; the current harness does not programmatically walk every
semantic identifier or compare pixels to the source mockups.

The preview screenshot must show both `DEMO PLACEHOLDER` and
`PREVIEW NOT CONNECTED`. The viewer screenshot uses a named real GIF fixture,
not the design raster.

## Layer 4 - timing and fault tests

- Schedule GUI-heartbeat observations at 16.67 ms and fail when receiver,
  filesystem, decode, or persistence work causes two consecutive missed frames
  (33 ms).
- Keep progress active beyond two seconds with a fake advancing transaction;
  do not sleep for two real seconds or invent a percent.
- Remove the fake review/library source after decode and prove animation,
  polling, and navigation continue from detached data.
- Inject missing, full, read-only, unmountable, and I/O/removal storage results;
  assert compact, unclipped USB-specific messages.
- Inject the previously observed Terminus-hub `error -71` disconnect and later
  recovery as events. The UI must show loss/recovery truthfully, retain stable
  logical identities, avoid duplicate serial owners, and never claim the
  transient fault is permanently fixed without a new hardware run.

## Pi-only acceptance boundary

Headless tests cannot prove emitted photons, touch mapping, serial ownership,
GPIO electrical state, real USB unbind/recovery, compositor handoff, or reboot.
The Pi checklist lists those separate gates. Record which were actually run in
`evidence/UX_EVIDENCE_TEMPLATE.md`; do not promote fixture/desktop results or
the existence of a rollback procedure into Pi passes.
