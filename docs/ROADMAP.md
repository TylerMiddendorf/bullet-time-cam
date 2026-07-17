# Bullet-Time Camera Rig Roadmap

This roadmap reflects product decisions through July 17, 2026, capture-path bench evidence through July 11, and product-boot hardware evidence through July 17. The remaining version 1 budget is approximately $200, so purchases should be tied to a demonstrated milestone and reused in the integrated device whenever practical.

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

Status: active - Checkpoint 4 physical and Pi hardware-trigger validation remains open

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

- Camera-node simplification is implemented, flashed, and startup-verified on all four nodes; capture validation remains open.
- Raspberry Pi BCM GPIO17 hardware-trigger output is installed and fake-backend tested with a boot-safe low idle and 100 ms high pulse; the service is stopped pending unpowered circuit checks and electrical validation.
- Use USB `CAPTURE_STARTED` as the Pi notification path for both physical and Pi-initiated captures; do not add a direct trigger-sense GPIO.
- Identify and configure the available touchscreen.
- Establish Raspberry Pi OS and application development environment.
- Assign stable logical camera numbers.
- Define a transport-independent capture and image-transfer protocol.
- Prototype direct JPEG transfer from one ESP32S3 frame buffer.
- Select USB or Wi-Fi from measured latency, reliability, power, and complexity.
- If USB leads, validate the available powered hub first and acquire only the hub/cabling still needed for the bench prototype.
- Scale transfer from one node to all four nodes.
- Implement capture-set grouping, partial-set handling, and diagnostics.
- Preserve originals and generate the version 1 GIF.
- Implement the loading/result/error display states.
- Configure the accepted product boot path: no visible OS content during early boot, then the product logo handing directly to the full-screen application, with no desktop, console, cursor, or boot diagnostics.
- Measure normal shutter-to-review time against the soft two-second target.

Intermediary checkpoints:

1. Pi and touchscreen bring-up
2. Offline GIF/UI vertical slice using existing repository photos
3. One-node direct USB JPEG transfer
4. **Active:** one-node full-system bench test through the powered USB hub, including capture, direct transfer, preservation, representative processing, touchscreen display, and stage analytics
5. Four-node capture grouping and partial-failure handling
6. Integrated live GIF/touchscreen flow
7. Performance and reliability pass

By product-owner decision on July 10, 2026, work fast-forwards to Checkpoint 4. Checkpoints 2 and 3 are not marked complete; the portions required for the one-node vertical slice are absorbed into Checkpoint 4, and remaining offline four-image and isolated-transfer coverage is deferred. The one-node test must capture detailed stage timing, integrity, resource, and failure evidence before four-node scaling. One-node measurements guide future choices but do not replace later concurrent four-node and electrical power measurements.

Checkpoint 4 has demonstrated the temporary USB-request-to-touchscreen path, a clean 20-capture instrumented run, two literal hub reconnects, visible missing-node error/recovery, safe non-commit when the receiver is terminated mid-transfer, and a live deliberately corrupted payload that produced a targeted NACK, visible UI error, no committed/partial image, and immediate successful recovery. On July 17, simplified firmware was compiled, hash-verified, flashed, and startup-smoked on all four nodes; 13 Pi/protocol tests passed for the hardware-only normal action and GPIO safety behavior. It remains active for the unpowered circuit inspection plus physical-button and Pi-GPIO capture demonstrations. The measured earlier 2.494-second median result exceeds the soft target; acquisition and USB transfer are the first optimization candidates before four-node scaling. Separately, the product-boot portion of Checkpoint 6 was visually accepted on July 17 and is reproducible through `RASPBERRY_PI_BOOT_RUNBOOK.md`.

Exit criteria:

- Repeated button presses complete the path from four nodes to touchscreen.
- Original JPEGs and the GIF are preserved for every successful capture.
- Incomplete capture sets remain usable and report the failed camera.
- Normal captures approach the two-second review target.

## Milestone 2 - User-Removable Media

Status: after bench integration

- Acquire and integrate a separate removable-card reader.
- Keep Raspberry Pi boot storage protected and internal.
- Define capture-set directory and filename conventions.
- Write originals and GIFs to the user card.
- Handle missing, full, corrupt, and prematurely removed cards safely.

## Milestone 3 - Integrated Battery and Safe Power

Status: after measuring the bench system

- Measure idle, capture, transfer, processing, display, and peak power.
- Set a runtime or captures-per-charge target.
- Select battery capacity and regulators from measured demand.
- Add USB-C charging.
- Add battery/fuel monitoring.
- Implement one-button startup and coordinated shutdown.
- Trigger the same safe shutdown before low-voltage brownout.
- No operation while charging is required for version 1.

## Milestone 4 - Compact Version 1 Enclosure

Status: after hardware layout stabilizes

- Arrange all final version 1 components.
- Model a reasonably compact box-shaped enclosure.
- Maintain the 4 cm sensor spacing and straight camera alignment.
- Provide openings for cameras, screen, shutter, power, USB-C, media card, and other required access.
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

Approximately $200 remains for version 1. Do not purchase battery, charging, enclosure-specific, or optional network hardware until the bench-top end-to-end milestone identifies actual requirements. Use already-available bench hardware where reliable, and confirm electrical and software compatibility before buying each missing component.
