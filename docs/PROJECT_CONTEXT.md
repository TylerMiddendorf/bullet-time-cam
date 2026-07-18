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
7. Provide a removable USB drive so the user can take completed images and animations off the camera while the Raspberry Pi boot microSD remains protected inside the device.
8. Potentially host a Wi-Fi hotspot from the central computer so a phone or laptop can browse and retrieve finished media.

The likely central computer is a Raspberry Pi 4 Model B, but that selection is provisional.

## Intended User Experience

The current product concept is:

1. Power on a self-contained handheld camera.
2. See no operating-system content during boot: the display may remain blank during the early kernel phase, then shows only the product logo followed directly by the full-screen camera application, without boot logs, cursors, or loading diagnostics.
3. Use its screen to review status and configure capture settings.
4. Hold and aim the rig like a normal digital camera.
5. Press one physical shutter button.
6. All four camera nodes capture their viewpoints.
7. The central computer receives the images and performs the post-processing pipeline.
8. The initial product plays the four photographs in sequence and then reverses direction, creating the appearance of a camera moving back and forth while time is frozen.
9. Under normal conditions, a reviewable result targets appearing on the built-in screen within two seconds after capture.
10. The user retrieves finished media from removable storage and, potentially, through the device's Wi-Fi hotspot.

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
- Connection to the shared physical trigger
- The same Arduino camera-node firmware

Firmware 0.2.3 implements the July 17 camera-node simplification and subsequent bounded transfer/recovery fixes: it streams the 2048x1536 JPEG directly from the frame buffer to the Pi, does not initialize or access node storage, and leaves `D0 / GPIO1` unused. The same image is flashed to all four nodes and each passes camera, BTC1 protocol/stable-identity, and trigger startup gates. Earlier card/LED results remain truthful historical prototype evidence, not evidence for the current design. Physical and Pi-triggered four-node capture/integrity function is verified, and the product owner completed the prescribed unpowered multimeter checklist with every check reported passing.

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

For the first complete version, the physical shutter button pulls the shared active-low `D1 / GPIO2` trigger line used by all camera nodes. All four camera grounds share the trigger reference.

The Raspberry Pi also initiates the same simultaneous hardware capture through BCM `GPIO17` (physical pin 11) and a 2N3904 NPN open-collector stage. GPIO17 connects through 4.7 kOhm to the transistor base; a 100 kOhm resistor pulls the base to common ground; the emitter connects to common ground; and the collector connects to the shared trigger bus. GPIO17 idles low and pulses high for 100 ms, causing the transistor to pull the trigger bus low without ever driving the bus high. The Pi learns that capture began from the nodes' USB `CAPTURE_STARTED` messages rather than a separate trigger-sense GPIO. The complete circuit, power-sequencing rules, and validation sequence are in [`TRIGGER_CIRCUIT.md`](TRIGGER_CIRCUIT.md).

### Display and controls

Version 1 needs a minimal on-device interface that communicates system/capture status and automatically shows the post-capture animation. It does not need to stream a live preview, expose camera settings, or manage older captures.

The installed display is an 800x480 HDMI touchscreen. A July 17 query of the running Pi reports HDMI-A-2 at 65.681 Hz with a 150x100 mm physical area and generic EDID identity `Addi-Data GmbH`, model `0x0004`, serial `0x00000001`. Touch is provided by USB controller `8888:6666` over the display's micro-USB connection. That interface advertises USB 5 V / 100 mA maximum (0.5 W); this is descriptor data, not a measurement of the entire panel and backlight. Outer bezel/depth and actual load require physical measurement if needed for enclosure or battery sizing.

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

Historical prototype storage:

- Each camera node saved captures to its own 16 GB card before firmware 0.2.0 superseded that path.

Approved camera-node revision:

- Remove node microSD initialization, saving, backup, diagnostics, and card requirements from the firmware and deployment checks.
- Transfer every live JPEG directly from the ESP32S3 frame buffer to the central computer.
- Preserve user media centrally; removing node cards does not remove the separate user-removable media requirement.

Planned product storage:

- A user-removable USB mass-storage drive for finished captures and animations
- A central mechanism for collecting images from the four nodes
- Direct image transfer from each node to the central computer, if bandwidth tests support it
- A protected internal microSD card dedicated to the Raspberry Pi operating system and application
- Automatic Raspberry Pi application discovery of writable USB-backed filesystems
- A `BulletTime/` directory on the selected USB drive containing capture-set directories, original JPEGs, manifests, and generated GIFs

