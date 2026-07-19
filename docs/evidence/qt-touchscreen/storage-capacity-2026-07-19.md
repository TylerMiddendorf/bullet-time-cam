# Removable Storage Capacity - Raspberry Pi Evidence

Date: July 19, 2026

Final deployed code commit: `6398f3a` (`Separate library capacity values`)

Feature commit: `81a2a49` (`Show removable storage capacity in library`)

## Scope and source boundary

- App 0.2.3 shows used and available capacity plus a utilization bar in the
  removable-media library sidebar.
- Opening the library resolves the selected writable USB volume, scans its
  `BulletTime/` catalog, and reads capacity from that same filesystem.
- A successful deletion refreshes both the catalog and the capacity figures.
- Missing or unreadable removable media reports `UNAVAILABLE`; the calculation
  does not fall back to the Raspberry Pi boot microSD.

## Git deployment chain

- The feature commit was pushed to `origin/main`, then the clean Pi checkout at
  `/home/username/bullet-time-cam` fast-forwarded from `c6ad92a` to `81a2a49`.
- Visual inspection of the first native render found the side-by-side capacity
  values touching. The layout correction was committed as `6398f3a`, pushed,
  and fast-forward pulled on the Pi before the final render.
- The final Pi checkout and `origin/main` were clean and aligned at full commit
  `6398f3ac0969571f5dcec395d3da4fd2e3b5323f`.

## Automated and live-storage results

- Windows development host: 121 tests ran; 120 passed and the environment-gated
  live-evidence test skipped as expected. All repository pre-commit and
  pre-push checks passed.
- Raspberry Pi at `81a2a49`: the same 121-test suite ran in 2.421 seconds; 120
  passed and the same live-evidence test skipped.
- The Pi resolver selected `/media/username/USB DISK/BulletTime` on `/dev/sdb1`.
  The production controller reported `327.7 KB USED / 248.0 GB AVAILABLE` and a
  used fraction of `0.0000013214871699453645`.
- Independent `df -B1` output matched the backend exactly: 247,963,058,176 total
  bytes, 327,680 used bytes, and 247,962,730,496 available bytes.
- The connected product volume contained zero capture-set directories during
  this check. No media was created, changed, or deleted during validation. This
  current empty-volume observation supersedes neither the earlier historical
  capture evidence nor its recorded artifact counts.

## Native 800x480 render

The final Pi-native Wayland smoke found the `storageUsageMetric` object, observed
the first frame at exactly 800x480, and emitted zero QML errors. The corrected
render SHA-256 was
`bf3b71ed3a770890ae6b14d7e7c51eb69b4ed3e2e8d7789d46927f5eeb6179ef`.

Visual inspection confirmed that the stacked USED and AVAILABLE rows are
separate and legible, the utilization bar stays inside its card, and the
existing catalog, page controls, and three primary actions remain inside the
viewport. The harness used representative `18.6 GB` and `231.4 GB` values for
the visual render; the real-volume figures above were separately exercised
through the production resolver and controller on the same Pi.

## Final runtime state

- `bullet-time-ui.service` was restarted after rendering and was active/running
  at PID 4719 with `NRestarts=0` and `ExecMainStatus=0`.
- Every boot-experience verifier check passed; native Wayland remained active
  without Xwayland.
- GPIO17 was configured as output LOW after deployment.
- The running source reports app version 0.2.3.

