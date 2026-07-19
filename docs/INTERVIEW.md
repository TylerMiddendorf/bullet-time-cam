# Project Interview

Status: baseline interview complete

This interview captures product intent, constraints, and decisions that cannot be recovered from firmware alone. Summaries should be carried into `PROJECT_CONTEXT.md` once confirmed.

## Starting Context - June 26, 2026

### Product vision supplied by the project owner

- Build a production-like, complete bullet-time rig.
- Keep it handheld and fairly compact.
- Use four camera nodes, each managed by its own ESP32S3.
- Add a main computer, prospectively a Raspberry Pi 4 Model B.
- Have the main computer collect the images, improve image quality, and create a GIF that moves through all viewpoints.
- Add an integrated screen for settings, image review, and potentially pre-capture previews.
- Add a normal camera-like shutter button.
- Power the complete system with an internal rechargeable battery.
- Give the user removable microSD storage for retrieving media.
- Potentially add a Wi-Fi hotspot for browsing photos from a phone or laptop.

### Current state supplied by the project owner

- Four XIAO ESP32S3 Sense modules are available.
- Each has a 16 GB microSD card and an OV3660 sensor.
- All four are installed on a breadboard.
- The breadboard has one universal trigger button and individual status LEDs.
- The nodes are powered over USB from a battery hub.
- All four boards and the shared trigger work as expected.
- Every camera node saves its images to its own microSD card.

## Interview Topics

Topics are ordered roughly by how strongly they affect the rest of the design:

1. Capture experience and final animation
2. Physical camera geometry and intended subjects
3. Image-transfer and central-control architecture
4. Image processing and quality expectations
5. Screen and user-interface workflow
6. Storage and file retrieval
7. Power, charging, and runtime
8. Enclosure, ergonomics, and environmental expectations
9. Reliability and failure handling
10. Wi-Fi sharing and optional features
11. Budget, schedule, and fabrication constraints

## Interview Completion

The initial product-definition interview is complete. Future questions should be added when a milestone exposes a new decision or changes an existing assumption.

## Decision Log

### 2026-06-26 - Capture experience and output

- Intended subjects are people, places, and objects.
- Captures are expected in good light, such as outdoor daylight or with an LED ring.
- The device is held and aimed like a normal digital camera.
- Four cameras are arranged side by side in a horizontal line.
- The animation moves back and forth through the viewpoints while the scene appears frozen.
- The first implementation plays the four captured photographs directly.
- A result should normally appear on the device screen within two seconds of pressing the shutter.
- Future processing may align the views, normalize their appearance, and use AI frame interpolation.
- NeRF and 3D Gaussian Splatting are possible longer-term experiments.

### 2026-06-26 - Camera geometry and scale

- The first complete rig uses four cameras.
- The ideal later system scales to 12 or more cameras.
- Adjacent sensors are spaced approximately 4 cm apart.
- The four-camera arrangement has an approximate 12 cm first-to-last sensor span.
- All four cameras can point straight ahead because the array is relatively narrow.
- A larger array should have a slight curve to direct the outer cameras toward the subject region.
- The typical subject distance is about 3.5 ft (approximately 1.07 m).
- Longer and other practical subject distances should also be supported.
- At the current pitch, a future 12-camera array would span approximately 44 cm before enclosure margins.

### 2026-06-26 - Communication, trigger, and node storage

- USB and Wi-Fi are the preferred communication candidates.
- USB is expected to reduce latency, radio energy use, and software complexity.
- Wi-Fi would reduce internal wiring and may reduce build cost.
- Wi-Fi reliability is a concern in radio-dense locations such as music festivals.
- Both transports should be discussed and potentially prototyped.
- The first complete version continues to use the physical button and shared trigger pin directly.
- A later version should allow the central computer to pull the same trigger line low for remote capture and time-lapse operation.
- Direct node-to-central-computer transfer is preferred to depending on four microSD cards.
- Direct transfer remains conditional on bandwidth and latency tests.
- Buffering the captured JPEG in board memory is preferred if practical.
- Node microSD cards may remain useful as optional backup or diagnostic storage.

Engineering recommendation recorded for evaluation:

- Lead with USB for the first four-camera product and implement Wi-Fi as a second transport.
- Keep the capture and transfer protocol independent of its underlying transport.
- Transmit directly from the ESP32S3 camera frame buffer when possible.
- Use an open-drain or isolated pull-down circuit when the central computer is later connected to the active-low trigger bus.

