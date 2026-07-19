# Bullet-Time Camera Rig Roadmap

This roadmap reflects product decisions and capture/trigger/product-boot hardware evidence through July 18, 2026. The remaining version 1 budget is approximately $200, so purchases should be tied to a demonstrated milestone and reused in the integrated device whenever practical.

The project has no fixed completion date. Milestones advance when their exit criteria are satisfied.

## Milestone 0 - Four-Camera Capture Subsystem

Status: complete prototype

- Four XIAO ESP32S3 Sense camera nodes
- Four OV3660 sensors
- Four 16 GB node microSD cards
- Shared physical shutter button
- Individual status LEDs
- Common firmware on all four nodes
- Successful 2048x1536 JPEG capture to each node card

The node microSD cards and GPIO-driven status LEDs are historical prototype features. Firmware 0.2.0 removes their behavior from the camera nodes and passed revised four-node startup verification on July 17; this does not invalidate the completed prototype evidence.

## Milestone 1 - Bench-Top End-to-End Capture

Status: complete July 18, 2026; the soft two-second review target remains an optimization item

Goal: use bench/USB power to prove the entire software and data path before investing in the battery system or enclosure.

The detailed checkpoint plan, cost gates, tests, and exit criteria are in [`MILESTONE_1_PLAN.md`](MILESTONE_1_PLAN.md).

End-to-end path after the approved trigger/node simplification:

1. The physical shutter or Raspberry Pi BCM GPIO17 through the 2N3904 open-collector circuit triggers the four camera nodes on their shared `D1 / GPIO2` bus.
2. Each node provides its captured JPEG to the Raspberry Pi.
3. The Pi groups received images into one capture set.
4. The Pi preserves every received original.
5. The Pi creates the raw-image back-and-forth GIF.
6. The touchscreen shows a loading state during capture and transfer.
7. The touchscreen shows the completed animation until the next capture.
8. Missing nodes produce a camera-specific error without discarding successful images.

Work:

- Camera-node simplification is implemented, flashed, startup-verified, and functionally capture-tested on all four nodes.
- Raspberry Pi BCM GPIO17 hardware-trigger output is installed and fake/hardware tested with boot-safe LOW idle, one 100 ms HIGH pulse per action, and LOW cleanup. The service is active and idles output LOW.
- Use USB `CAPTURE_STARTED` as the Pi notification path for both physical and Pi-initiated captures; do not add a direct trigger-sense GPIO.
- Identify and configure the available touchscreen.
- Establish Raspberry Pi OS and application development environment.
- Assign stable logical camera numbers.
- Define a transport-independent capture and image-transfer protocol.
- Prototype direct JPEG transfer from one ESP32S3 frame buffer.
- Use USB as the selected V1 transport; defer Wi-Fi unless USB exposes a concrete blocker.
- Use the product owner's installed final V1 USB hub/cabling chain; its four concurrent camera links are enumerated and have passed the recorded repeated transfer tests. The later aggregate-power gate was retired by the July 18 product-owner decision.
- Integrate the validated concurrent four-node transfers into the product coordinator and capture-set workflow.
- Implement capture-set grouping, partial-set handling, and diagnostics.
- Preserve originals and generate the version 1 GIF.
- Implement the loading/result/error display states.
- Configure the accepted product boot path: no visible OS content during early boot, then the product logo handing directly to the full-screen application, with no desktop, console, cursor, or boot diagnostics.
- Measure normal shutter-to-review time against the soft two-second target.

Intermediary checkpoints:

1. **Absorbed/retired as a separate gate:** Pi and touchscreen bring-up; required behavior was validated by the later integrated checkpoints
2. **Absorbed/retired as a separate gate:** Offline GIF/UI vertical slice; required complete/partial GIF and UI behavior passed in Checkpoints 5-7
3. **Absorbed/retired as a separate gate:** One-node direct USB JPEG transfer; required transport, integrity, reconnect, and timing behavior passed in Checkpoint 4 and later regressions
4. **Complete:** one-node full-system bench test through the powered USB hub, including capture, direct transfer, preservation, representative processing, touchscreen display, stage analytics, and the electrical inspection
5. **Complete:** Four-node capture grouping and partial-failure handling
6. **Complete:** Integrated live GIF/touchscreen flow
7. **Complete:** Performance and reliability pass, with the measured latency limitation retained

By product-owner decision on July 10, 2026, work fast-forwarded to Checkpoint 4.
At Milestone 1 close, Checkpoints 1-3 were retired as standalone gates rather
than represented as independently completed. Their required product behavior
was absorbed and accepted by Checkpoints 4-7; their original proposals remain
in `MILESTONE_1_PLAN.md` as historical planning context.

