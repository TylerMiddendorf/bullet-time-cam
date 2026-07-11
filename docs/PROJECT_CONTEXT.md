# Bullet-Time Camera Rig - Project Context

This file is the durable project brief. Update it as product decisions are made so future work can begin from the actual system goal rather than treating the ESP32 camera-node firmware as the entire project.

## Product Goal

Build a production-like, complete bullet-time camera rig that is handheld and fairly compact. The first complete product uses four cameras. The longer-term ideal is an architecture that can scale to 12 or more cameras.

The finished device is intended to:

1. Initially use four cameras positioned to capture the subject from four viewpoints.
2. Give each camera its own Seeed Studio XIAO ESP32S3 Sense computer.
3. Use a central computer to coordinate capture, collect all four images, clean up and improve image quality, and turn the result into an animated GIF that moves through the viewpoints.
4. Provide an integrated screen where the user can adjust camera settings, review captured images, and potentially see previews before capture.
5. Provide a physical shutter button that behaves like the button on a normal camera.
6. Run from an internal rechargeable battery.
7. Provide removable microSD storage so the user can take completed images and animations off the camera.
8. Potentially host a Wi-Fi hotspot from the central computer so a phone or laptop can browse and retrieve finished media.

The likely central computer is a Raspberry Pi 4 Model B, but that selection is provisional.

## Intended User Experience

The current product concept is:

1. Power on a self-contained handheld camera.
2. Use its screen to review status and configure capture settings.
3. Hold and aim the rig like a normal digital camera.
4. Press one physical shutter button.
5. All four camera nodes capture their viewpoints.
6. The central computer receives the images and performs the post-processing pipeline.
7. The initial product plays the four photographs in sequence and then reverses direction, creating the appearance of a camera moving back and forth while time is frozen.
8. Under normal conditions, a reviewable result targets appearing on the built-in screen within two seconds after capture.
9. The user retrieves finished media from removable storage and, potentially, through the device's Wi-Fi hotspot.

The intended subjects include people, places, and objects. The expected capture environment has good light, such as daylight outdoors or an LED ring illuminating the scene.

Details of the later live-preview experience and the retake flow remain to be decided.

For version 1, the screen is deliberately simpler than the eventual product concept:

- No live preview before capture
- No user-adjustable camera settings
- No gallery, browsing, or deletion interface
- A capture/loading screen while a shot is being acquired and assembled
- Post-capture review of the generated animation
- The most recent animation remains displayed until the next capture begins
- Basic system and capture status as needed

Live preview is the first planned follow-up after version 1 end-to-end integration. User-adjustable camera settings are deferred to version 2.

## Capture Geometry and Output

### Initial product

- The four cameras are arranged side by side in one horizontal line.
- Adjacent camera sensors are spaced approximately 4 cm apart.
- Four cameras therefore have an approximate 12 cm first-to-last sensor span, before enclosure margins.
- All four cameras point straight ahead.
- All four capture at approximately the same moment.
- The four viewpoints are played as a back-and-forth animation.
- The visual effect should resemble one camera moving horizontally while the subject and scene remain frozen in time.
- The first implementation uses the four captured images directly.
- Version 1 performs no alignment, color matching, exposure normalization, or AI interpolation.
- Version 1 preserves all four original JPEGs and the generated animated GIF.
- The device has a soft two-second shutter-to-review target under normal conditions.
- A typical subject distance is about 3.5 ft (approximately 1.07 m), although the camera should remain usable at longer and other practical distances.

Total enclosure width and animation timing remain open.

### Scaled camera array

- The ideal later system has 12 or more cameras.
- The approximately 4 cm sensor pitch is the current geometry target.
- A 12-camera array at that pitch spans about 44 cm from the first sensor to the last, before enclosure margins.
- At four cameras the sensors are close enough to point straight ahead.
- A larger array will need a slight curve so its outer cameras converge toward the useful subject region.
- The camera-node and central-control architecture should avoid unnecessary assumptions that permanently limit the system to four nodes.

### Future processing

Later versions may:

- Align the four views.
- Correct differences so the views look as though they came from one consistently configured camera.
- Use AI frame interpolation to create a smoother apparent camera move.
- Explore NeRF or 3D Gaussian Splatting for richer novel-view or 3D results.

These are future enhancements rather than requirements for the first complete four-frame product.

The quality-processing work begins after the complete device can reliably capture, transfer, animate, display, and preserve a four-image set end to end.

