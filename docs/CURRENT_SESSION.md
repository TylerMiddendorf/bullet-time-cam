# Current Session - Aggregate Power Measurement

Status reviewed: July 18, 2026

## Verified State

- Milestone 2 removable USB qualification is complete at Raspberry Pi revision
  `8fd1f17a774b2b093971b817a36d97aca0f6a806`, app version `0.2.1`.
- The UI survives disappearance of its reviewed GIF without a service restart.
  Missing-media and camera-disconnect messages fit the 800x480 screen.
- Guarded one-hour cleanup removed the pre-existing stale staging directory.
- The product FAT was backed up file-for-file, repaired, and returned a clean
  offline `fsck.vfat -n -v` result again after final capture
  `20260718T175104Z_04b69c0b`.
- That final actual-UI capture passed byte validation for Cameras 1-4 and GIF
  order `[1, 2, 3, 4, 3, 2]` on the product drive.
- `bullet-time-ui.service` is active, GPIO17 is output LOW, all four stable
  camera identities are present, and the product USB drive is mounted writable.
  The clean 64 MiB `M2TEST` partition is attached and unmounted.
- The complete focused evidence is in
  [`evidence/milestone-2/focused-retest-and-fat-repair-2026-07-18.md`](evidence/milestone-2/focused-retest-and-fat-repair-2026-07-18.md).

## Immediate Work

Begin Milestone 3 with aggregate bench-power measurement before selecting any
battery, regulator, charger, fuel gauge, or shutdown controller.

1. Identify a suitable external inline power instrument and its voltage/current
   range, sample/logging capability, burden voltage, and connection point.
2. Measure the complete final V1 bench chain, including Raspberry Pi, display,
   final hubs/cabling, four camera nodes, and product USB storage.
3. Record stable idle, one real touchscreen-triggered four-camera capture,
   transfer/processing/review, and observed peak current/power. Repeat enough
   captures to establish representative and maximum values.
4. Record source voltage at the load during peak activity and any Pi
   undervoltage/throttling indication. Software resource metrics are not a
   substitute for the electrical measurement.
5. Use measured demand only after this evidence to set runtime/captures-per-
   charge targets and evaluate battery, regulation, charging, monitoring, and
   safe-power-cut hardware.

No suitable aggregate electrical instrument has yet been identified in the
repository evidence. Do not infer system power from USB descriptors or Linux
software counters.
