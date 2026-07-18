# Milestone 2 Removable-Media Qualification - 2026-07-18

Status: initial hardware matrix executed; findings later closed by focused retest

## Tested Baseline

- Raspberry Pi repository revision: `710eadd09709faf4826fc26a9ccb6c5c66c27b2b`
- Initial boot ID: `c8d6eae1-ed16-4598-be3f-60137e569b80`
- Post-reboot ID: `fd841dec-65af-492d-98f5-9113d701f1f5`
- Protected boot filesystem: `/dev/mmcblk0p2`, ext4, mounted at `/`
- Product media: USB serial `900049666ACEB315`, UUID `B67C-53C4`, 231 GB
  FAT, label `USB DISK`, normally mounted at `/media/username/USB DISK`
- Expendable media: USB serial `900048D90E707A22`, destructively reduced to a
  64 MiB FAT32 partition labeled `M2TEST` for the fault tests
- All four stable Espressif `/dev/serial/by-id` identities were present.
- `bullet-time-ui.service` was active and GPIO17 was output LOW before and
  after the completed test run.
- The deterministic suite passed locally: 68 tests run with the one
  environment-gated hardware test skipped. The same deterministic Pi run had
  67 passes and only the live test's absent ledger blocked that invocation.
  Supplying the existing four-node ledger at `/tmp/m2-four-node-e2e-ledger.json`
  made the environment-gated physical-rig test pass separately in 47.189 seconds.

Block-device letters changed after USB unbind/rebind operations. Every
destructive action was therefore guarded by the recorded USB serial and
sysfs ancestry rather than an assumed `/dev/sdX` name. The product drive and
boot microSD were never formatted, filled, or deliberately corrupted.

## Checkpoint Results

### 1 - Restart, idle removal/reinsertion, automatic remount, and reboot

Normal baseline `20260718T144202Z_c98e96d9`, post-reboot UI capture
`20260718T145225Z_72bf4d6e`, and automatic-remount UI capture
`20260718T145328Z_37c5ca06` each contained four byte-valid originals, a valid
ordered GIF, and correct product-drive manifest metadata. The automatic-remount
capture completed in 2509.653 ms; its display callback arrived at 6572.534 ms.

The product drive was then powered off while idle, physically unplugged and
reinserted, and recovery capture `20260718T154132Z_f05fea19` passed all four
cameras without a code or configuration change. A final actual-UI product
capture after the complete fault matrix, `20260718T163525Z_3a578613`, also
passed all byte checks and recorded the product UUID/source correctly. Its
retained manifest is
[`final-product-20260718T163525Z_3a578613-manifest.json`](final-product-20260718T163525Z_3a578613-manifest.json).

A separate bounded headless automatic-remount attempt timed out at 60 seconds
without publishing a capture. The actual running-service click immediately
afterward passed and is the qualifying automatic-remount evidence.

### 2 - Missing media

With no USB block media present, an injected click into the running Tk label
exercised the production `<Button-1>` binding. Capture was blocked before a Pi
trigger: camera sequence remained 2, GPIO17 stayed LOW, the service remained
active, and the boot-card artifact inventory did not change.

A controlled 100 ms GPIO17/NPN action then exercised the same shared active-low
bus as the physical shutter. The four nodes captured sequence 3, but the Pi
failed closed and committed nothing to internal storage. After reinsertion,
the successful recovery set contained sequence 4 from all cameras, proving the
touch action was blocked and the shared-bus action was received but rejected.
Screenshots are
[`missing-media-ui-2026-07-18.png`](missing-media-ui-2026-07-18.png) and
[`missing-media-physical-ui-2026-07-18.png`](missing-media-physical-ui-2026-07-18.png).

### 3 - Full, read-only, and corrupt/unmountable media

The expendable drive first passed baseline capture
`20260718T155300Z_afa044f2`. It was then filled to 98% with a temporary 59 MiB
file. An actual UI capture failed with `ENOSPC`; no capture directory or staging
artifact was published, the service stayed active, GPIO17 returned LOW, and the
boot-card inventory remained 8 files with SHA-256
`8e5f7f458313121b2a235e3b20c6ee8f4a12bae6d9ac2f71c3e6a783add358ef`.
The filler was removed and recovery `20260718T155603Z_6fcac2c5` passed. See
[`full-media-ui-2026-07-18.png`](full-media-ui-2026-07-18.png) and
[`full-recovery-20260718T155603Z_6fcac2c5-manifest.json`](full-recovery-20260718T155603Z_6fcac2c5-manifest.json).

For the qualifying read-only test, the product USB-storage interface was
unbound so it could not be selected and `M2TEST` was the only media, mounted
read-only. The actual UI click was blocked, GPIO17 remained LOW, the service
stayed active, and neither the media listing nor boot-card inventory changed.
After restoring the drive read-write, recovery `20260718T160300Z_e9bf8aac`
passed all four cameras. See
[`read-only-media-isolated-ui-2026-07-18.png`](read-only-media-isolated-ui-2026-07-18.png)
and
[`read-only-recovery-20260718T160300Z_e9bf8aac-manifest.json`](read-only-recovery-20260718T160300Z_e9bf8aac-manifest.json).
Earlier read-only attempts were discarded because the automounter correctly
selected the still-attached writable product drive.

For corrupt/unmountable media, only the expendable partition's verified first
512-byte boot sector was zeroed. UDisks rejected it as unmountable. Startup and
UI-click paths reported the mount failure; the service stayed active, GPIO17
remained LOW, and the boot-card inventory did not change. After reformatting the
expendable drive, recovery `20260718T160727Z_583e49df` passed. See
[`corrupt-media-startup-ui-2026-07-18.png`](corrupt-media-startup-ui-2026-07-18.png),
[`corrupt-media-click-ui-2026-07-18.png`](corrupt-media-click-ui-2026-07-18.png),
and
[`corrupt-recovery-20260718T160727Z_583e49df-manifest.json`](corrupt-recovery-20260718T160727Z_583e49df-manifest.json).

