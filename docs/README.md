# Documentation Index

Project documents are organized by ownership so changing state has one canonical
home. Update linked summaries only when needed for navigation; do not copy full
status narratives between files.

## Canonical Project State

- [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md) — durable product goal, architecture,
  confirmed decisions, constraints, and current state
- [`ROADMAP.md`](ROADMAP.md) — milestone order, status, cost gates, and exit criteria
- [`MILESTONE_1_PLAN.md`](MILESTONE_1_PLAN.md) — detailed plan for the active milestone
- [`CURRENT_SESSION.md`](CURRENT_SESSION.md) — concise handoff for the active checkpoint
- [`INTERVIEW.md`](INTERVIEW.md) — dated product-owner decisions and requirement changes

## Test Plans and Runbooks

- [`FOUR_NODE_E2E_TEST_PLAN.md`](FOUR_NODE_E2E_TEST_PLAN.md) — executable Checkpoint 5 acceptance contract
- [`TRIGGER_CIRCUIT.md`](TRIGGER_CIRCUIT.md) — approved shared-trigger wiring and validation
- [`RASPBERRY_PI_BOOT_RUNBOOK.md`](RASPBERRY_PI_BOOT_RUNBOOK.md) — reproduce, verify, recover, or roll back the product boot state
- [`RASPBERRY_PI_SSH.md`](RASPBERRY_PI_SSH.md) — non-secret Pi access boundary and recovery guidance

## Evidence and History

- [`evidence/README.md`](evidence/README.md) — milestone/checkpoint evidence index
- [`history/`](history/) — completed implementation-session logs retained for context

Evidence proves only the checkpoint and hardware state named by its plan. Code
existence or an older successful demonstration is not evidence that a later
integration gate works.
