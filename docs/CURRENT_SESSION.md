# Current Session - Milestone 2 Removable-Media Qualification

Status reviewed: July 18, 2026

## Verified State

- All five Milestone 2 hardware scenario families have been exercised over SSH
  on the live four-camera Raspberry Pi rig. Fail-closed behavior, atomic
  non-publication, no boot-card fallback, recovery after each isolated fault,
  and preferred/fallback/deterministic two-drive selection passed.
- The deterministic suite passed locally, and the environment-gated physical
  four-node E2E test passed on the Pi when supplied its existing evidence ledger.
- Final actual-UI product capture `20260718T163525Z_3a578613` passed byte
  validation for Cameras 1-4 and recorded the correct product USB destination.
- The product drive, serial `900049666ACEB315`, is mounted at
  `/media/username/USB DISK`. `bullet-time-ui.service` is active and GPIO17 is
  output LOW.
- The expendable drive, serial `900048D90E707A22`, was intentionally erased and
  repartitioned as a clean 64 MiB FAT32 `M2TEST` volume. It is currently
  unmounted.

## Immediate Work

Milestone 2 stays active because qualification found real exit blockers:

1. Make UI polling tolerate disappearance of the currently reviewed GIF. The
   existing process and receiver survive removal, but the Tk polling callback
   dies and screen updates require a service restart.
2. Wrap or otherwise fit storage failures within the 800x480 display. Missing,
   full, read-only, corrupt, and mid-write errors are substantially clipped.
3. Back up the product USB media, then repair its dirty FAT and reconcile the
   one-byte primary/backup boot-sector difference. No repair was performed in
   the qualification session.
4. Remove or deliberately retain the pre-existing uncommitted
   `.20260718T015549Z_273b2de6.part` directory and define startup cleanup for
   stale staging.
5. Rerun the focused removal/error-display checks and one final recovery
   capture. A literal cable-yank during write is optional corroboration; the
   completed fault used deterministic removal of the serial-verified
   USB-storage interface while staging was active.

The full result, screenshots, manifests, filesystem evidence, and capture IDs
are in
[`evidence/milestone-2/removable-media-qualification-2026-07-18.md`](evidence/milestone-2/removable-media-qualification-2026-07-18.md).
After Milestone 2 closes, measure aggregate electrical power before choosing
battery, charging, regulation, monitoring, or safe-power-cut hardware.
