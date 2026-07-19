# Milestone 6 Plan - Synchronized Settings and Control UI

Status: planned after Milestone 5 live preview

## Outcome

Replace the disabled Settings placeholders with a coherent 800x480 control
system for the complete four-camera product. Ordinary controls apply one
validated photographic profile to all four OV3660 nodes, report per-node
acknowledgement and readback, persist on the Raspberry Pi, and are recorded in
every capture manifest. Individual-node adjustment is limited to a protected
calibration/service workflow.

This milestone defines the settings and information architecture. It does not
make every low-level ESP32 camera-driver option a user feature, does not add a
battery UI, and does not claim that AI interpolation, network sharing, display
backlight control, audio, or operating-system updates exist before their
supporting hardware and software are implemented and validated.

## Current Baseline

The current Settings route contains disabled cards for Exposure, White Balance,
Smooth Motion, and AI Interpolation. Its only operative maintenance action is
the idle-only `RECONNECT CAMERAS` recovery.

Firmware 0.2.3 currently fixes the four nodes to:

- 2048x1536 QXGA JPEG, driver quality 8
- Automatic exposure, advanced automatic exposure, automatic gain, and a 4x
  gain ceiling
- Automatic white balance and automatic white-balance gain
- Brightness 0, contrast +1, saturation 0, sharpness +1, and denoise enabled
- Bad-pixel correction, white-pixel correction, and raw gamma enabled
- Four warm-up frames after a 700 ms light-settle delay

The Pi currently fixes GIF frame duration to 150 ms and maximum GIF width to
800 pixels. Camera settings have no Pi-to-node command protocol, capability
report, acknowledgement, readback, or capture-manifest snapshot.

## Product-Control Principles

1. Normal photographic controls apply to all cameras together. Independent
   automatic metering is not accepted as synchronized appearance.
2. The UI presents photographic concepts and tested presets, not raw register
   numbers or implementation details.
3. Unsupported controls remain hidden rather than disabled with an implication
   that they work.
4. Settings cannot change during capture, transfer, publication, or recovery.
5. A setting is shown as applied only after all expected nodes acknowledge it
   and return the effective value.
6. Partial application produces a prominent unsynchronized warning and blocks
   normal capture until the user restores a common validated profile or enters
   an explicitly designed degraded mode.
7. The validated current firmware profile is always available as Factory
   Defaults.
8. Every capture manifest records the requested profile, effective per-camera
   values, firmware versions, and any synchronization exception.
9. Destructive, identity, timing, transport, and hardware controls are
   separated from ordinary photography settings.
10. Touch controls use large targets and progressive disclosure appropriate to
    the native 800x480 display.

## User-Facing Settings Inventory

### Camera

Initial release candidates:

- Camera preset: Auto, Daylight, Indoor LED, Low Light, and Custom
- Exposure mode: Auto or Manual
- Exposure compensation: -2 through +2
- Manual exposure value, shown only in Manual after sensor units are calibrated
  to a truthful user-facing scale
- Gain mode: Auto or Manual
- Maximum automatic gain: validated subset of 2x, 4x, 8x, and 16x
- White balance: Auto, Sunny, Cloudy, Office/Fluorescent, and
  Home/Incandescent
- Brightness, contrast, saturation, and sharpness: -2 through +2
- Denoise: Low, Normal, and High mapped to validated sensor/processing profiles
- Resolution: validated subset beginning with 2048x1536, 1600x1200, and
  1280x720
- Image quality: Best, Balanced, and Fast/Small, mapped to tested JPEG values
- Orientation: Normal, Mirror, Flip, and Rotate 180 degrees
- Composition overlay: Off, thirds grid, and center crosshair
- Reset all camera settings to the validated factory profile

The first implementation should prioritize presets, exposure compensation,
white balance, brightness/contrast/saturation, resolution/quality, and reset.
Manual exposure/gain follows only after the units and cross-camera behavior are
measured.

### Multi-Camera Synchronization and Calibration

- Synchronized settings state for all four cameras
- Exposure and white-balance lock across the array
- Reference camera selection
- Per-camera exposure, white-balance/color, brightness, contrast, and
  saturation trims
- Per-camera orientation
- Logical left-to-right Camera 1-4 order and stable UID display
- Camera enable/disable for diagnosis
- Alignment/calibration overlay and test capture
- Restore all calibration trims

These controls live in a protected Calibration area. Logical order, identity,
and individual disable actions require confirmation because errors change the
result geometry or can silently create partial captures.

