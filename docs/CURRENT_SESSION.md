# Current Session — Milestone 2 Removable-Media Qualification

Status reviewed: July 18, 2026

## Starting State

- Milestone 1 is complete. The physical shutter and normal touchscreen/GPIO17
  paths both produce integrated four-camera originals, atomic manifests, ordered
  six-frame GIFs, and full-screen review on the Raspberry Pi.
- The qualifying physical-rig run completed 25/25 normal sets, 100 originals,
  and 25 GIFs. Every logical camera unavailability, checksum corruption,
  mid-transfer truncation, recovery, and reboot-identity scenario passed the
  byte validator and environment-gated E2E test.
- Representative normal and corrected Camera 4 partial-result screens were
  photographed. The presentation defect found during the first partial visual
  run was fixed in `710eadd`.
- Camera firmware 0.2.3 is installed on all four nodes. Camera 4 passed a final
  bounded startup smoke, `bullet-time-ui.service` is active, and GPIO17 is
  output LOW.
- The full evidence summary and scenario ledger are under
  [`evidence/milestone-1/checkpoint-5/`](evidence/milestone-1/checkpoint-5/).
- Complete-set review time was 3.250 seconds median and 3.289 seconds maximum,
  so the soft two-second target remains an explicit optimization item.

## Immediate Work

1. Test removable-drive unplug/replug and automatic remount in the normal
   product service context.
2. Exercise visible missing, full, read-only/corrupt, and removal-during-write
   failure behavior without falling back to the boot microSD.
3. Verify deterministic selection when more than one writable USB drive is
   present.
4. Retain persisted artifacts and service/UI evidence for each real-drive fault
   and recovery case under `docs/evidence/milestone-2/`.
5. Measure aggregate electrical power before choosing battery, charging,
   regulation, monitoring, or safe-power-cut hardware.

The completed bench milestone plan remains at
[`MILESTONE_1_PLAN.md`](MILESTONE_1_PLAN.md), and the current ordering and budget
gates are in [`ROADMAP.md`](ROADMAP.md).