## System Architecture

### Camera nodes - confirmed hardware

There are four identical camera nodes. Each currently consists of:

- Seeed Studio XIAO ESP32S3 Sense
- OV3660 camera sensor
- 16 GB microSD card
- Connection to the shared physical trigger
- Individual status LED
- The same Arduino camera-node firmware

Each node currently captures a 2048x1536 JPEG and saves it to its own microSD card.

### Central computer - planned

The central computer is expected to:

- Coordinate the system and capture workflow
- Acquire images from all four ESP32S3 nodes
- Track which four images belong to the same capture
- Run image cleanup and quality-improvement processing
- Create the final animated GIF
- Preserve every original JPEG alongside the generated GIF
- Target a reviewable result within two seconds under normal conditions
- Drive the integrated display and user interface
- Manage finished-media storage
- Potentially provide a local Wi-Fi hotspot and media browser

A Raspberry Pi 4 Model B with 2 GB RAM is already on hand and is the current central-computer candidate. Its operating system, communication links, and measured performance requirements are not yet fixed. It should be evaluated against the version 1 capture, transfer, GIF-generation, display, and two-second normal-case targets before it is treated as the final production choice.

### Camera-node communication - under evaluation

The two preferred transport candidates are USB and Wi-Fi.

USB advantages:

- Lower and more predictable latency
- Lower radio energy use
- Less software and network complexity
- Better behavior in radio-dense environments such as music festivals

USB disadvantages:

- More internal wiring and connectors
- Requires sufficient central USB ports or an internal USB hub
- Becomes increasingly cumbersome when scaling from four to 12 or more nodes

Wi-Fi advantages:

- Less physical data wiring
- Potentially lower assembly cost
- Easier physical scaling to more camera nodes

Wi-Fi disadvantages:

- Greater susceptibility to congestion and interference
- Higher energy use
- More discovery, connection, retry, and failure-handling complexity
- Less deterministic multi-node transfer timing

The current engineering direction is to prototype and measure both. USB is the leading candidate for the first four-camera product because reliability and the two-second normal-case result target matter more than eliminating short internal cables. Wi-Fi remains valuable as an alternate transport and may become more attractive for a 12+ node array.

The transport should sit behind a common capture/transfer protocol so the rest of the central software does not depend directly on USB or Wi-Fi.

### Trigger architecture

For the first complete version, the physical shutter button continues to pull the shared active-low trigger line used by all camera nodes.

Later, the central computer should also be able to initiate a capture for remote shutter, intervalometer, and time-lapse features. Its trigger output can join the same active-low trigger line, but it must behave as an isolated/open-drain pull-down. It must not drive the line high while the physical button can short it to ground. The exact transistor, buffer, or isolation circuit remains to be designed.

### Display and controls

Version 1 needs a minimal on-device interface that communicates system/capture status and automatically shows the post-capture animation. It does not need to stream a live preview, expose camera settings, or manage older captures.

The input method should be whichever is simplest to integrate with the selected Raspberry Pi display. A touchscreen is the leading option because small Raspberry Pi-compatible displays commonly include touch input, but touch is not yet a hard requirement. The exact display size, resolution, brightness, connection, and physical controls remain open.

Planned sequence:

1. Version 1: capture/loading state, persistent latest-result review, and essential status only
2. Fast follow: live preview
3. Version 2: user-adjustable camera settings
4. Much later: network-based media access, remote control, and other Wi-Fi features after the onboard experience is polished

### Power - prototype and planned

Current prototype power:

- All four ESP32S3 boards are powered over USB from a battery hub.

Planned product power:

- One internal rechargeable battery
- Internal power distribution for the four camera nodes, central computer, screen, and supporting electronics
- Mandatory USB-C charging
- Long enough runtime to take many capture sets per charge
- A single user-facing on/off control for the complete device
- Coordinated shutdown of the Raspberry Pi and camera nodes before power is removed
- Automatic safe shutdown when battery charge becomes too low, before brownout
- No requirement to operate while charging

The power subsystem must not simply remove power from a running Raspberry Pi. A hardware power controller or supervisor will likely need to monitor the button and battery, request an orderly software shutdown, wait for completion, and then disconnect the system load. The same sequence should run for a user shutdown and a low-battery shutdown.

Battery chemistry, capacity, regulators, exact low-battery thresholds, and a numerical runtime/capture-count target remain open. Those values should be chosen after measuring the real four-node, central-computer, display, and storage load.

