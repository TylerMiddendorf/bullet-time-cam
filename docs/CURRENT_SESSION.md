# Current Session - Compact Version 1 Enclosure

Status reviewed: July 18, 2026

## Qt UX Implementation Rollback Baseline

- Work on the Qt Quick/PySide6 interface began from Git commit `63420c1`
  (`Accept external V1 power arrangement`) on branch `main`.
- No files were staged when the implementation session began. An existing
  unstaged product-owner edit to `docs/MILESTONE_4_PLAN.md` was deliberately
  left untouched and is not part of the UI rollback baseline.
- To return to the exact pre-UI repository state without discarding unrelated
  working-tree changes, restore the UI commits relative to `63420c1`; do not
  use a destructive working-tree reset.
- Scope guard: implement the supplied UX mockups with a generated temporary
  preview image, but do not implement a live camera stream and do not display
  battery level or battery status.
- The completed Qt runtime is `fb1d1e7`. Pre-UI commit `63420c1`, the installer
  backup, and retained Tk packages provide a documented non-destructive recovery
  path, but an end-to-end rollback drill has not been performed.

## Verified State

- Milestones 1 and 2 are complete. The full four-camera workflow and removable
  USB fault/recovery behavior are physically validated.
- App 0.2.1 survives disappearance of its reviewed GIF, fits bounded errors on
  the 800x480 display, and cleans expired staging safely.
- The product FAT was backed up, repaired, and returned a clean offline check
  after final actual-UI capture `20260718T175104Z_04b69c0b`.
- The product owner accepted an external battery pack as the V1 power solution.
  It supplies separate rated 5 V / 2 A feeds to the Raspberry Pi and powered
  USB hub and has its own battery-percentage display.
- Aggregate measurement, internal battery/charging integration, and automatic
  safe-power sequencing are retired as V1 gates. No electrical measurement or
  coordinated shutdown evidence is claimed.
- The complete removable-media follow-up is in
  [`evidence/milestone-2/focused-retest-and-fat-repair-2026-07-18.md`](evidence/milestone-2/focused-retest-and-fat-repair-2026-07-18.md).
- Native Qt Quick/PySide6 now runs on the Pi's 800x480 Wayland session. Seven
  routes, a bounded real four-camera capture, and the 214-entry USB
  library passed SSH-accessible validation. Preview remains a labeled static
  logo fixture and the UI contains no battery state. Evidence is in
  [`evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md`](evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md).
- The first Qt soft reboot failed to return to the LAN and required a physical
  power cycle. Recovery checks passed, but no persistent journal was available;
  the cause and clean Qt soft-reboot lifecycle remain open.

## Immediate Work

Execute Milestone 4 from [`MILESTONE_4_PLAN.md`](MILESTONE_4_PLAN.md):

1. Measure every enclosure-facing component and connector, including the real
   display bezel/depth, camera modules and ribbons, Raspberry Pi, installed
   hubs/cabling, trigger hardware, shutter, and removable product USB drive.
2. Lay out the four sensors in their straight 4 cm spacing and arrange the
   remaining hardware for cooling, serviceability, cable bend radius, and
   removable-media access.
3. Route and strain-relieve the external pack's separate Pi and powered-hub
   leads; the external pack does not consume internal enclosure volume.
4. Produce and inspect fit-check prints before committing to a complete shell.
5. Assemble and rerun the product capture, display, removable-media, and thermal
   acceptance checks in the closed enclosure.
