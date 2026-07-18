# Milestone 2 Focused Retest and Product FAT Repair - 2026-07-18

Status: pass; Milestone 2 exit blockers resolved

## Implementation and Automated Tests

- Final tested revision: `8fd1f17a774b2b093971b817a36d97aca0f6a806`
- Raspberry Pi application version: `0.2.1`
- The Tk event drain now catches a failed presentation without terminating the
  recurring poll callback. Review frames are detached from removable media
  after loading, and display-metric persistence tolerates later removal.
- Missing, full, read-only, unmountable, and I/O-error details are reduced to
  bounded actionable messages while full diagnostics remain in the service
  journal. The 800x480 label uses centered wrapping and a 24-point font.
- Camera disconnects now render as a bounded logical-camera message while the
  port exception remains in the journal.
- USB roots remove only capture staging directories that exactly match
  `.YYYYMMDDTHHMMSSZ_XXXXXXXX.part` and are at least 3600 seconds old. Fresh
  staging, files, symlinks, and unrelated `.part` names are not removed.
- Local and Raspberry Pi deterministic runs each passed 73 tests before the
  camera-message iteration and 74 afterward. One environment-gated live
  evidence test was skipped in each deterministic invocation. Repository
  formatting, lint, hygiene, and pre-push tests passed.

## Backup and FAT Repair

Before repair, the complete product USB contents were copied to the ignored
local maintenance directory
`.maintenance-backups/product-usb-before-fat-repair-20260718/`. The copy
contains 1,224 source files totaling 947,483,006 bytes. Relative-path SHA-256
comparison found zero missing files, zero extra files, and zero hash
mismatches. The backup also contains the first 32 filesystem sectors and the
partition-table dump; their SHA-256 values are respectively
`241302f87da481b22322bb447b763d1df0df19eabd557d055e59586ed9e26f9d`
and
`b79e42fffb0bb2a1d97a501553e285f0b0c763f3b5afd6efe202f806d33eae20`.

The repair target was re-resolved immediately before the operation as USB
serial `900049666ACEB315`, UUID `B67C-53C4`; it was `/dev/sdb1` at repair time.
The service was stopped, GPIO17 remained LOW, and the filesystem was unmounted.
The read-only pre-check returned 1, reported the dirty bit and the known
primary/backup boot-sector difference at offset 65 (`01/00`). `fsck.vfat -a -v`
removed the dirty state and wrote the changes. The immediate offline read-only
post-check returned 0 with no boot-sector difference and no filesystem error.

After the final recovery capture, the product partition had enumerated as
`/dev/sda1`. A second cleanly unmounted `fsck.vfat -n -v` returned 0, confirming
that the repaired filesystem remained clean through a real application write.

## Focused Hardware/UI Retest

The production Tk `<Button-1>` binding was exercised through one injected
Xwayland pointer click per action; normal capture still used one GPIO17 pulse.

1. Production capture `20260718T174008Z_177d0b5c` produced and displayed a
   complete app-0.2.1 four-camera review on the repaired product drive.
2. Both storage interfaces were cleanly unmounted and serial-verified before
   deterministic USB-storage unbinding. A touchscreen action with no writable
   USB drive stayed before the trigger boundary: the service remained active,
   GPIO17 stayed LOW, and the complete three-line error is visible in
   [`focused-retest-missing-media-ui-2026-07-18.png`](focused-retest-missing-media-ui-2026-07-18.png).
3. With the reviewed product path absent, a resolved Camera 1 CDC disconnect
   emitted the real follow-up UI event. The journal recorded the caught
   `FileNotFoundError` for
   `20260718T174008Z_177d0b5c/bullet_time.gif` at 13:45:23. The same service PID
   remained active and processed the subsequent camera event, proving that the
   polling callback survived without a service restart.
4. The follow-up camera diagnostic was compacted and redeployed. Its real
   800x480 result is retained in
   [`focused-retest-camera-disconnect-ui-2026-07-18.png`](focused-retest-camera-disconnect-ui-2026-07-18.png).
5. Final actual-UI recovery capture `20260718T175104Z_04b69c0b` passed the
   repository byte validator with Cameras 1-4 successful, five recorded files,
   GIF order `[1, 2, 3, 4, 3, 2]`, app version `0.2.1`, and product-drive storage
   metadata. See
   [`focused-retest-final-20260718T175104Z_04b69c0b-manifest.json`](focused-retest-final-20260718T175104Z_04b69c0b-manifest.json)
   and
   [`focused-retest-final-recovery-ui-2026-07-18.png`](focused-retest-final-recovery-ui-2026-07-18.png).

The previously stale
`.20260718T015549Z_273b2de6.part` directory was removed automatically at the
first eligible product-root resolution, with the exact removal retained in the
service journal.

## Final State and Exit Decision

- `bullet-time-ui.service`: active on revision `8fd1f17`
- GPIO17: output LOW
- Camera identities: all four stable `/dev/serial/by-id` links present
- Product drive: serial `900049666ACEB315`, UUID `B67C-53C4`, mounted writable
  at `/media/username/USB DISK`
- Expendable drive: serial `900048D90E707A22`, clean 64 MiB `M2TEST`, attached
  and unmounted
- Final capture: `20260718T175104Z_04b69c0b`, complete and byte-valid
- Product FAT: clean offline check after the final capture

The remaining distinction is unchanged: active-write loss was produced by
serial-verified USB-interface unbinding, not a literal cable yank. That is
retained as a test-method limitation, not an unsatisfied Milestone 2 gate.
Milestone 2 is complete. The next ordered work is instrumented aggregate power
measurement before battery and safe-power hardware selection.
