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
