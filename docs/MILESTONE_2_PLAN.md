# Milestone 2 Plan - User-Removable USB Media Qualification

Status: active July 18, 2026

## Outcome

Prove that removable USB media is a safe product boundary, not only a working
normal-case destination. The Raspberry Pi must persist valid capture sets to a
writable USB-backed filesystem, fail visibly and without boot-card fallback
when that destination is unusable, and recover without manual source-code or
configuration changes.

Milestone 1 already proves normal four-node capture, atomic persistence, GIF
generation, touchscreen review, and reboot continuity on the installed USB
drive. This milestone qualifies real-media lifecycle and fault behavior.

## Scope and Safety Boundary

In scope:

- Normal application-service capture to the selected USB drive
- Service restart, idle unplug/replug, and automatic remount
- Missing, full, read-only, corrupt/unmountable, and removal-during-write media
- Deterministic selection with more than one writable USB drive
- Visible error behavior, atomic publication, recovery, and proof of no boot-card fallback

Out of scope:

- Aggregate power measurement and battery selection
- Enclosure port design
- User-facing gallery, deletion, or media-formatting tools
- Repairing arbitrary damaged customer filesystems

Use the validated product drive for normal, restart, idle unplug/replug, and
multi-drive selection tests only. Use a clearly identified expendable USB drive
with no needed data for full, corrupt/unmountable, and removal-during-write
tests. Before any fault setup, resolve and record the exact block device,
filesystem, mountpoint, transport, and capacity. Never format, fill, corrupt, or
unmount the Raspberry Pi boot device or an unresolved device path.

## Required Baseline

Before each physical test session:

1. Record the tested Git revision, Raspberry Pi boot ID, application and camera
   firmware versions, and `bullet-time-ui.service` state.
2. Confirm GPIO17 is output LOW and all four stable camera identities are present.
3. Record the boot device and every attached USB block device, including USB
   ancestry, filesystem, label, mountpoint, and free space.
4. Confirm the intended test drive is writable by the application user and the
   boot microSD is a different block device.
5. Complete one normal four-camera capture, validate its JPEG/GIF bytes and
   manifest storage metadata, and retain its capture ID as the baseline.
6. Create a new evidence directory under `docs/evidence/milestone-2/` for the
   session. Do not mix exploratory attempts with qualifying evidence.

## Checkpoint 1 - Restart and Idle Unplug/Replug

Procedure:

1. Restart the normal user service with the validated drive mounted and make a
   complete four-camera capture.
2. Remove the drive only while the application is idle and no capture or write
   is active.
3. Confirm the UI reports unavailable storage and the service remains alive.
4. Reinsert the same drive and allow the normal service context to request or
   observe its mount without editing configuration.
5. Make another complete four-camera capture and validate every original, GIF,
   manifest, and storage record.
6. Reboot once with the drive attached and prove one more normal capture after
   startup.

Exit gate:

- Restart, idle removal, reinsertion, automatic remount, and reboot recovery
  require no code/configuration edit or boot-card media fallback.
- Pre-removal and post-recovery capture sets remain byte-valid and distinct.

## Checkpoint 2 - Missing Media

Procedure:

1. Remove all writable USB storage while the application is idle.
2. Attempt one touchscreen capture. It must be blocked before GPIO17 is pulsed
   and must show a clear storage error.
3. Press the physical shutter once. The nodes may capture because the Pi does
   not own that physical action, but the Pi must reject the incoming data rather
   than commit it internally.
4. Compare application-owned internal paths and the USB mount state before and
   after both attempts; no new capture directory, JPEG, manifest, GIF, or
   leftover partial may appear on the boot filesystem.
5. Reinsert the validated drive and complete a normal recovery capture.

Exit gate:

- Touch capture is blocked, physical capture fails closed, the UI communicates
  the fault, no boot-card capture artifact is created, and ordinary capture
  recovers after reinsertion.

## Checkpoint 3 - Full, Read-Only, and Corrupt/Unmountable Media

Run each condition separately with a verified expendable USB drive and restore
a clean writable state between conditions.

Procedure for each condition:

