# Documentation Index

Project documents are organized by ownership so changing state has one canonical
home. Update linked summaries only when needed for navigation; do not copy full
status narratives between files.

## Canonical Project State

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) — durable product goal, architecture,
  confirmed decisions, constraints, and current state
- [`ROADMAP.md`](ROADMAP.md) — milestone order, status, cost gates, and exit criteria
- [`MILESTONE_1_PLAN.md`](MILESTONE_1_PLAN.md) — completed bench end-to-end milestone plan and measured exit evidence
- [`MILESTONE_2_PLAN.md`](MILESTONE_2_PLAN.md) — completed removable-media qualification procedures, evidence requirements, and exit result
- [`MILESTONE_3_PLAN.md`](MILESTONE_3_PLAN.md) — closed/retired aggregate-power and safe battery-integration plan
- [`MILESTONE_4_PLAN.md`](MILESTONE_4_PLAN.md) — active enclosure layout, print, and acceptance gates
- [`CURRENT_SESSION.md`](CURRENT_SESSION.md) — concise handoff for active enclosure work
- [`INTERVIEW.md`](INTERVIEW.md) — dated product-owner decisions and requirement changes

## Test Plans and Runbooks

- [`FOUR_NODE_E2E_TEST_PLAN.md`](FOUR_NODE_E2E_TEST_PLAN.md) — executable four-node acceptance contract used for the July 18 hardware pass
- [`TRIGGER_CIRCUIT.md`](TRIGGER_CIRCUIT.md) — approved shared-trigger wiring and validation
- [`RASPBERRY_PI_BOOT_RUNBOOK.md`](RASPBERRY_PI_BOOT_RUNBOOK.md) — reproduce, verify, recover, or roll back the product boot state
- [`RASPBERRY_PI_SSH.md`](RASPBERRY_PI_SSH.md) — non-secret Pi access boundary and recovery guidance

## Evidence and History

The independent [`Qt touchscreen validation track`](qt-touchscreen/README.md)
defines the shipped seven-route Qt Quick contract, deterministic headless
strategy, evidence templates, and Pi deployment/rollback checklist. Deployment
results and native 800x480 route captures are under
[`evidence/qt-touchscreen/`](evidence/qt-touchscreen/).

- [`evidence/README.md`](evidence/README.md) — milestone/checkpoint evidence index
- [`history/`](history/) — completed implementation-session logs retained for context

Evidence proves only the checkpoint and hardware state named by its plan. Code
existence or an older successful demonstration is not evidence that a later
integration gate works.

## Design References

The native 800x480 seven-route adaptation is specified in
[`qt-touchscreen/UX_SPEC.md`](qt-touchscreen/UX_SPEC.md) under the current
four-camera, no-live-preview, no-battery, and no-hotspot scope guards.

- [`../designs/ux-mockups/README.md`](../designs/ux-mockups/README.md) —
  non-binding touchscreen concepts organized by V1, fast-follow, and later scope