### 4 - Removal during write

An actual UI capture created staging directory
`.20260718T163114Z_0c95d8d0.part` on `M2TEST`. Immediately after detecting that
directory, the test unbound only the expendable drive's verified USB-storage
interface. This deterministic kernel-level removal exercised loss during an
active write without disturbing camera USB, power, or trigger wiring; it was
not a literal cable pull.

The kernel logged offline/write and FAT I/O errors. The UI reported `EIO`, the
service remained active, GPIO17 returned LOW, the interrupted capture was not
published, and the boot-card inventory was unchanged. See
[`removal-during-write-ui-2026-07-18.png`](removal-during-write-ui-2026-07-18.png).
Offline read-only `fsck.vfat` found a dirty bit and 348 orphaned clusters
(178176 bytes), demonstrating that repair was required. The expendable drive
was reformatted; recovery `20260718T163341Z_73b96051` passed all four cameras,
and a subsequent cleanly unmounted offline `fsck.vfat -n -v` returned zero with
no errors. Its manifest is
[`mid-write-recovery-20260718T163341Z_73b96051-manifest.json`](mid-write-recovery-20260718T163341Z_73b96051-manifest.json).

### 5 - Multiple USB drives

With both drives writable, the configured `USB DISK` preference won and
capture `20260718T154517Z_697ca950` was published wholly on the product drive.
With the product drive unmounted, fallback captures
`20260718T154616Z_28788d08` and, after a service restart,
`20260718T154713Z_d98c72f3` were published wholly on the expendable drive. See
[`fallback-20260718T154616Z_28788d08-manifest.json`](fallback-20260718T154616Z_28788d08-manifest.json)
and
[`fallback-20260718T154713Z_d98c72f3-manifest.json`](fallback-20260718T154713Z_d98c72f3-manifest.json).

With the preference disabled in an in-memory test configuration, five resolver
scans consistently chose the lexical mount path
`/media/username/USB DISK/BulletTime`; hardware capture
`20260718T154847Z_7a67b3fd` passed on that destination. No capture was split
between drives, and the deployed configuration was not changed.

## Defects and Limitations

1. **UI poll crash after media removal.** When the product drive containing the
   currently reviewed GIF was detached, the UI poll callback tried to reopen
   the disappeared file and raised `FileNotFoundError` in `ui.py` `show_media()`.
   The process, service, receiver, and later capture remained alive, but display
   event polling stopped until `bullet-time-ui.service` was restarted. The
   stalled presentation is retained in
   [`two-drive-ui-stalled-2026-07-18.png`](two-drive-ui-stalled-2026-07-18.png).
2. **Storage errors are clipped.** Missing, full, read-only, corrupt, and
   mid-write failure strings exceed the 800x480 screen. Storage is identifiable
   as the failure class, but substantial text is outside the visible area, so
   the plan's clear-error exit claim is not met.
3. **Product FAT is dirty.** Read-only offline `fsck.vfat -n -v` exited 1,
   reported the dirty bit, and found a one-byte primary/backup boot-sector
   difference at offset 65. Kernel warnings recur on mounts. No repair was made;
   useful product media should be backed up before repair is authorized.
4. **A pre-existing stale staging directory remains.** Product-drive directory
   `.20260718T015549Z_273b2de6.part`, dated July 17, contains four JPEGs and a
   zero-byte GIF with no manifest. It is clearly uncommitted, but automatic
   stale-staging cleanup is not implemented.
5. The mid-write loss was a serial-verified USB-storage unbind rather than a
   literal cable yank. It is deterministic evidence for the software and
   filesystem behavior; a literal yank remains optional corroboration if the
   product owner requires that exact physical mechanism.
6. `/home/username/DISK/BulletTime/e2e-20260718` is empty. Four historical
   one-camera files remain under repository `pi_app/captures/`; before/after
   inventories prove none were created or changed by this qualification.

## Final State and Exit Decision

At handoff, the product drive is mounted at `/media/username/USB DISK`, the
expendable 64 MiB `M2TEST` partition is clean and unmounted,
`bullet-time-ui.service` is active, GPIO17 is output LOW, and final product
capture `20260718T163525Z_3a578613` is byte-valid for all four cameras.

All five checkpoint scenario families were exercised on the Raspberry Pi. The
fail-closed and atomic-publication safety behavior passed, no test wrote new
media to the boot microSD, deterministic selection passed, and every isolated
fault recovered to a byte-valid four-camera capture. At this initial handoff,
Milestone 2 remained open until the UI poll crash, clipped storage errors,
product FAT health, and stale staging directory were resolved.

## Later July 18 Resolution

The follow-up deployed app 0.2.1, caught the live missing-review exception
without terminating Tk polling, fit the storage errors within 800x480, added
guarded expired-staging cleanup, backed up all product files with full SHA-256
agreement, and repaired the product FAT. The FAT passed a clean offline check
again after final byte-valid capture `20260718T175104Z_04b69c0b`. The exact
implementation, backup, repair, focused retest, screenshots, and final state are
recorded in
[`focused-retest-and-fat-repair-2026-07-18.md`](focused-retest-and-fat-repair-2026-07-18.md).
That evidence closes Milestone 2. The serial-verified USB-interface unbind
remains recorded as the mid-write test method rather than a literal cable yank.