### 2026-06-26 - Version 1 processing and preservation

- Version 1 takes the four raw captured images and assembles them into the animation.
- Alignment, color/exposure normalization, and other image-quality processing begin after the complete setup works end to end.
- All four original images must be preserved.
- The generated GIF must also be preserved.
- The version 1 end-to-end media set therefore contains at least four original JPEGs and one animated GIF.

### 2026-06-26 - Version 1 screen and controls

- The simplest control technology should be used.
- A touchscreen is the leading option because it is common on small Raspberry Pi-compatible displays, but it is not mandatory.
- Version 1 provides post-capture review only, with no live preview.
- Live preview is a fast-follow feature after version 1 end-to-end integration.
- Version 1 does not expose user-adjustable camera settings.
- Camera settings are deferred to version 2 and will be revisited after integration.

### 2026-06-26 - Central storage and version 1 review flow

- The Raspberry Pi uses a protected internal boot card.
- Original JPEGs and generated GIFs are written to a separate user-removable media card.
- Version 1 does not need an on-device gallery or deletion workflow.
- During acquisition and processing, the screen displays a capture/loading state.
- After processing, the latest result is displayed.
- The latest result remains on-screen until the next capture starts.

### 2026-06-26 - Version 1 battery and power behavior

- Version 1 should have substantial runtime and take many pictures per charge.
- A numerical runtime or capture-count target has not yet been set.
- USB-C charging is required.
- The camera does not need to operate while charging.
- One on/off button should safely start and stop the complete system.
- Shutdown must safely stop the Raspberry Pi and all camera nodes before removing power.
- Low battery should trigger the same safe shutdown path before the system can brown out.

Engineering recommendation recorded for evaluation:

- Measure the complete system before selecting final battery capacity.
- Use a hardware power controller or supervisor that can request shutdown, monitor completion, and disconnect power.
- Include battery measurement/fuel-gauge capability rather than relying on brownout detection.

### 2026-06-27 - Version 1 enclosure

- Version 1 uses a simple 3D-printed, box-shaped enclosure.
- It includes openings for every system that needs external access.
- The enclosure should be kept reasonably small.
- Exact size and weight targets are not required for version 1.
- Refined ergonomics are deferred to later enclosure revisions.
- Integrated lighting, a tripod mount, and weather resistance are later-edition considerations.

### 2026-06-27 - Version 1 failure handling and timing

- A failed camera does not invalidate the entire capture set.
- Images received successfully from the remaining cameras are still saved.
- Processing continues with the available images.
- The screen reports that an error occurred.
- The error identifies the camera number and includes relevant debugging details.
- The two-second shutter-to-review goal is a soft normal-case target.
- Capture, transfer, or other active work may extend the wait beyond two seconds.
- The display should continue showing the loading state while work is progressing.
- Exact timeouts and automatic retry behavior still need to be designed.

### 2026-06-27 - Wi-Fi feature timing

- Device-hosted Wi-Fi and browser-based access are much-later features.
- Network media access, remote triggering, remote status, and remote settings are outside version 1.
- Wi-Fi product features should not be developed until the onboard system is highly polished.

### 2026-06-27 - Current inventory and implementation boundary

Hardware already available:

- Raspberry Pi 4 Model B with 2 GB RAM
- Raspberry Pi-compatible touchscreen
- Four working XIAO ESP32S3 Sense camera nodes
- 3D printer access

Hardware not yet available:

- USB hub
- Integrated battery and charging system
- Separate user-removable media-card reader

Implementation status:

- No work has been completed beyond the working four-camera breadboard prototype.
- There is no Raspberry Pi-side application or transfer service.
- There is no GIF-generation pipeline.
- There is no integrated display interface.
- There is no battery/power integration.
- There is no enclosure design or print.

### 2026-06-27 - Budget and agreed next milestone

- Approximately $200 remains available for version 1.
- The budget is considered tight.
- The next milestone is a bench-top end-to-end prototype using existing USB/bench power.
- That milestone connects four camera nodes to the Raspberry Pi, generates the GIF, and displays it on the touchscreen.
- Battery integration and enclosure work wait until the central path is proven and measured.
- Purchases should be limited to hardware that directly unblocks the agreed milestone.

### 2026-06-27 - Schedule