Firmware 0.2.3 transmits the captured JPEG directly from the ESP32S3 frame buffer and returns the buffer after the ACK/NACK transfer attempt. Simultaneous four-node operation is validated at product level. The qualifying 25-cycle run completed every set, but its 3.250-second median remains above the soft two-second target.

The Raspberry Pi boot card should not be normally accessible to the user. The removable USB drive uses a user-accessible USB port. The application must not fall back to the boot card when USB media is absent: touchscreen-initiated capture is blocked with a clear storage error, and a physical capture that arrives without writable USB storage is rejected rather than committed internally. Missing-drive detection and automatic mounting are implemented; full, corrupt, read-only, and removal-during-write behavior still require Raspberry Pi hardware validation.

### Enclosure and physical design

Version 1 uses a simple 3D-printed box-shaped enclosure. It should:

- Be kept reasonably compact
- Protect and contain the complete integrated system
- Provide openings for all components that need external access
- Hold the four cameras in the defined straight horizontal arrangement

Version 1 does not have numerical weight or ergonomic targets. Integrated lighting, a tripod mount, weather resistance, refined grip geometry, and a polished industrial design are deferred to later revisions.

Exact dimensions should be set after the central computer, display, USB or network hardware, removable USB-drive access, power electronics, battery, cooling, and internal wiring are selected and arranged.

### Failure behavior

Version 1 uses graceful degradation for capture and transfer failures:

- A failure by one camera does not discard successful images from the other cameras.
- The central computer continues saving and processing the images that arrived successfully.
- It creates the best available result from the remaining images when possible.
- The screen clearly reports that an error occurred.
- The error identifies the logical camera number and shows relevant diagnostic details.
- A stable camera identity scheme is therefore required even though all nodes run the same firmware.

The two-second shutter-to-review goal is a soft normal-case target. It may be exceeded while a capture, transfer, save, or other operation is actively progressing. The loading screen should remain active rather than report a false timeout. Timeout thresholds, retry policy, minimum image count for an animation, and whether diagnostics are also written to the removable USB drive remain to be designed.

## Current State

As of July 18, 2026:

