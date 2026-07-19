# Qt Touchscreen Migration Validation Track

Status: completed implementation/validation track, deployed on the physical Pi;
not a canonical milestone or product-decision document. Canonical status lives
in `docs/PROJECT_CONTEXT.md` and `docs/ROADMAP.md`.

This directory defines a testable V1 UX contract and a repeatable validation
path for migrating the Raspberry Pi touchscreen from Tkinter to Qt Quick with
PySide6. The implementation shipped and passed the bounded physical-rig checks
recorded in `docs/evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md`.

## Scope

- 800x480 full-screen touchscreen presentation
- Seven deterministic test routes covering Ready, progress, partial review,
  Capture, Settings, Library, and real-GIF viewer compositions
- Product-logo handoff, complete review, actionable error states, and safe
  receiver/shutdown behavior
- Headless Qt tests and screenshot evidence
- Raspberry Pi deployment, health checks, and recovery to the known Tkinter
  baseline

Explicitly excluded:

- Live camera streaming or a live-preview pipeline
- Battery level, charge, power-source, or battery-status UI
- Live setting changes or any setting command sent to a camera node
- Media renaming, sharing, editing, or boot-card browsing
- Network controls, hotspot claims, and 12-camera behavior
- Changes to `docs/MILESTONE_4_PLAN.md`

## Source Priority

When sources disagree, use this order:

1. Confirmed decisions in `docs/PROJECT_CONTEXT.md` and
   `docs/INTERVIEW.md`
2. Milestone ordering and scope in `docs/ROADMAP.md`
3. Existing receiver events and storage safety behavior
4. Visual concepts `designs/ux-mockups/01-v1-ready.png` through
   `07-gif-viewer.png`, subject to the scope adaptations below
5. Engineering choices in this directory

All seven PNGs are 1619x971 reference renders, not pixel-perfect raster
backgrounds. Every route lays out native 800x480 Qt objects. The source images
do not authorize battery UI or reserved battery space, a live preview backend,
hotspot claims, 12-camera behavior, multimedia dependencies, mutable media
operations other than confirmed whole-capture-set deletion, or node setting commands.

The later compositions are deliberately adapted into bounded validation
routes:

- Design 4 is the Capture route. It uses only the generated static camera
  fixture and must say `STATIC PLACEHOLDER` and
  `CAMERA VIEW NOT CONNECTED` until live preview exists. It is the only
  touchscreen route allowed to emit `CAPTURE`.
- Design 5 reports the current four cameras. Unsupported settings are visible
  only as disabled/unavailable controls and have no node-command binding.
- Design 6 reads only committed captures on removable USB media. It can delete
  one confirmed, revalidated capture set; it cannot rename, share, edit, or fall
  back to the boot card.
- Design 7 decodes a selected real GIF into detached PNG data-URL frames and
  presents them with Qt Quick `Image`; it does not import Qt Multimedia.

`assets/ui/preview-placeholder.png` is the only approved camera-view fixture
for this track. Whenever it is visible, the UI must overlay the exact text
`STATIC PLACEHOLDER`; it must never call the image live or imply camera transport.

## Documents

- `UX_SPEC.md` - normative screen, interaction, transition, and acceptance
  contract
- `HEADLESS_QT_TEST_STRATEGY.md` - deterministic Qt/QML test layers and CI/Pi
  commands
- `PI_DEPLOYMENT_ROLLBACK.md` - staged installation, health gates, activation,
  rollback, and boot recovery
- `evidence/UX_EVIDENCE_TEMPLATE.md` - dated validation record template
- `evidence/ROUTE_EVIDENCE_TEMPLATE.json` - machine-readable seven-route
  screenshot/evidence skeleton

The machine-readable companion contract lives at
`pi_app/qt_validation/ux_contract.json`. It remains separate from the production
QML so scope and interaction constraints can be validated without starting the
display runtime.

Validate that companion contract without Qt or third-party Python packages:

```bash
python3 -m pi_app.tools.validate_qt_ux_contract --json
python3 -m unittest pi_app.tests.test_qt_ux_contract -v
```