### Storage - prototype and planned

Current prototype storage:

- Each camera node saves captures to its own 16 GB microSD card.

Planned product storage:

- User-removable storage for finished captures and animations
- A central mechanism for collecting images from the four nodes
- Direct image transfer from each node to the central computer, if bandwidth tests support it
- Node microSD storage only as an optional backup or diagnostic path rather than the primary pipeline
- A protected internal boot card dedicated to the Raspberry Pi operating system and application
- A physically separate user-removable media card containing the original JPEGs and generated GIFs

The camera driver already exposes a captured JPEG in the ESP32S3 frame buffer before it is written to microSD. A future firmware path may transmit directly from that buffer and return it after transfer, avoiding a required intermediate card write. Available memory, sustained transport bandwidth, retries, and the two-second normal-case target must be measured under simultaneous four-node operation.

The Raspberry Pi boot card should not be normally accessible to the user. The removable media card needs its own accessible slot or reader. The exact reader interface, card-removal detection, filesystem, and behavior when the media card is missing, full, corrupt, or removed during a write remain to be designed.

### Enclosure and physical design

Version 1 uses a simple 3D-printed box-shaped enclosure. It should:

- Be kept reasonably compact
- Protect and contain the complete integrated system
- Provide openings for all components that need external access
- Hold the four cameras in the defined straight horizontal arrangement

Version 1 does not have numerical weight or ergonomic targets. Integrated lighting, a tripod mount, weather resistance, refined grip geometry, and a polished industrial design are deferred to later revisions.

Exact dimensions should be set after the central computer, display, USB or network hardware, media-card reader, power electronics, battery, cooling, and internal wiring are selected and arranged.

### Failure behavior

Version 1 uses graceful degradation for capture and transfer failures:

- A failure by one camera does not discard successful images from the other cameras.
- The central computer continues saving and processing the images that arrived successfully.
- It creates the best available result from the remaining images when possible.
- The screen clearly reports that an error occurred.
- The error identifies the logical camera number and shows relevant diagnostic details.
- A stable camera identity scheme is therefore required even though all nodes run the same firmware.

The two-second shutter-to-review goal is a soft normal-case target. It may be exceeded while a capture, transfer, save, or other operation is actively progressing. The loading screen should remain active rather than report a false timeout. Timeout thresholds, retry policy, minimum image count for an animation, and whether diagnostics are also written to the media card remain to be designed.

## Current State

As of July 10, 2026:

- Four XIAO ESP32S3 Sense modules, four OV3660 sensors, and four 16 GB microSD cards are on hand.
- All four modules are assembled on a breadboard.
- A universal/shared shutter button is wired to all four nodes.
- Each node has its own status LED.
- The boards are powered by USB from a battery hub.
- The shared button and all four camera nodes work as expected.
- Each node captures and saves images to its individual microSD card.
- The repository contains working camera-node firmware plus wiring and flashing instructions.
- A Raspberry Pi 4 Model B with 2 GB RAM is on hand.
- The Raspberry Pi 4 has been imaged and boots Raspberry Pi OS successfully with the intended 800x480 HDMI display.
- Touch input works on the intended display.
- The display uses HDMI video and a micro-USB connection for touch and/or display-side power.
- The Raspberry Pi is reachable on the bench LAN as `camerapi` at the current address `10.0.0.136`, with OpenSSH enabled and verified key-based login for the local Windows/Codex development account.
- The dedicated private SSH key is stored outside the repository under the Windows user profile; non-secret connection details, the pinned host-key fingerprint, access boundaries, and recovery guidance are recorded in `docs/RASPBERRY_PI_SSH.md`.
- A powered USB hub is available for bench testing and carries USB data for at least one XIAO ESP32S3 camera node as detected by the Raspberry Pi.
- A 3D printer is available.
- The final integrated USB hub/cabling choice has not been validated.
- No integrated battery/charging system has been acquired.
- No separate user-removable card reader has been acquired.
- Raspberry Pi/display bring-up is mostly complete and first USB enumeration through a powered hub has started, but no Raspberry Pi application, transfer service, GIF-generation pipeline, display UI, power integration, or enclosure work has started.
- Approximately $200 remains available for version 1.
- Milestone 1 work has deliberately fast-forwarded to a one-node full-system vertical slice through the available powered hub: physical trigger, direct frame-buffer transfer to the Pi, verified persistence, representative processing, and touchscreen display.
- This sequencing change does not mark the earlier offline UI or isolated one-node transfer checkpoints complete; required portions are being integrated into the active test and remaining coverage is deferred.
- The one-node bench setup does not currently have its physical button connected. A framed Pi-to-node USB capture request is approved as temporary test scaffolding; it exercises the same capture routine but does not satisfy the later physical-trigger verification requirement.
- The Git-tracked Pi application and camera firmware now complete the one-node USB-request-to-touchscreen path through the powered hub, with CRC validation, atomic original preservation, manifests, resource/timing instrumentation, and reconnect discovery by stable node UID.
- A final 20-capture resource-instrumented run completed 20/20 captures with no checksum failures, recorded errors, or partial files. Median capture-event-to-display callback was 2.494 seconds, so the soft two-second target is not yet met; camera acquisition (1.374 seconds median) and node transfer (0.773 seconds median) dominate.
- A forced receiver interruption left no committed or partial capture, and the app/node recovered without a Pi reboot. Two literal cable unplug/replug cycles preserved logical Camera 1 and service continuity; a live disconnect displayed a missing-node error and recovered visibly. An in-flight corrupt-payload/NACK UI test, electrical power measurement, and concurrent four-node behavior remain unverified.

