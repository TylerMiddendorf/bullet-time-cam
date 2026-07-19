# Ready USB Storage and Settings Home - 2026-07-19

## Outcome

App 0.2.8 shows removable-USB connection state and a circular used-capacity
gauge on Ready. The gauge also reports available capacity. Settings now has the
same large home-icon action as Library, returning directly to Ready.

Capacity remains scoped to the selected writable removable USB filesystem. A
missing or unreadable volume reports disconnected/unavailable; the protected
Raspberry Pi boot card is never used as a capacity fallback.

## Revision and Deployment

- Capacity-refresh checkpoint: `afd0bae` (`Refresh USB capacity on home`)
- UI checkpoint: `2153c7a` (`Show USB storage on home screen`)
- Final tested source: `2153c7a5b983b2a1d73bb1ee97ae36ae485678ed`
- Both commits were pushed to `origin/main` and fast-forward pulled by the clean
  `/home/username/bullet-time-cam` checkout on `camerapi`.

## Raspberry Pi Verification

- The complete deterministic Pi suite ran 127 tests in 2.414 seconds. All 126
  deterministic tests passed; only the environment-gated live-ledger test was
  skipped as expected.
- Native Wayland Ready and Settings renders were exactly 800x480, found the
  required `storageUsageCircle` and `homeButton` objects, swapped a frame, and
  emitted zero QML errors.
- The Ready fixture render SHA-256 was
  `442bdbff24181435f71b5ac29051f522604fa7d2ef89df970095cc6c0ec29fcb`.
  The Settings fixture render SHA-256 was
  `03273673add00891682474f5f492f969ff42cf88916b8f9b840cea4e2c7c706f`.
- Visual inspection confirmed the circle, percentage, connected status, free
  capacity, and Settings home icon were legible and unclipped.
- A native QML interaction smoke emitted the Settings `homeButton.tapped`
  signal and confirmed Ready loaded by finding its `settingsButton`.
- The production resolver selected
  `/media/username/USB DISK/BulletTime`. It read 247,963,058,176 total bytes,
  10,027,008 used bytes, and 247,953,031,168 free bytes. The production
  controller formatted those values as `10.0 MB` used and `248.0 GB` available.
- After restarting the live service, a compositor capture showed `USB
  CONNECTED`, `0%`, and `248.0 GB FREE`. Zero percent is the correct rounded
  display for approximately 0.004% use. Its SHA-256 was
  `08bcb4474d3f4d3840a31fc7aec0384a05d500b268270012dfb63b9186548ca3`.
- All 39 boot/session checks passed. The live service was active/running as PID
  8095 with `NRestarts=0` and exit status 0. Four stable camera serial paths
  were present, GPIO17 remained output LOW, and `/dev/sda1` remained mounted
  read/write as the product FAT volume.

## Scope

This was a UI and removable-storage status deployment check. It did not create,
modify, or delete product media and did not initiate a new camera capture.