- Version 1 has no fixed deadline.
- Progress is milestone-based.
- Each stage advances when its exit criteria are met rather than on a calendar date.

### 2026-07-10 - Fast-forward to one-node full-system bench test

- The product owner chose to fast-forward Milestone 1 work to Checkpoint 4 using one camera node connected through the available USB hub to the Raspberry Pi.
- The narrow test must cover the real physical trigger, image capture, direct USB image transport, Pi-side validation and preservation, representative processing, and touchscreen display.
- It must collect detailed timings for the distinct node and Pi stages, plus image size/integrity, Pi resource use, reconnect behavior, and failure evidence needed for future transport, processing, storage, hub, timeout/retry, four-node, and power-test decisions.
- Earlier Checkpoints 2 and 3 are not declared complete. Their required one-node elements are folded into the active vertical slice; remaining offline four-image, partial-set, and isolated-transfer coverage is deferred.
- One-node results may be used to project bottlenecks, but they do not replace later concurrent four-node validation or electrical power measurements.
- No new hardware purchase is authorized by this sequencing change; use the available node, powered hub, Pi, and touchscreen.

### 2026-07-10 - Temporary USB capture request

- The physical shutter button is not currently set up for the one-node bench test.
- Add a Pi-to-node USB capture-request message so the end-to-end path can be exercised now.
- The touchscreen may issue this temporary request; it does not replace later verification of the shared physical trigger.
- Keep all Arduino and Raspberry Pi application/service code in Git. Deploy the Pi application by committing and pushing the repository, then pulling a Git checkout on the Pi rather than relying on ad hoc copied source files.

### 2026-07-16 - Product boot presentation

- During Raspberry Pi startup, the integrated display shows only the repository product logo at `assets/Logo_800x480.png`.
- The logo transitions directly into the full-screen camera application.
- Raspberry Pi firmware artwork, desktop UI, boot logs, loading diagnostics, login prompts, and cursors must not be visible during normal startup.
- SSH and the serial console may remain available as non-display recovery and diagnostic paths.

### 2026-07-17 - Accepted Raspberry Pi boot implementation

- The product owner visually accepted the final cold-boot presentation after the remaining cloud-init text and compositor pointer were removed.
- On the validated Raspberry Pi OS Trixie/kernel combination, the accepted reliable sequence is a blank/black early boot, then `assets/Logo_800x480.png`, then the full-screen camera application.
- No operating-system text, firmware artwork, desktop, login prompt, loading diagnostics, or cursor may be visible.
- A logo during the pre-userspace kernel phase is no longer required on this exact platform because both attempted early-logo mechanisms prevented the Pi from reaching userspace or networking.
- Reliable startup takes priority over showing the logo earlier. The non-display SSH and serial recovery paths remain available.
- The accepted state and its rejected alternatives must be reproducible from the repository on a replacement Pi; `docs/RASPBERRY_PI_BOOT_RUNBOOK.md`, the installer, and the verifier are the canonical deployment path.

### 2026-07-17 - Simplified camera nodes and Raspberry Pi hardware trigger

- Remove the individual camera-node status LEDs and their GPIO behavior from the target design.
- Remove camera-node microSD initialization, saving, backup behavior, card requirements, and related runtime messages from the target firmware.
- Continue preserving every original JPEG and generated GIF on central storage; this decision removes only the four node-local cards and does not change the separate user-removable media requirement.
- Keep each camera's shared active-low trigger on XIAO `D1 / GPIO2` with the physical normally-open shutter button between the trigger bus and common ground.
- Use Raspberry Pi BCM `GPIO17` on physical pin 11 to initiate the same shared hardware trigger through a 2N3904 NPN open-collector circuit.
- Connect Pi GPIO17 through 4.7 kOhm to the 2N3904 base, connect 100 kOhm from base to common ground, connect the emitter to common ground, and connect the collector to the shared trigger bus.
- Keep GPIO17 low while idle and pulse it high for approximately 100 ms to produce the active-low trigger pulse.
- Do not connect a Raspberry Pi output directly to the shared trigger bus and never drive the bus high.
- Do not add a separate Pi trigger-sense input. Camera nodes continue reporting `CAPTURE_STARTED` over USB so physical-button and Pi-initiated captures enter the same Pi workflow.
- Implementation status at that point: firmware 0.2.0 removed the superseded node behavior and passed revised startup plus powered functional capture gates on all four nodes on July 17. Normal Pi capture is a single 100 ms GPIO17 pulse with the USB request explicit diagnostic scaffolding only. Separate physical and Pi actions produced one Camera 1 commit/display and exactly one valid capture per node in four-port observers; a 10-cycle run completed 40/40 captures with zero errors/duplicates. The multimeter inspection had initially been skipped; the later July 17 entry below records its subsequent completion and supersedes that open-gate status.

