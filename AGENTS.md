# Agent Orientation

This repository is a handheld four-camera bullet-time rig, not only an ESP32 camera-firmware project.

## Required Context

Before planning or changing the project, read:

1. `docs/PROJECT_CONTEXT.md` - canonical product goal, architecture, confirmed decisions, constraints, and current state
2. `docs/ROADMAP.md` - ordered project milestones and budget gates
3. `docs/MILESTONE_1_PLAN.md` - active bench-integration checkpoints, tests, and exit criteria
4. `docs/INTERVIEW.md` - product-owner answers and decision history
5. `README.md` - repository overview and current camera-node operating instructions

Do not copy changing project details into this file when a canonical document already owns them.

## Current Direction

- Milestone 0, the four-camera breadboard capture subsystem, is complete.
- Milestone 1, bench-top end-to-end capture through the Raspberry Pi and touchscreen, is active.
- Follow the checkpoint order and cost gates in `docs/MILESTONE_1_PLAN.md`.
- The project is milestone-based and has no fixed deadline.
- Approximately $200 remains for version 1, so avoid purchases until measurements establish requirements.
- Battery integration and enclosure work follow the bench-top end-to-end milestone.

## Documentation Rules

- Treat confirmed decisions differently from provisional engineering recommendations.
- When the product owner changes a requirement, update `docs/PROJECT_CONTEXT.md` and record the decision in `docs/INTERVIEW.md`.
- When milestone scope, ordering, status, or exit criteria change, update `docs/ROADMAP.md` and the active milestone plan.
- Keep `README.md` aligned with the current high-level project state and working firmware instructions.
- When completing a checkpoint, record its evidence and advance status in the relevant planning document.

## Progress Recording

Do not leave planning or orientation documents stale after verified progress.

When work produces a successful result:

1. Record what was demonstrated, the date, and the relevant test or measurement in the active milestone plan.
2. Mark the checkpoint complete only when its exit gate has actually been satisfied.
3. Update `docs/ROADMAP.md` when a milestone changes status, its ordering changes, or the next milestone becomes active.
4. Update the Current State section of `docs/PROJECT_CONTEXT.md` when the project gains a material new capability, piece of integrated hardware, or validated architectural decision.
5. Update `README.md` when the repository's user-facing capabilities, setup, or high-level project state changes.
6. Update this `AGENTS.md` when the active milestone, required reading list, stable guardrails, or current direction changes.
7. Record unresolved failures, limitations, and follow-up work alongside successes so later sessions do not mistake a partial demonstration for completion.

Use `docs/INTERVIEW.md` for product-owner decisions and requirement changes, not routine implementation logs.

Evidence should be concrete where practical: test counts, timing results, checksums, photos, logs, commands, or named output artifacts. Code existing is not by itself proof that a checkpoint works.