- Four XIAO ESP32S3 Sense modules and four OV3660 sensors are on hand. Four node cards from the superseded prototype remain in inventory but are not used by current firmware.
- All four modules are assembled on a breadboard.
- A universal/shared shutter button is wired to all four nodes.
- Historical/superseded: each node previously used an individual status LED.
- The boards are powered by USB from a battery hub.
- The shared button and all four camera nodes work as expected.
- Historical/superseded: the original prototype saved images to individual node cards.
- Firmware 0.2.3 is flashed and startup-verified on all four nodes. It leaves `D0 / GPIO1` unused and transfers captures directly through BTC1 without initializing node storage.
- A Raspberry Pi 4 Model B with 2 GB RAM is on hand.
- The Raspberry Pi 4 has been imaged and boots Raspberry Pi OS successfully with the intended 800x480 HDMI display.
- Touch input works on the intended display.
- The display uses HDMI video and a micro-USB connection for touch and/or display-side power.
- The Raspberry Pi is reachable on the bench LAN as `camerapi` at the current address `10.0.0.136`, with OpenSSH enabled and verified key-based login for the local Windows/Codex development account.
- The dedicated private SSH key is stored outside the repository under the Windows user profile; non-secret connection details, the pinned host-key fingerprint, access boundaries, and recovery guidance are recorded in `docs/RASPBERRY_PI_SSH.md`.
- The final V1 USB hub/cabling chain is installed on the Raspberry Pi. The Pi reports VIA Labs `2109:3431` feeding Terminus `1a40:0101`; the four ESP32 nodes enumerate concurrently through the downstream four-port hub at 12 Mb/s, while the touchscreen and removable drive also enumerate on the installed chain.
- A 3D printer is available.
- The final integrated USB hub/cabling selection is installed and has passed the recorded four-node concurrent integrity runs. Aggregate system power remains unmeasured.
- No integrated battery/charging system has been acquired.
- The product owner has added a USB drive to the Raspberry Pi for removable JPEG/GIF storage.
- The Pi application detects mounted USB-backed filesystems, can request automatic mounting through `udisks2`, writes capture sets below `BulletTime/`, records the selected USB filesystem in each manifest, and refuses to fall back to the boot microSD. The added 231 GB FAT USB partition is `/dev/sda1`, label/mount name `USB DISK`, and is mounted read/write for the camera user at `/media/username/USB DISK`. Product-level four-original/manifest/GIF persistence and reboot continuity pass on this drive. Full/read-only/corrupt/removal-during-write and deterministic multi-drive cases remain Milestone 2 work.
- Raspberry Pi/display bring-up, concurrent four-node grouping, multi-image GIF generation, camera-specific partial capture, touchscreen review, and normal removable-USB persistence are implemented and physically validated. Power integration and enclosure work remain.
- Approximately $200 remains available for version 1.
- Milestone 1 work deliberately fast-forwarded to a one-node full-system vertical slice through the available powered hub: direct frame-buffer transfer to the Pi, verified persistence, representative processing, and touchscreen display. The earlier temporary USB-request diagnostic path and the current physical/Pi hardware-trigger paths are validated.
- This sequencing change does not mark the earlier offline UI or isolated one-node transfer checkpoints complete; required portions are being integrated into the active test and remaining coverage is deferred.
- The physical button and Pi GPIO17/2N3904 stage are connected to the four-node shared trigger. The framed Pi-to-node USB request remains explicit diagnostic scaffolding only; normal touchscreen actions use one 100 ms GPIO17 pulse.
- The Git-tracked Pi application and camera firmware complete the physical/Pi-trigger-to-touchscreen path through all four powered nodes, with CRC validation, atomic capture-set preservation, ordered GIFs, manifests, resource/timing instrumentation, camera-specific partial review, and reconnect discovery by stable node UID.
- A final 20-capture resource-instrumented run completed 20/20 captures with no checksum failures, recorded errors, or partial files. Median capture-event-to-display callback was 2.494 seconds, so the soft two-second target is not yet met; camera acquisition (1.374 seconds median) and node transfer (0.773 seconds median) dominate.
- A forced receiver interruption left no committed or partial capture, and the app/node recovered without a Pi reboot. Two literal cable unplug/replug cycles preserved logical Camera 1 and service continuity; a live disconnect displayed a missing-node error and recovered visibly. A deliberately corrupted live USB payload produced a targeted NACK and visible checksum error without committing an original or partial file; the next normal capture succeeded.
- On July 17, one physical press and one normal Pi touchscreen action each produced exactly one Camera 1 capture through atomic commit and display with no error. Separate four-node observers showed one physical press and one real 100 ms GPIO17 pulse each produced exactly one valid capture per stable UID with zero duplicates/errors. A 10-cycle GPIO17 run passed all 40 captures; pulse-to-all-completions was 2.455 seconds median and 2.497 seconds maximum, with 4.930 ms maximum start spread.
- Later on July 17, the repository/module reorganization at `b950740` was pushed before the Pi pulled it, then regression-tested on the physical rig. The exact rebuilt firmware passed all three startup gates on all four reflashed nodes; another 10-cycle GPIO17 run passed 40/40 valid captures with zero duplicates/errors. The renamed `bullet-time-ui.service`, removable USB capture, and all 33 automated boot checks passed both installation and a requested Pi reboot; a post-reboot real capture was CRC-valid and the service returned active with GPIO17 LOW. Detailed evidence is in `docs/evidence/milestone-1/checkpoint-4/refactor-hardware-regression-2026-07-17.md`.
- On July 18, the full product coordinator passed its physical-rig E2E contract: 25/25 complete four-node sets (100 originals and 25 six-frame GIFs), every logical camera unavailable separately, checksum-corrupt and mid-transfer-truncated Camera 1 cases with complete recovery, stable Camera 4 identity through reboot, and separate physical-shutter and touchscreen/GPIO17 product captures. The byte validator passed 35 named sets and the environment-gated live suite passed. Complete-set time was 3.250 seconds median and 3.289 seconds maximum, so the soft two-second target remains open. Representative normal and corrected camera-specific partial screens were photographed. See `docs/evidence/milestone-1/checkpoint-5/checkpoint5-four-node-e2e-2026-07-18.md`.
- The product owner initially connected the trigger circuit while powered, then later completed the full prescribed unpowered multimeter checklist and reported every continuity, resistance, button, isolation, and no-direct-short check passing. Individual readings were not retained. Electrical power remains unmeasured.
- July 16-17 product-boot trials found four constraints on the current Raspberry Pi OS Trixie/kernel build. A custom Plymouth script theme crashed Plymouth 24.004.60 in `libply-splash-core`/`libply`; Raspberry Pi's initramfs early-fullscreen-logo path produced black/no-signal output and never reached networking; after the generated hook/package were removed and initramfs rebuilt, a console-less boot still failed to reach networking while the otherwise identical `console=tty1` recovery boot succeeded; and regenerating the already-clean initramfs after that successful boot again prevented the Pi from reaching userspace. The visually accepted implementation disables both splash mechanisms and desktop chrome, bypasses initramfs with `auto_initramfs=0`, retires Raspberry Pi Imager's completed NoCloud/cloud-init boot stages, retains one masked/silenced `tty1` console for boot compatibility, loads a transparent compositor cursor, and produces a blank early boot followed by matched compositor/application logo frames and the camera UI. The July 17 final cold boot showed no operating-system text or cursor and passed all automated checks. Reproduction and recovery are documented in `docs/RASPBERRY_PI_BOOT_RUNBOOK.md`.