This is a successful four-camera capture-subsystem prototype at the boundary before central integration. It demonstrates the camera nodes, common trigger, local status indication, and local image storage. The next major milestone is the first bench-top end-to-end path through the Raspberry Pi; the project is not yet the self-contained handheld product.

The active work first proves and instruments that complete path with one node through the available USB hub, then scales it to four nodes. Battery integration and enclosure work follow only after the bench path works and its power/performance requirements have been measured. See `ROADMAP.md` and `MILESTONE_1_PLAN.md`.

The project is milestone-driven and has no fixed completion date. Work advances when the current milestone's exit criteria are satisfied.

## Confirmed Decisions

- The first complete rig has four cameras.
- The longer-term ideal is 12 or more cameras.
- Adjacent sensors are spaced about 4 cm apart.
- The four-camera array points straight ahead; a larger array will require a slight curve.
- The typical subject distance is about 3.5 ft, with support for other distances.
- Each camera has its own ESP32S3 computer.
- The device has a central computer in addition to the camera nodes.
- The device is intended to be handheld and fairly compact.
- The primary output is an animated GIF that moves through the captured viewpoints.
- The initial animation uses the four captured photographs and plays back and forth.
- Version 1 uses the raw captured images without alignment or appearance normalization.
- Every original image and the generated GIF are preserved.
- Version 1 provides post-capture review but no live preview.
- During capture, version 1 displays a loading/capture screen.
- After capture, the latest result remains displayed until the next capture.
- Version 1 does not provide an on-device gallery or deletion controls.
- Live preview is a fast-follow feature after end-to-end integration.
- User-adjustable camera settings are deferred to version 2.
- The four cameras are mounted side by side in a horizontal line.
- The rig is held and aimed like a normal digital camera.
- Expected subjects include people, places, and objects.
- Captures assume good daylight or added lighting such as an LED ring.
- A reviewable result targets appearing within two seconds after capture under normal conditions.
- The two-second target is soft and may be exceeded while work is actively progressing.
- The first version continues to use the shared physical trigger line.
- The central computer should later be able to activate that trigger for remote and time-lapse capture.
- Direct transfer to the central computer is preferred over dependence on four node microSD cards, subject to bandwidth testing.
- The final device has an integrated screen and a physical shutter button.
- The final device uses an internal rechargeable battery.
- The user needs removable storage for exported media.
- Raspberry Pi boot storage is protected and internal.
- User media is stored on a separate removable card.
- USB-C charging is required.
- Version 1 does not need to operate while charging.
- One on/off button controls the complete device.
- User-requested and low-battery shutdowns must safely stop all systems before power removal.
- Low battery must trigger orderly shutdown before a brownout.
- Version 1 uses a simple box-shaped 3D-printed enclosure.
- The version 1 enclosure should remain reasonably compact and expose all required user-accessible components.
- Weight optimization, ergonomic shaping, integrated lighting, tripod mounting, and weather resistance are deferred to later revisions.
- A failed camera does not cause successful images from that capture to be discarded.
- Version 1 saves and processes the available images when a capture set is incomplete.
- The screen reports incomplete captures with the failed camera number and relevant diagnostic details.
- Wi-Fi hotspot, browser access, and remote network features are deferred until the onboard system is highly polished.
- The available central-computer prototype is a Raspberry Pi 4 Model B with 2 GB RAM.
- A touchscreen and 3D printer are already available.
- Approximately $200 remains for version 1.
- The next milestone is a bench-top, USB-powered end-to-end prototype from four camera nodes through Raspberry Pi GIF generation and touchscreen review.
- Within that milestone, the active checkpoint is a one-node trigger-to-screen vertical slice through the powered USB hub, with detailed timing and resource analytics before four-node scaling.
- Battery and enclosure integration follow the bench-top end-to-end milestone.
- Progress is milestone-based without a fixed version 1 deadline.

