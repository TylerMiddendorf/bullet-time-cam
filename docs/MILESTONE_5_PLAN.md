# Milestone 5 Plan - Live Preview and Fast-Follow Reliability

Status: live-preview checkpoints complete July 19, 2026; Milestone 5 remains
active for status/recovery and latency follow-up

## Outcome

Replace the Capture screen's static demonstration surface with genuine, bounded
live frames from the four installed camera nodes without changing the validated
shared-trigger, concurrent still-capture, camera-identity, removable-storage, or
USB-recovery behavior.

## Non-Negotiable Invariants

- The physical shutter and Raspberry Pi GPIO17 continue to use the existing
  shared active-low hardware trigger and four-node still-photo workflow.
- Full-resolution still captures remain 2048x1536 JPEGs transferred concurrently
  under the existing BTC1 transaction, CRC, acknowledgement, grouping, and
  atomic removable-USB publication rules.
- Preview frames are never capture originals, never enter a capture set or
  manifest, and never touch removable USB storage.
- The existing stable eFuse UID remains the sole logical-camera identity.
- One `NodeSession` continues to own each serial stream. No preview component may
  open, read, or write a camera port independently.
- Preview is best-effort. A missing, late, corrupt, or disconnected preview must
  not fail a still capture or disconnect an otherwise usable node.
- Capture and camera-USB recovery take priority over preview.

## Selected Preview Architecture

The Pi polls for one low-resolution JPEG at a time through two additive BTC1
message types. It rotates requests through logical Cameras 1-4 while the Capture
route is visible and the capture workflow is idle. At most one preview request
is outstanding across the complete rig.

Each node remains in 320x240 preview mode while idle and labels each response with
its stable UID, boot ID, preview sequence, dimensions, byte count, and CRC. The
node checks the shared trigger during bounded preview acquisition and before
transmission. After a shared trigger it switches to 2048x1536, uses the existing
settle/warmup sequence, restores preview mode before transfer, and continues the
unchanged capture transaction. Preview payload size and host request cadence are
bounded so a shutter arriving during the short transmission window has a
bounded delay.

The existing receiver validates preview identity, dimensions, byte count, CRC,
and JPEG decodability. It publishes the newest validated frame only to in-memory
UI state. The Capture screen displays that genuine frame with its logical camera
number and preview health. It does not imply that the preview is synchronized or
that it is the full-resolution still image.

Before touchscreen capture, the UI leaves the Capture route and the receiver
stops issuing preview requests before pulsing GPIO17. Physical captures are
recognized from `CAPTURE_STARTED` exactly as before; receipt of any such frame
also suspends preview immediately. Preview remains suspended through capture,
publication, recovery, and reconnect activity.

## Checkpoint 1 - Protocol and Firmware

- Add bounded preview request and image message types without modifying existing
  capture message values or semantics.
- Add low-resolution preview acquisition with guaranteed restoration of the
  QXGA still-photo configuration.
- Check the shared trigger at preview preemption points.
- Add host-compilable policy tests and compile the complete firmware with OPI
  PSRAM enabled.

Exit gate: firmware tests and the pinned-FQBN build pass, and source inspection
shows the original capture entry point, message values, resolution, and transfer
path remain intact.

## Checkpoint 2 - Pi Preview Service

- Extend the existing serial-session owner to schedule one rotating request.
- Validate identity, request correlation, bounds, CRC, and JPEG content.
- Enforce route/idle/capture/recovery suspension and request timeouts.
- Publish frames only through bounded in-memory events; do not resolve or write
  removable storage for preview.
- Add deterministic tests for rotation, corruption, timeout, disconnect,
  capture priority, physical-capture preemption, and storage isolation.

Exit gate: deterministic tests pass and a headless Pi run receives genuine,
validated frames from each of the four registered physical nodes without
creating or changing a capture directory.

## Checkpoint 3 - Native 800x480 Display

- Keep the static placeholder until Checkpoint 2's physical four-node gate has
  passed.
- Then display the latest genuine preview in the Capture route with aspect-fit
  behavior, camera-number attribution, and bounded stale/unavailable states.
- Stop requesting frames whenever the route is not Capture.
- Preserve the existing Capture, Settings, and Back touch targets.

Exit gate: native Wayland rendering on the physical 800x480 display shows valid
frames from Cameras 1-4, contains no static/demo/live claim when no genuine frame
has arrived, and introduces no QML warnings or layout overflow.

## Checkpoint 4 - Regression and Hardware Qualification

- Reboot or restart into the normal product session and confirm all four stable
  logical identities.
- Exercise physical-shutter and touchscreen captures while preview is active.
- Validate all four original JPEGs, CRCs, manifest, preview artifact, GIF, and
  review presentation on removable USB media.
- Compare preview-active capture timings with the established 3.250-second
  median baseline. Record the samples; preview must not cause an unexplained or
  unbounded regression.
- Run camera USB recovery from Settings, wait for all four sessions, confirm
  preview resumes, and complete another valid four-camera capture.
- Run the full deterministic Pi suite and boot/session verifier.

Final exit gate: genuine preview works for all four cameras on the 800x480 Pi,
both shutter paths still produce valid concurrent four-camera sets, storage and
identity invariants hold, USB recovery passes, and concrete results are recorded
under `docs/evidence/`.

Result: passed. The full evidence, including the initial stale-buffer failure,
final firmware design, test counts, firmware hash, all-camera CRCs, native
screenshots, preview-active/no-preview timing comparison, USB recovery, and
post-recovery capture is in
[`evidence/milestone-5/live-preview-2026-07-19.md`](evidence/milestone-5/live-preview-2026-07-19.md).

## Follow-Up Work

After live preview closes, continue Milestone 5 with demonstrated status and
recovery gaps, the unexplained Qt soft-reboot failure, and bounded work toward
the soft two-second shutter-to-review target. Synchronized user-adjustable
settings remain Milestone 6.
