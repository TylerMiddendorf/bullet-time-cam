# Agent Guidelines

## Required Context

Before planning or changing the project, read:

1. `docs/PROJECT_CONTEXT.md` for the canonical product goal, architecture, decisions, constraints, and current state.
2. `docs/ROADMAP.md` for milestone ordering, status, and budget gates.
3. The plan for the active milestone identified by `docs/ROADMAP.md`, when one exists, for checkpoints, tests, and exit criteria.
4. `docs/INTERVIEW.md` for product-owner decisions and requirement history.
5. `README.md` for the repository overview and current operating instructions.

Do not duplicate changing project details in this file. Keep project state, active work, inventory, budget, and milestone-specific direction in their canonical documents.

## Documentation Ownership

- Distinguish confirmed product decisions from provisional engineering recommendations.
- When the product owner changes a requirement, update `docs/PROJECT_CONTEXT.md` and record the decision in `docs/INTERVIEW.md`.
- When milestone scope, ordering, status, or exit criteria change, update `docs/ROADMAP.md` and the affected milestone plan.
- Update the Current State section of `docs/PROJECT_CONTEXT.md` when the project gains a material capability, integrated hardware, or validated architectural decision.
- Keep `README.md` aligned with user-facing capabilities, setup, operating instructions, and high-level project state.
- Use `docs/INTERVIEW.md` for product-owner decisions and requirement changes, not routine implementation logs.

## Evidence and Progress

- Do not treat code existing as proof that hardware or an end-to-end checkpoint works.
- Record successful demonstrations in the relevant milestone plan with the date and concrete evidence where practical, such as test counts, timings, checksums, photos, logs, commands, or named output artifacts.
- Mark a checkpoint complete only after its exit gate has been satisfied.
- Record unresolved failures, limitations, and follow-up work alongside successes so partial demonstrations are not mistaken for completion.
- Keep planning and orientation documents current after verified progress.