Checkpoint 4 demonstrated the temporary diagnostic USB-request path, a clean 20-capture instrumented run, reconnect/error/NACK recovery, and the normal physical/Pi hardware-trigger-to-touchscreen paths. On July 17, simplified firmware was compiled, hash-verified, flashed, and startup-smoked on all four nodes. One physical press and one normal Pi pulse each produced exactly one Camera 1 atomic-commit/display workflow. Separate four-port observers showed one physical press, one GPIO17 pulse, and 10 repeated GPIO17 cycles produced 48/48 valid four-node captures in total with zero errors or duplicates; repeated pulse-to-all-completions was 2.455 seconds median and maximum start spread was 4.930 ms. The product owner subsequently completed the prescribed unpowered multimeter checklist and reported all checks passing, closing Checkpoint 4. After the repository/module refactor at `b950740`, all four nodes were reflashed and startup-verified, another 10-cycle/40-image physical-rig regression passed without errors or duplicates, and the pulled Pi application completed CRC-valid removable-USB captures before and after a verified reboot. The renamed service and all 33 automated boot gates passed after that reboot.

On July 18, the integrated concurrent receiver, capture coordinator, atomic four-image persistence, ordered GIF pipeline, and camera-specific partial review passed the physical-rig acceptance contract. The qualifying run produced 25/25 complete sets, 100 originals, 25 six-frame GIFs, no failed normal transactions, and no leftover partial files. Separate scenarios passed for every camera unavailable, one checksum-corrupt transfer plus recovery, one controlled mid-payload truncation plus recovery, Camera 4 reboot identity, physical shutter, normal touchscreen/GPIO17 capture, and complete/partial touchscreen review. The byte validator passed 35 named capture sets and the environment-gated hardware test passed. Capture-set completion was 3.250 seconds median and 3.289 seconds maximum, so the soft two-second target was not met and remains a known optimization rather than a hidden exit-gate claim. Full evidence is in `docs/evidence/milestone-1/checkpoint-5/checkpoint5-four-node-e2e-2026-07-18.md`.

Exit criteria:

- Repeated button presses complete the path from four nodes to touchscreen.
- Original JPEGs and the GIF are preserved for every successful capture.
- Incomplete capture sets remain usable and report the failed camera.
- Normal latency is measured and the gap from the soft two-second target is explicitly retained.

## Milestone 2 - User-Removable USB Media

Status: complete July 18, 2026

The detailed real-drive procedures, safety boundaries, evidence requirements,
and exit gates are in [`MILESTONE_2_PLAN.md`](MILESTONE_2_PLAN.md).

- Use the USB drive added by the product owner rather than a separate removable-card reader.
- Keep Raspberry Pi microSD boot storage protected and internal, with no media fallback to it.
- Automatically detect writable USB-backed mounted filesystems and request mounting through `udisks2` when needed.
- Store capture sets below `BulletTime/` on the selected USB drive and record the filesystem selection in each manifest.
- Validate actual JPEG and GIF writes, restart behavior, unplug/replug, and deterministic selection when more than one USB drive is present.
- Handle missing, full, corrupt, read-only, and prematurely removed USB drives safely and visibly.

Bring-up evidence on July 17-18, 2026 established user-service mounting,
writable product-media capture, reboot persistence, and the full four-camera
application path. The July 18 qualification then executed all five hardware
checkpoint families: idle physical unplug/reinsert and automatic remount;
missing media through UI and shared-trigger paths; isolated full, read-only,
and unmountable expendable media; deterministic removal of the expendable
USB-storage interface during active staging; and preferred, fallback, restart,
and no-preference two-drive selection. Every isolated fault avoided boot-card
fallback and valid-looking partial publication, then recovered to a byte-valid
four-camera capture. The final product capture was
`20260718T163525Z_3a578613`; the environment-gated four-node E2E test also
passed with its evidence ledger.

The focused follow-up deployed app 0.2.1, made Tk event polling survive removal
of the reviewed GIF, fit storage errors within 800x480, added guarded cleanup
for expired capture staging, backed up all 1,224 product-drive files with zero
SHA-256 mismatches, and repaired the dirty product FAT. A clean offline FAT
check passed again after final actual-UI capture
`20260718T175104Z_04b69c0b`, which byte-validated all four cameras and the
ordered GIF. The active-write test method remains a serial-verified kernel
USB-storage unbind rather than a literal cable yank. See
`docs/evidence/milestone-2/focused-retest-and-fat-repair-2026-07-18.md`.

## Milestone 3 - Integrated Battery and Safe Power

Status: closed July 18, 2026 by product-owner acceptance of the external power arrangement; planned aggregate measurement was not executed

The measurement and integration checkpoints are in
[`MILESTONE_3_PLAN.md`](MILESTONE_3_PLAN.md).

- Use the selected external battery pack's separate rated 5 V / 2 A outputs for
  the Raspberry Pi and powered USB hub.
