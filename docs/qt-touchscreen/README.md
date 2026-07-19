# Qt Touchscreen Migration Validation Track

Status: independent implementation/validation track based on Git commit
`1ef1ba6`; not a canonical milestone or product-decision document.

This directory defines a testable V1 UX contract and a repeatable validation
path for migrating the Raspberry Pi touchscreen from Tkinter to Qt Quick with
PySide6. It does not claim that the Qt implementation has shipped or passed on
the physical rig.

## Scope

- 800x480 full-screen touchscreen presentation
- Product-logo handoff, readiness, capture progress, complete review, partial
  review, and actionable error states
- Headless Qt tests and screenshot evidence
- Raspberry Pi deployment, health checks, and recovery to the known Tkinter
  baseline

Explicitly excluded:

- Live camera streaming or a live-preview pipeline
- Battery level, charge, power-source, or battery-status UI
- Camera settings, media library/browsing/deletion, network controls, and
  12-camera concepts
- Changes to `docs/MILESTONE_4_PLAN.md`

## Source Priority

When sources disagree, use this order:

1. Confirmed decisions in `docs/PROJECT_CONTEXT.md` and
   `docs/INTERVIEW.md`
2. Milestone ordering and scope in `docs/ROADMAP.md`
3. Existing receiver events and storage safety behavior
4. V1 visual concepts `designs/ux-mockups/01-v1-ready.png` through
   `03-v1-review-partial.png`
5. Engineering choices in this directory

The mockups are visual references, not authority to add out-of-scope features.
They are 1619x971 reference renders, not pixel-perfect raster backgrounds: the
implementation lays out native 800x480 Qt objects. The battery glyph and its
reserved header compartment in `01-v1-ready.png` are deliberately omitted.

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

The machine-readable companion contract lives at
`pi_app/qt_validation/ux_contract.json`. It is intentionally separate from the
current production UI so this track can be reviewed and tested without changing
the known-good Tkinter path.