### 2026-07-17 - Removable USB media replaces removable media-card direction

- The product owner added a USB drive to the Raspberry Pi for storage of original JPEGs and generated GIFs.
- This supersedes the June 26 separate user-removable media-card decision; the Raspberry Pi still boots from a protected internal microSD card.
- The Pi application automatically discovers writable mounted filesystems whose backing block device is on the USB bus and asks `udisks2` to mount detected USB block media when necessary.
- Capture sets are stored below `BulletTime/` on the selected USB drive. If multiple writable USB drives are connected, configuration may prefer the drive's mount-directory name; otherwise selection is deterministic.
- The application must not silently write user captures to the protected boot microSD when removable USB storage is unavailable.
- Touchscreen-initiated capture is blocked with a visible error when no writable USB drive is available. Physical captures that still arrive are rejected rather than committed to internal storage.
- The implementation and failure path have automated test coverage. Pi inspection confirmed the added 231 GB FAT partition as `/dev/sda1`, label `USB DISK`; automatic mounting succeeded from the same user-service context as the camera application and produced a writable `/media/username/USB DISK` mount. Deployment of the new application plus actual JPEG persistence, unplug/replug, full-drive, read-only/corrupt-filesystem, and removal-during-write behavior still require evidence.

### 2026-07-17 - Trigger inspection, final USB chain, and display inventory

- The product owner completed the prescribed unpowered trigger-circuit multimeter checklist and reported that it passed fully. This supersedes the earlier same-day status in which the inspection had been skipped; individual readings were not retained in the repository.
- The product owner confirmed that the hub and cabling currently installed on the Raspberry Pi are the final V1 selection rather than temporary bench hardware.
- Read-only SSH inspection confirmed that the installed chain enumerates VIA Labs hub `2109:3431`, downstream Terminus hub `1a40:0101`, all four stable ESP32 identities, touchscreen controller `8888:6666`, and the removable USB drive.
- The running compositor reports the installed HDMI display at 800x480, 65.681 Hz, with a 150x100 mm physical area and generic EDID identity `Addi-Data GmbH`, model `0x0004`. The USB interface declares 5 V / 100 mA maximum. This descriptor is not an electrical measurement of the entire panel/backlight, and Linux cannot report the enclosure-facing bezel/depth.

### 2026-07-18 - External battery pack accepted for version 1

- The product owner directed that aggregate-power work be ignored because the
  power solution has already been handled.
- Version 1 uses an external battery pack with one rated 5 V / 2 A output for
  the Raspberry Pi and a separate rated 5 V / 2 A output for the powered USB
  hub.
- The battery pack has its own battery-percentage display, which is the V1
  charge indication.
- This supersedes the June 26 internal rechargeable battery, aggregate
  measurement, integrated charging/fuel-gauge, single-control sequencing, and
  automatic low-battery shutdown direction as V1 gates.
- No independent aggregate-current, runtime, regulation-margin, or coordinated
  shutdown measurement is claimed. Milestone 3 is closed by changed
  product-owner acceptance rather than by electrical test evidence, and
  enclosure work proceeds next.

### 2026-07-18 - Qt touchscreen UX scope and constraints

- Replace the on-device Tk interface with native Qt Quick/QML and PySide6 for
  fast, direct-feeling 800x480 touchscreen interaction.
- Implement the seven mockup-derived compositions for ready, progress, partial
  review, preview, four-camera controls, removable-media library, and viewer.
- Do not connect live preview yet. Use a temporary static image derived from the
  product logo and label it clearly as a disconnected demonstration
  placeholder.
- Do not include battery level, battery state, or reserved battery UI space.
  The separate display on the selected external battery pack remains the V1
  charge indication.
- Include read-only browsing of historical capture sets on the product USB
  drive and a viewer that detaches selected media before presentation. Do not
  add delete or edit controls.
