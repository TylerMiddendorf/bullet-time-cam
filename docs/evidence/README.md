# Evidence Index

Evidence is grouped by the milestone and checkpoint whose exit gate it supports.
Raw logs, screenshots, manifests, and summaries stay together so a result can be
reviewed without searching one large flat directory.

## Milestone 1 — Bench-Top End-to-End Capture

- [`checkpoint-1/`](milestone-1/checkpoint-1/) — Raspberry Pi, display, USB, and bench inventory
- [`checkpoint-4/`](milestone-1/checkpoint-4/) — one-node trigger-to-screen vertical slice, protocol fault/recovery tests, firmware deployment, electrical inspection, and four-node trigger integrity
- [`checkpoint-5/`](milestone-1/checkpoint-5/) — completed four-node product grouping, GIF/touchscreen flow, 25-cycle reliability, per-camera partial failures, corrupt/truncated recovery, reboot identity, byte validator, and UI photographs

## Milestone 2 — User-Removable USB Media

- [`removable-media-qualification-2026-07-18.md`](milestone-2/removable-media-qualification-2026-07-18.md)
  — complete real-Pi hardware matrix covering normal/reboot/reinsert/remount,
  missing/full/read-only/corrupt/mid-write loss, recovery, deterministic
  two-drive selection, and the physical-rig E2E test; it records the initial
  media-safety pass and the UI/filesystem findings discovered during that run
- [`focused-retest-and-fat-repair-2026-07-18.md`](milestone-2/focused-retest-and-fat-repair-2026-07-18.md)
  — app 0.2.1 fixes, automated tests, file-for-file product backup, FAT repair,
  stale-staging cleanup, focused real-UI removal/error retest, clean post-capture
  FAT check, and final byte-valid capture closing Milestone 2

- [`../MILESTONE_2_PLAN.md`](../MILESTONE_2_PLAN.md) — completed fault procedures,
  safety boundaries, evidence requirements, and exit gates
- [`milestone-2/`](milestone-2/) — USB-media discovery, mount bring-up, and
  qualifying fault/recovery evidence

Each new evidence directory should include or link to the relevant plan, state
the date and tested revision, distinguish successful gates from limitations,
and retain concrete artifacts where practical.