1. Establish and record the condition without modifying the boot device:
   insufficient free space for a capture set, a read-only mounted filesystem,
   or a deliberately unmountable/invalid test filesystem.
2. Start one capture through the normal UI when selection permits it, or record
   the pre-capture rejection when the resolver correctly excludes the drive.
3. Confirm the UI identifies storage as the reason for failure and the service
   remains responsive.
4. Confirm no incomplete capture directory is published and no `.part` file or
   artifact appears on the boot filesystem.
5. Restore or replace the expendable media, then complete and byte-validate one
   normal recovery capture.

Exit gate:

- Full, read-only, and corrupt/unmountable media each fail visibly and
  atomically, never fall back to the boot card, and do not require a Pi reboot
  to recover unless filesystem repair itself requires one. Any required reboot
  must be recorded as a limitation rather than hidden.

## Checkpoint 4 - Removal During Write

This test may damage the selected filesystem. Back up any useful contents and
use only a verified expendable drive.

Procedure:

1. Begin one normal four-camera capture and retain logs that show the capture
   entered loading and storage staging began.
2. Remove only the expendable USB drive while that capture is actively writing;
   do not disturb camera USB data, shared power, or trigger wiring.
3. Confirm the application reports a storage failure, remains responsive, and
   does not publish the interrupted capture as valid or write it to the boot card.
4. Reinsert the drive, inspect its filesystem health outside the application,
   and record whether repair was needed.
5. Restore a writable USB destination and complete a byte-valid recovery capture.

Exit gate:

- The interrupted set is absent or clearly uncommitted, no partial artifact is
  treated as valid, the boot card remains unused for media, and a later capture
  succeeds after storage recovery.

## Checkpoint 5 - Multiple USB Drives

Procedure:

1. Attach the validated `USB DISK` and one additional writable USB drive.
2. Confirm the configured preferred mount name wins and that the manifest names
   the selected source device, filesystem, mountpoint, and capture root.
3. Remove the preferred drive while idle and confirm the remaining eligible
   drive is selected consistently on repeated rescans and service restart.
4. When testing without a configured preference, confirm repeated selection is
   deterministic by mount path.
5. Complete and validate a capture in each selection state. A single capture
   set must never be split across drives.

Exit gate:

- Preferred and fallback selection match the documented rules, selection is
  deterministic, manifests identify the actual destination, and each capture
  set is published wholly on one drive.

## Evidence Requirements

For every qualifying scenario retain:

- Tested revision, boot ID, application/firmware versions, and service state
- Exact block-device, USB-ancestry, filesystem, mountpoint, and free-space data
- Trigger source and capture ID, or explicit proof that capture was blocked
- Relevant application/service and kernel storage logs with timestamps
- Before/after directory listings proving publication or non-publication
- Manifest and byte-validation output for every successful baseline/recovery set
- A touchscreen photograph or video for each distinct visible error class
- Explicit proof that no application capture artifact appeared on the boot filesystem
- Recovery steps, filesystem-repair result, and any limitation or unexpected behavior

Summarize the completed run in a dated Markdown record under
`docs/evidence/milestone-2/`. Raw exploratory logs that are not needed to
support a qualifying claim should remain untracked.

## Milestone Exit Gate

Milestone 2 is complete only when all five checkpoints pass on the Raspberry Pi
hardware and the evidence shows:

- Normal, restart, idle unplug/replug, automatic remount, and reboot persistence work.
- Missing, full, read-only, corrupt/unmountable, and mid-write removal fail safely and visibly.
- No fault path stores user media on the protected boot microSD.
- Failed staging never publishes a capture directory or leaves a valid-looking partial artifact.
- The service and UI recover to a successful byte-validated capture after every fault class.
- Multiple-drive selection is deterministic and accurately recorded in manifests.
- `ROADMAP.md`, `PROJECT_CONTEXT.md`, `CURRENT_SESSION.md`, `README.md`, and the
  evidence index are updated with the demonstrated result and any remaining limitation.

After this gate closes, the next ordered work is aggregate electrical power
measurement and Milestone 3 battery/safe-power design.