- Camera settings may be represented as disabled future controls, but must not
  emit node commands. The current device remains a four-camera system and the
  UI must not claim hotspot or network availability.
- Track Pi validation through Git: commit and push changes, then fast-forward
  pull the same commits on the Pi before testing over SSH.

### 2026-07-18 - Touchscreen overflow and library navigation follow-up

- Keep the complete ready-screen capture prompt inside its button.
- Keep the removable-USB library heading inside its sidebar box.
- Make large media libraries discoverably navigable with right-side Up and Down
  controls; retain touch scrolling and include pagination status.
- Apply, commit, push, deploy, and verify these fixes one at a time on the
  Raspberry Pi.

### 2026-07-19 - Library and viewer deletion

- Add the ability to delete images/GIFs from the on-device library viewer and
  verify the behavior on the Raspberry Pi.
- This supersedes the July 18 read-only-library and no-delete constraint.
- Deletion applies to one complete published capture set: its original JPEGs,
  animation GIF, and manifest are removed together from removable USB storage.
- Require explicit confirmation and clearly state that deletion cannot be
  undone. Keep rename, editing, sharing, and boot-card browsing unsupported.

### 2026-07-19 - Removable-media capacity metric

- Show storage usage and availability on the Raspberry Pi media-library screen.
- Derive both figures from the currently selected removable USB filesystem.
- If removable USB capacity cannot be read, show it as unavailable rather than
  reporting capacity from the protected Raspberry Pi boot card.
- Commit and push the change, fast-forward pull it on the Pi, and verify the
  behavior on the physical Pi before treating it as complete.

### 2026-07-19 - Ready navigation and dedicated Capture screen

- Keep all existing USB, four-camera, READY/ATTENTION, and detail statuses on
  the Ready/start screen.
- Remove direct touchscreen photo taking from Ready. Its three actions are a
  gear icon opening Settings/control center, Library, and Capture.
- Rename the former Preview Demo route to Capture everywhere in current UI and
  operating documentation.
- Make Capture the only touchscreen photo-taking screen. Review and Settings
  may link to Capture but must not enqueue a photo themselves.
- Replace Media Demo and generic media-navigation labels with Library.
- Preserve the independent physical shutter and the existing capture-progress,
  review, camera-status, and USB-status behavior.
- Commit changes incrementally, push them, fast-forward pull the same commits
  on the Raspberry Pi, and test the reorganized UI there.

### 2026-07-19 - Ready and Library navigation icon sizing

- Replace the Library screen's `BACK TO CAMERA` label with a home icon that
  returns directly to Ready.
- Make the Ready screen's Settings gear and the Library screen's home icon
  occupy most of their respective touch buttons.

### 2026-07-19 - Camera USB recovery control

- Add a Settings action that can recover all four camera connections when the
  Raspberry Pi USB controller loses the downstream camera hub branch.
- The recovery is system maintenance, not an operative camera-image setting;
  exposure, white balance, smoothing, and interpolation remain disabled.
- The action may run only while capture is idle. It stops the application,
  syncs and unmounts USB filesystems, resets the validated Pi xHCI controller,
  waits for four usable ESP32 serial ports, and restarts the application.
- The product owner explicitly approved a persistent passwordless sudo rule
  limited to `/usr/bin/systemctl start --no-block
  bullet-time-usb-recovery.service`. No general shell or arbitrary sudo access
  is authorized.
- Track implementation and Pi validation through commit, push, fast-forward
  pull, native Settings rendering, a real controller recovery, and a valid
  four-camera capture afterward.

### 2026-07-19 - Ready USB storage and Settings home navigation

- Show whether the removable USB drive is connected on the Ready/home screen.
- Add a circular storage-usage indicator to Ready using capacity from the
  selected removable USB filesystem, without boot-card fallback.
- Add a large home-icon button to Settings matching the Library home action and
  returning directly to Ready.
- Commit and push incrementally, fast-forward pull each checkpoint on the Pi,
  and verify the implementation on the physical Pi.

### 2026-07-19 - Capture-time library previews

- Generate small image previews when captures are taken so large removable-USB
  libraries do not need to decode animated GIFs during catalog loading.
- Publish the preview atomically with the capture originals, animation, and
  manifest; retain compatibility with historical sets that lack a preview.
- Commit and push the change, fast-forward pull it on the Raspberry Pi, and
  verify it with a real capture on the physical rig.