- Use the battery pack's own percentage display as the V1 charge indication.
- Retire aggregate measurement, internal battery/charging integration, and
  automatic low-battery shutdown as V1 gates.
- Do not claim actual current, runtime, regulation margin, or coordinated
  shutdown as independently measured or demonstrated.

This supersedes the earlier internal-battery direction for V1. The original
measurement and safe-power checkpoints remain in `MILESTONE_3_PLAN.md` as
historical planning context.

## Completed UI Platform Track - Qt Touchscreen

Status: complete July 18, 2026

- Replace the Tk runtime with native Qt Quick/QML and a PySide6 bridge while
  preserving the receiver, GPIO17 trigger, atomic media pipeline, and headless
  operation.
- Implement seven native 800x480 routes derived from the approved UX
  explorations: ready, progress, partial review, static preview placeholder,
  four-camera controls, removable-media library, and detached viewer.
- Keep the preview demonstrably static and logo-based. Do not add live camera
  transport, Qt Multimedia, battery UI/state, network claims, rename/edit/share
  operations, or operative camera-setting commands.
- Deploy through commit, push, and fast-forward Pi pull; validate native
  Wayland boot, route rendering, capture, removable-media browsing, GPIO17 idle
  safety, camera identity, and service recovery.

Physical-Pi runtime validation passed at `fb1d1e7`: 112 deterministic tests
passed with one expected live-evidence skip, a complete four-camera UI capture
was published, and the 214-entry product library loaded in 0.527 seconds after
bounded eager thumbnail decoding. The seven 800x480 route artifacts were
rendered without QML warnings across their recorded `d502fff` and `828831b`
commits; the final library optimization was validated separately rather than
misattributed to those renders. A human-operated touch-feel observation remains
useful enclosure UX feedback, but is not represented as SSH evidence. The first
Qt soft reboot also failed to return and required a physical power cycle; with
no persistent journal, its cause and clean soft-reboot lifecycle remain open.
Details and route artifacts are in
[`evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md`](evidence/qt-touchscreen/qt-ui-deployment-2026-07-18.md).

On July 19, the product owner superseded the original read-only-library
boundary. App 0.2.2 adds confirmed deletion from both the library and detached
viewer. The operation is limited to a revalidated published capture-set
directory on the active removable USB root and removes its JPEG originals, GIF,
and manifest together. Rename, edit, share, and boot-card operations remain out
of scope. Final commit `3f99e76` passed the Pi's 118-test suite (one expected
live-evidence skip), native viewer/confirmation rendering, production-QML load,
and a disposable real-product-USB deletion check that retained all 222
pre-existing capture directories. See
[`library-deletion-2026-07-19.md`](evidence/qt-touchscreen/library-deletion-2026-07-19.md).

App 0.2.3 adds used and available capacity from the selected removable USB
filesystem to the media-library sidebar. Feature commit `81a2a49` and visual
correction `6398f3a` were each pushed and fast-forward pulled on the Pi. The
121-test Pi suite passed with only the expected live-evidence skip; the backend
matched `/dev/sdb1` byte-for-byte with `df`, and the corrected native 800x480
Wayland render passed without QML errors. See
[`storage-capacity-2026-07-19.md`](evidence/qt-touchscreen/storage-capacity-2026-07-19.md).

## Milestone 4 - Compact Version 1 Enclosure

Status: active July 18, 2026

The detailed layout, print, and acceptance checkpoints are in
[`MILESTONE_4_PLAN.md`](MILESTONE_4_PLAN.md).

- Arrange all final version 1 components.
- Model a reasonably compact box-shaped enclosure.
- Maintain the 4 cm sensor spacing and straight camera alignment.
- Provide openings for cameras, screen, shutter, the two external battery-pack
  leads, removable USB media, and other required access.
- 3D print and revise for fit.

Ergonomics, weight optimization, integrated lighting, tripod mounting, and weather resistance are later revisions.

## Milestone 5 - Fast Follow

- Add live preview.
- Improve ordinary user-facing status and recovery behavior.
- Refine the enclosure and controls based on use.

## Version 2 and Later

- Add synchronized user-adjustable camera settings.
- Align the viewpoints.
- Normalize exposure, color, and camera appearance.
- Add AI frame interpolation.
- Explore NeRF and 3D Gaussian Splatting.
- Scale the system toward 12 or more slightly curved camera nodes.
- After the onboard experience is polished, consider hotspot-based media access and remote controls.

## Budget Rule

Approximately $200 remains for version 1. The product owner has accepted the
existing external battery pack, so the earlier battery/charging purchase gate is
retired. Tie enclosure-specific and optional network purchases to demonstrated
requirements, reuse available hardware where reliable, and confirm compatibility
before buying each missing component.
