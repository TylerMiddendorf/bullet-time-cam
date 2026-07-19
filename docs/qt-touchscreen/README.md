# Qt Touchscreen Migration Validation Track

Status: independent implementation/validation track started from rollback
baseline `1ef1ba6` and contract commit `1f6ff70`; not a canonical milestone or
product-decision document.

This directory defines a testable V1 UX contract and a repeatable validation
path for migrating the Raspberry Pi touchscreen from Tkinter to Qt Quick with
PySide6. It does not claim that the Qt implementation has shipped or passed on
the physical rig.

## Scope

- 800x480 full-screen touchscreen presentation
- Seven deterministic test routes covering ready, progress, partial review,
  static preview placeholder, current four-camera control center, read-only
  removable-media library, and real-GIF viewer compositions
- Product-logo handoff, complete review, actionable error states, and safe
  receiver/shutdown behavior
- Headless Qt tests and screenshot evidence
- Raspberry Pi deployment, health checks, and recovery to the known Tkinter
  baseline

Explicitly excluded:

- Live camera streaming or a live-preview pipeline
- Battery level, charge, power-source, or battery-status UI
- Live setting changes or any setting command sent to a camera node
- Media deletion, renaming, sharing, or boot-card browsing
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
operations, or node setting commands.

The later compositions are deliberately adapted into bounded validation
routes:

- Design 4 uses only the generated static preview fixture and must say
  `DEMO PLACEHOLDER` and `PREVIEW NOT CONNECTED`.
- Design 5 reports the current four cameras. Unsupported settings are visible
  only as disabled/unavailable controls and have no node-command binding.
- Design 6 reads only committed captures on removable USB media. It cannot
  delete, rename, share, or fall back to the boot card.
- Design 7 opens a real GIF with Qt Quick `AnimatedImage`; it does not import
  Qt Multimedia.

`assets/ui/preview-placeholder.png` is the only approved preview-like fixture
for this track. Whenever it is visible, the UI must overlay the exact text
`DEMO PLACEHOLDER`; it must never call the image live or imply camera transport.

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
`pi_app/qt_validation/ux_contract.json`. It is intentionally separate from the
current production UI so this track can be reviewed and tested without changing
the known-good Tkinter path.

Validate that companion contract without Qt or third-party Python packages:

```bash
python3 -m pi_app.tools.validate_qt_ux_contract --json
python3 -m unittest pi_app.tests.test_qt_ux_contract -v
```
