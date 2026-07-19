# Removable Storage Capacity - Raspberry Pi Evidence

Date: July 19, 2026

Final deployed code commit: `00d7531` (`Fix asynchronous library refresh results`)

Feature commit: `81a2a49` (`Show removable storage capacity in library`)

## Scope and source boundary

- App 0.2.4 shows used and available capacity plus a utilization bar in the
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
  `00d753180e1fbda5c00759ede9edfaac4398afac` after the regression fix.

## Post-deployment failure and root cause

The initial acceptance at `6398f3a` was incomplete. It validated the capacity
backend and QML layout separately but did not exercise the asynchronous handoff
between them in the running product UI. After a real four-camera capture, the
product owner reported that the new set and capacity were both absent.

SSH inspection found complete capture `20260719T180653Z_8f63b1f9` on `/dev/sdb1`
with four JPEG originals, its GIF, and a valid schema-2 manifest. A direct
production catalog scan returned that one entry and calculated `3.8 MB` used and
`248.0 GB` available. A live compositor screenshot instead showed the library
stuck at `REFRESHING REMOVABLE USB MEDIA`, zero capture sets, and `UNAVAILABLE`.

The background worker queued `(catalog, storage_usage)`, but the Qt poller passed
that tuple as one positional argument to `apply_catalog`. The resulting callback
exception prevented the refresh result from being applied. Commit `00d7531`
replaces the loose result queues with `_AsyncResultQueue`, whose `drain` method
always expands each worker result into the callback's original arguments. The
same mechanism now handles catalog scan, media open, and deletion results.

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
- After the user capture exposed the handoff defect, the Windows and Pi suites
  each ran 122 tests at `00d7531`; 121 passed and only the environment-gated
  live-evidence test skipped. The new regression test enters the library,
  queues a real catalog snapshot and capacity result together, drains the exact
  runtime result mechanism, and requires the capture entry plus both formatted
  capacity values to replace the loading state.
- A focused Pi exercise of that fixed path against the real product volume
  applied one result, changed catalog state to `ready`, returned capture
  `20260719T180653Z_8f63b1f9`, and reported `3.8 MB` used / `248.0 GB` available.

## Native 800x480 render

The Pi-native Wayland layout smoke found the `storageUsageMetric` object, observed
the first frame at exactly 800x480, and emitted zero QML errors. The corrected
render SHA-256 was
`bf3b71ed3a770890ae6b14d7e7c51eb69b4ed3e2e8d7789d46927f5eeb6179ef`.

Visual inspection confirmed that the stacked USED and AVAILABLE rows are
separate and legible, the utilization bar stays inside its card, and the
existing catalog, page controls, and three primary actions remain inside the
viewport. The harness used representative `18.6 GB` and `231.4 GB` values for
the visual render; the real-volume figures above were separately exercised
through the production resolver and controller on the same Pi. This harness
render did not test the asynchronous runtime handoff; that validation gap and
its subsequent regression coverage are documented above.

## Final runtime state

- `bullet-time-ui.service` was restarted with the corrected code and was
  active/running at PID 5036 with `NRestarts=0`.
- Every boot-experience verifier check passed; native Wayland remained active
  without Xwayland.
- GPIO17 was configured as output LOW after deployment.
- The running source reports app version 0.2.4.