## Provisional Ideas

- Raspberry Pi 4 Model B as the central computer
- USB as the primary transport for the first four-camera product
- Wi-Fi as an alternate transport and possible scaling option
- A shared application protocol that can operate over USB or Wi-Fi
- ESP32S3 frame-buffer transmission without an intermediate microSD write
- A touchscreen as the main on-device input method
- Live or near-live camera previews before capture
- A much-later device-hosted Wi-Fi hotspot for media access and possible remote control
- Image cleanup and enhancement performed locally on the central computer
- View alignment and appearance matching
- AI-generated intermediate frames
- NeRF or 3D Gaussian Splatting processing
- A dedicated hardware power controller or supervisor for button handling, battery monitoring, shutdown coordination, and final power cutoff

## Major Work Remaining

The ordered implementation plan is maintained in `ROADMAP.md`. The active bench-integration work is broken into testable intermediaries in `MILESTONE_1_PLAN.md`.

- Choose total enclosure width and define the curve/convergence geometry for a future 12+ camera array.
- Define GIF frame duration, playback direction, loop behavior, and export settings.
- Define the capture-set directory and filename scheme for four originals plus one GIF.
- Define camera-node identity and capture-set synchronization.
- Prototype and benchmark USB and Wi-Fi image transfer with four nodes.
- Test capture, transfer, and initial processing against the two-second normal-case target.
- Design a transport-independent capture and image-transfer protocol.
- Design the central computer's safe open-drain connection to the trigger bus.
- Implement reliable image transfer and retry/error handling.
- Assign and persist a stable logical number for each camera node.
- Define progress detection, timeout thresholds, retry rules, and the minimum viable partial animation.
- Implement user-visible camera-specific errors and useful diagnostic logging.
- Choose and benchmark the central computer.
- Record the available touchscreen model, physical size, exact power needs, and software support.
- Validate the available powered USB hub with all required camera nodes, or acquire a suitable USB hub if the bench hub is not reliable enough for the first transfer prototype.
- Acquire a separate user-removable media-card reader.
- Design the image alignment, cleanup, enhancement, and GIF pipeline.
- Design the on-device interface and preview architecture.
- Select a display and implement the minimal version 1 status/review interface.
- Add live preview after version 1 works end to end.
- Define version 2 camera settings and how they are synchronized across nodes.
- Select and integrate the separate user-removable card reader.
- Define safe behavior for a missing, full, corrupt, or prematurely removed media card.
- Design the internal power, charging, monitoring, and safe-shutdown system.
- Measure idle, capture, transfer, processing, and display power consumption.
- Set a numerical runtime or captures-per-charge requirement from those measurements.
- Select the battery, USB-C charging implementation, regulators, fuel gauge, and shutdown supervisor.
- Define the Raspberry Pi/node shutdown handshake and safe power-cut timing.
- Design the compact enclosure, camera mounts, controls, ports, and cooling.
- Lay out the integrated version 1 hardware before fixing enclosure dimensions.
- Produce a simple 3D-printable box enclosure with the required external openings and camera alignment.
- Revisit weight, ergonomics, lighting, tripod mounting, and weather resistance after version 1.
- Demonstrate the two-second normal-case end-to-end review target on candidate central hardware.
- Establish objective reliability, image-quality, runtime, and size targets.
- After the onboard experience is polished, optionally implement hotspot-based media browsing, download, and remote features.

## Draft Definition of Done

The project is complete when a user can pick up one self-contained device, power it on, configure a shot on its screen, press its physical shutter once, reliably capture all four views, receive a processed bullet-time GIF, review it, and remove or download the finished media without opening the device or manually handling the four camera-node cards.

This definition is a draft and should be refined during the project interview.