The project now has a validated four-node Raspberry Pi product workflow for both trigger sources. The node-to-Pi protocol, direct concurrent JPEG transfer, integrity checks, atomic capture-set preservation, ordered GIF generation, instrumentation, camera-specific partial degradation, and touchscreen review work on the physical rig. Raspberry Pi GPIO17 is deployed, idles output LOW, and has passed fake-backend plus powered hardware tests. Milestone 1 is complete, with the 3.250-second median review latency explicitly retained above the soft two-second target. It is not yet a self-contained handheld product because removable-drive fault qualification, aggregate power measurement, battery/safe-power integration, and enclosure work remain.

The next milestone is removable USB media fault qualification, followed by electrical power measurement and battery/safe-shutdown design. Latency optimization can proceed without invalidating the completed behavior/reliability evidence. See `ROADMAP.md`, `MILESTONE_1_PLAN.md`, and `FOUR_NODE_E2E_TEST_PLAN.md`.

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
- During boot, the display shows only `assets/Logo_800x480.png` and transitions directly to the full-screen camera application; Raspberry Pi firmware artwork, desktop UI, boot logs, cursors, and startup diagnostics are not user-visible.
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
- Camera-node local storage and GPIO-driven status indication are removed from firmware 0.2.3; all four nodes pass revised startup and physical/Pi-trigger functional capture gates, and the product owner reported the full unpowered circuit checklist passing.
- Live JPEGs transfer directly from each ESP32S3 frame buffer to the central computer.
- Each node uses `D1 / GPIO2` for the shared active-low physical trigger; `D0 / GPIO1` is unused.
- Raspberry Pi BCM GPIO17, physical pin 11, activates the shared trigger through the documented 2N3904 open-collector circuit.
- The Pi observes capture start through USB `CAPTURE_STARTED` messages rather than a separate trigger-sense GPIO.
- The final device has an integrated screen and a physical shutter button.
- The final device uses an internal rechargeable battery.
- The user needs removable USB storage for exported media.
- Raspberry Pi boot storage is a protected internal microSD card.
- Original JPEGs, manifests, and generated GIFs are stored on a physically separate USB drive; the application does not use the boot card as a media fallback.
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
- The bench-top, USB-powered end-to-end milestone from four camera nodes through Raspberry Pi GIF generation and touchscreen review is complete.
- Removable USB media fault qualification is next; battery and enclosure integration follow measured aggregate power and safe-power design.
- Progress is milestone-based without a fixed version 1 deadline.

## Provisional Ideas

- Raspberry Pi 4 Model B as the central computer
- USB as the primary transport for the first four-camera product
- Wi-Fi as an alternate transport and possible scaling option
- A shared application protocol that can operate over USB or Wi-Fi
- ESP32S3 frame-buffer transmission without an intermediate node storage write
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
- Optimize or explicitly accept the measured 3.250-second median four-node review path against the soft two-second target; run a focused Wi-Fi spike only if USB exposes a concrete blocker.
- Continue validating the Raspberry Pi candidate during removable-media fault and aggregate-power testing before treating it as the final production choice.
- Measure the installed display's outer bezel/depth and actual current only if the Pi-reported 150x100 mm area and USB 5 V / 100 mA descriptor are insufficient for enclosure or battery design.
- Retain the installed final V1 hub/cabling and include it in aggregate power and final enclosure-layout measurements.
- Complete real-drive unplug/replug, full, corrupt, read-only, removal-during-write, and deterministic multi-drive validation on the Raspberry Pi.
- Design future image alignment, cleanup, and enhancement after the validated raw-image GIF path.
- Design the fast-follow live-preview architecture.
- Add live preview after version 1 works end to end.
- Define version 2 camera settings and how they are synchronized across nodes.
- Validate and integrate the selected removable USB drive and its accessible product USB port.
- Complete hardware tests for a missing, full, corrupt, read-only, or prematurely removed USB drive.
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

The project is complete when a user can pick up one self-contained device, power it on, confirm readiness on its screen, press its physical shutter once, reliably capture all four views, receive a processed bullet-time GIF, review it, and remove or download the finished media without opening the device or manually handling the four camera-node cards.

This definition is a draft and should be refined during the project interview.
