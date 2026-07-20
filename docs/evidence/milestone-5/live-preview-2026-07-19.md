# Milestone 5 Live Preview - 2026-07-19

## Outcome

App and firmware 0.3.0 add a genuine, rotating four-camera preview to the native
800x480 Capture screen. Preview uses bounded 320x240 JPEGs in memory only. The
validated 2048x1536 shared-trigger capture, concurrent transfer, stable camera
identity, atomic removable-USB storage, camera recovery, and normal boot session
remain functional.

Milestone 5 remains active for later status/reliability and latency work. The
live-preview implementation and its recorded hardware gates are complete.

## Git Checkpoints

- `3cb2d40` - live-preview plan and isolation gates
- `86708e8` - additive preemptible firmware protocol
- `21871ba` - rotating single-flight Pi receiver and smoke tool
- `5cc7fa0` - node preview diagnostics
- `1d092d1`, `3f37b40` - first stale-buffer correction and regression assertion
- `e3240a7` - final idle-QVGA/full-resolution-capture sensor behavior
- `b6a4ca0` - genuine preview display and Capture-route lifecycle
- `51645c0`, `15d3741` - structured QML diagnostics and final placeholder removal
- `12ccfb5`, `d44be87`, `96fd683`, `f548c3f` - bounded native/full-runtime
  validation modes and tests
- `ab8c357` - app 0.3.0 release version

Each implementation checkpoint was committed and pushed to `origin/main`; the
Pi checkout was updated only by `git pull --ff-only origin main`.

## Firmware Build and Four-Node Deployment

Pinned target: `esp32:esp32:XIAO_ESP32S3:PSRAM=opi`

- Program storage: 372,217 bytes (11%)
- Dynamic memory: 33,376 bytes (10%), leaving 294,304 bytes
- Final application image SHA-256:
  `771633ae5f9addcb51a5fe18b74a9a5b59e55468d5ca7cf42aefb3022110ffff`
- Deployment used the four stable `/dev/serial/by-id` ESP32 paths and standard
  non-erase application address `0x10000`.
- All four writes completed with esptool 5.3.1 hash verification.
- Bounded startup smoke passed camera-ready 2048x1536 JPEG, BTC1 v1 with the
  matching eFuse UID and firmware 0.3.0, and shared-trigger readiness on all
  four nodes.

The first physical preview attempt exposed unreliable stale buffers when the
sensor changed QVGA to QXGA and back for every requested frame. Node diagnostics
identified `PREVIEW_FRAME_INVALID` on the affected cameras. The final design
keeps each idle node in QVGA, changes to QXGA only after a shared trigger,
retains the existing settle/warmup sequence, restores QVGA before still-image
transfer, and bounds preview acquisition to three attempts with trigger checks.

## Genuine Four-Camera Preview

The memory-only smoke tool deliberately used a storage implementation that
always rejects access. Its final pre-UI gate received three validated frames
from each physical camera:

| Camera | Stable UID | Frames | JPEG size range |
| --- | --- | ---: | ---: |
| 1 | `E072A1F9B3E4` | 3 | 4,211-4,238 bytes |
| 2 | `E072A1F9A190` | 3 | 3,369-3,532 bytes |
| 3 | `E072A1F99CC0` | 3 | 3,607-3,621 bytes |
| 4 | `E072A1F99CF8` | 3 | 3,761-3,924 bytes |

Every frame was a decodable 320x240 JPEG with matching metadata CRC. The smoke
reported `status: passed` and `storage_access: disabled`.

## Native 800x480 Display

The Capture route harness passed on the Pi's native Wayland compositor with one
root object, a found `previewImage`, a frame swap, exact 800x480 dimensions, and
zero QML errors. The full product runtime then opened Capture, connected the
real receiver, rotated genuine frames, and exited through its bounded validation
timer without log output or QML errors.

- Genuine runtime screenshot:
  [`genuine-preview-ui-800x480.png`](genuine-preview-ui-800x480.png)
- Dimensions: 800x480
- SHA-256:
  `3f5630841b52f302ee30b65c457641803e12c27741b3292c90418c24288d0c6d`

The image visibly attributes Camera 4, reports 320x240 rotating views, and has
no static/demo/disconnected preview claim.

## Preview-Active Capture and Latency Isolation

The full native runtime displayed preview for six seconds and then invoked the
same `QtUiController.request_capture()` used by the Capture button. Controller
and receiver tests require `PREVIEW_STOP` to precede `CAPTURE`; GPIO17 then
pulsed the existing open-collector shared trigger.

Capture `20260720T004727Z_c062657b` produced:

- status `complete`, schema 2, trigger source `pi_gpio17`
- the four expected stable UIDs and four CRC-valid originals
- `library_preview.jpg`, the ordered six-frame GIF, and the manifest on
  removable USB `/dev/sda1`
- complete-set time 3,720.677 ms
- original sizes 537,612-602,340 bytes
- no camera errors

The same firmware and scene, with preview disabled, produced capture
`20260720T004936Z_61985892` in 3,690.973 ms. The preview-active difference was
29.704 ms (0.8%) for this controlled pair. This supports preview isolation; it
does not replace the earlier 25-cycle latency qualification. Both are above the
soft two-second product target, and the preview-active display callback was
11,523.679 ms because this large-image GIF took substantially longer to build
and present. That broader processing latency remains open Milestone 5 work.

The progress screenshot was taken while all four cameras were complete and the
animation was building:

- [`preview-active-capture-progress-800x480.png`](preview-active-capture-progress-800x480.png)
- SHA-256:
  `1623f5cd92aefc467e12d9e161c7bb2f0a30651339d87478f698d9d25df847d7`
- Retained manifest:
  [`preview-active-capture-manifest.json`](preview-active-capture-manifest.json)

## USB Recovery and Post-Recovery Regression

The installed narrow recovery entry point reset the validated Pi xHCI
controller. The normal UI returned active under a new PID with `NRestarts=0`,
all four stable serial paths returned, and GPIO17 was output LOW.

A subsequent storage-disabled smoke received two new CRC-valid preview frames
from every camera. Post-recovery capture `20260720T005232Z_54ad4ce8` then passed
with app 0.3.0, four originals, preview artifact, GIF, no errors, and a
3,614.896 ms complete-set time. Its retained manifest is
[`post-recovery-capture-manifest.json`](post-recovery-capture-manifest.json).

Finally, the normal product service returned active at PID 9957 with
`NRestarts=0`; all 39 boot/session checks passed, native Wayland remained in
use without Xwayland, and GPIO17 remained output LOW.

## Automated Tests

- Final Windows deterministic suite: 137 passed, one expected live-evidence
  skip.
- Final Pi deterministic suite before release: 136 passed, one expected skip;
  the additional app-version checkpoint brings the source suite to 137 tests.
- UX contract: seven routes, zero errors.
- Native Capture-route QML smoke: PASS, 800x480, zero errors.

## Remaining Work

- Continue investigating large-image GIF/display latency and the soft two-second
  target.
- Continue the previously open Qt soft-reboot investigation.
- Physical enclosure acceptance remains deferred and open under Milestone 4.