### Capture

- Shutter delay: Off, 2, 5, or 10 seconds
- On-screen countdown
- Post-capture review enabled and review duration
- Partial-capture policy: create best available result, preserve originals
  only, or reject an incomplete set
- Keep original JPEGs
- Create animation
- Capture/session naming prefix
- User-facing retry behavior after a failed camera, once a bounded policy is
  validated

The physical shutter remains an independent primary input. Trigger pulse width,
association windows, warm-up frames, rearm timing, and transfer slots are not
ordinary capture settings.

### Animation and Processing

- Playback pattern: forward-and-back, forward only, or reverse only
- Animation speed: Slow, Normal, Fast, or Custom frame duration
- Optional endpoint hold
- Loop behavior
- Output width/size and GIF quality/optimization
- View alignment and automatic crop, when implemented
- Exposure/color matching, when implemented
- Motion smoothing level, explicitly separated from alignment
- AI interpolation: Off, 2x, or 4x only after a real implementation exists
- Preserve processed intermediate frames
- Output format selection only for formats the product can actually generate
- Regenerate an existing capture from its Library actions

The current `SMOOTH MOTION` placeholder must be decomposed into alignment,
appearance matching, and frame interpolation because they have different
effects, costs, and failure modes.

### Live Preview and Capture-Screen Preferences

After Milestone 5 provides a real preview transport:

- Preview source: reference camera, Camera 1-4, or four-camera grid
- Preview responsiveness/quality profile
- Grid and center overlays
- Capture/readiness/status overlays
- Remaining removable-storage capacity
- Screen-awake behavior while previewing
- Highlight clipping warning or preview zoom only if truthfully supported

Preview-only brightness or zoom must not silently alter captured output.

### Storage and Library

- Selected removable USB drive and connected/read-only/unavailable state
- Used and available capacity plus an estimated remaining-capture count
- Friendly capture/session naming
- Library sort order, thumbnail density, and complete/partial filtering
- Whole-set delete confirmation
- Cleanup views for oldest, largest, partial, or failed sets
- Safely eject USB, rescan storage, and repair/rescan the media catalog
- Export selection when an export destination/workflow exists
- Preserve-originals policy

The protected Pi boot card is never offered as media storage. Formatting media
or automatic deletion, if ever implemented, is a separately confirmed
technician/destructive action.

### Display and Controls

- Screen brightness only if controllable backlight hardware is verified
- Idle dim/screen timeout, wake on touch, and wake on shutter
- Text size and high-contrast mode
- Touch feedback and interface sound only when supporting hardware exists
- Left-handed primary-control layout
- Language and date/time format
- Destructive-action confirmations and resettable help hints

The accepted external battery pack provides its own percentage display. No
battery state, gauge, charging, or reserved battery region is added here.

### System

- Device name, date, time, and time zone
- Application, firmware, sensor, rig, and camera-identity information
- Camera and removable-storage health overview
- Reconnect cameras and rescan USB storage
- Export diagnostic report and recent user-relevant errors
- Restart application, restart device, and safe shutdown only after the soft
  lifecycle is validated
- Reset user settings and a separately confirmed factory reset
- Signed update/check/rollback controls only after a safe update mechanism
  exists

### Network and Sharing - Later and Hidden Until Implemented

- Hotspot on/off, name, password, QR code, and connected clients
- Device-hosted media download
- Explicit permissions for remote shutter and remote settings
- Hotspot inactivity timeout
- Joining/forgetting Wi-Fi networks and device naming

No network page or availability claim appears until the later onboard-polish
gate is satisfied.

## Settings Information Architecture

The Settings home uses six large tiles in a 2x3 grid:

1. Camera
2. Capture & Animation
3. Cameras
4. Storage
5. Display & Controls
6. System

`About & Diagnostics` is a footer action. `Network & Sharing` is absent until
operative. The Settings home should not retain the current large static preview
surface; preview is useful inside controls whose effects can be inspected.

### Page Behavior

- **Camera:** preview at left when available; preset, exposure, and white
  balance summaries at right; More, Reset, and Apply actions along the bottom.
- **Detailed setting:** one setting or tightly related group per screen, with a
  large value, wide slider or three-to-five choices, explanation, reset,
  cancel, and apply.
- **Capture & Animation:** three summary rows for Capture, Playback, and
  Processing, each opening a focused subpage.
- **Cameras:** four equal cards showing logical number, position, connection,
  firmware/profile state, and last-capture result; Sync/Test/Reconnect actions;
  Calibration behind a protected entry.
- **Storage:** existing capacity visualization plus Open Library, Safely Eject,
  Rescan, and Cleanup.
- **System:** ordinary information and maintenance separated visually from
  restart, reset, update, and other consequential actions.

Edits may preview immediately where safe, but persistent application uses an
explicit Apply transaction. The UI always states `Applied to all 4 cameras`,
`Pending`, or identifies the cameras that rejected the change.

## Checkpoint 1 - Settings Contract and Validated Profiles

1. Measure which ESP32 driver controls and ranges work on all four installed
   OV3660 nodes.
2. Define stable setting identifiers, units, allowed values, defaults, and
   dependencies.
3. Define Factory, Auto, Daylight, Indoor LED, and Low Light profiles from
   physical image evidence rather than names alone.
4. Decide which settings require camera restart, warm-up, or preview refresh.
5. Specify settings schema versioning and backward compatibility.

Exit gate: a reviewed contract lists every initially exposed setting, effective
range, default, capability rule, persistence rule, and evidence procedure.

## Checkpoint 2 - Bidirectional Node Protocol

1. Add node capability/status reporting.
2. Add set-profile and read-effective-settings messages without weakening the
   existing BTC1 capture transaction boundaries.
3. Apply settings only while idle and return per-field success or failure.
4. Add Pi broadcast coordination, bounded acknowledgement, readback, rollback,
   and unsynchronized-state handling.
5. Keep the current validated profile available after protocol or persistence
   failure.

Exit gate: repeated settings transactions across all four powered nodes either
finish with identical verified state or produce a bounded, camera-specific
failure without beginning a capture.

## Checkpoint 3 - Persistence and Capture Evidence

1. Persist user profiles and the selected profile atomically on the Pi.
2. Establish intentional boot behavior; nodes must not silently retain a state
   that disagrees with the Pi.
3. Record requested and effective per-camera settings in every manifest.
4. Handle old manifests and firmware versions without inventing settings data.
5. Add reset/migration tests and recovery from corrupt settings data.

Exit gate: cold boot, node reconnect, application restart, and profile reset
all return a known synchronized state, and new manifests prove the effective
capture configuration.

## Checkpoint 4 - Native 800x480 UI

1. Implement the Settings home hierarchy and focused control pages.
2. Preserve large Home/navigation targets and the idle-only camera recovery.
3. Hide unavailable future features rather than presenting false controls.
4. Add pending, applied, failed, unsynchronized, reset, and confirmation states.
5. Validate layout at native 800x480 with long values and error text.

Exit gate: production QML and interaction tests cover every route and state
without warnings, clipped controls, accidental capture commands, or unsupported
capability claims.

## Checkpoint 5 - Four-Camera Image and Recovery Qualification

For every initially shipped setting/profile:

1. Apply it to all four cameras and verify readback.
2. Capture a controlled daylight/bright scene and an indoor LED scene.
3. Record image dimensions, JPEG integrity/size, timing, and effective settings.
4. Compare exposure, white balance, color, and orientation across cameras.
5. Exercise one node disconnect/reconnect, one rejected setting, application
   restart, cold boot, Factory Defaults, and a normal capture afterward.
6. Confirm no setting violates removable-media fail-closed behavior or the
   shared-trigger safety contract.

Exit gate: every exposed control has physical four-node evidence, profiles have
accepted cross-camera output, recovery returns to a synchronized state, and no
ordinary setting can expose an unvalidated low-level configuration.

## Deferred or Technician-Only Controls

Keep the following outside ordinary UI: pixel format, XCLK, PSRAM/DMA and frame
buffer configuration, USB chunk/buffer sizes, GPIO assignments, protocol
version, raw sensor registers, transport slots, trigger pulse width, capture
association/no-progress windows, automatic rearm, serial baud/timeouts, and
arbitrary storage paths. Color-bar, lens/pixel correction, gamma, downsize/crop
internals, log level, UID mapping, and per-node disable belong only in bounded
diagnostic or calibration workflows.

## Evidence to Retain

- Settings contract and schema fixtures
- Firmware/application versions and exact profile payloads
- Four-node capability, acknowledgement, and readback logs
- Native 800x480 renders and interaction results
- Controlled-scene originals and comparison summaries
- Manifests proving effective settings
- Restart, cold-boot, reconnect, partial-application, reset, and recovery logs
- Known limitations and controls removed or narrowed after testing
