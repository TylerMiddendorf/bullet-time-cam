# Milestone 4 Plan - Compact Version 1 Enclosure

Status: active July 18, 2026

## Outcome

Produce a simple, reasonably compact, box-shaped 3D-printed enclosure for the
validated four-camera V1 rig. Preserve the straight approximately 4 cm sensor
spacing, expose all required controls and media access, protect wiring and
camera ribbons, and support the selected external two-output battery pack
without enclosing it.

## Confirmed Boundaries

- Four sensors remain in a straight horizontal line at approximately 4 cm
  center spacing; the exact as-built pitch is measured before CAD is fixed.
- The 800x480 display, physical shutter, removable product USB drive, and camera
  apertures are user-accessible as appropriate.
- The external battery pack remains outside the enclosure. Separate supply
  leads reach the Raspberry Pi and powered USB hub through strain-relieved
  openings.
- Integrated lighting, tripod mounting, weather sealing, refined ergonomics,
  and weight optimization remain later-revision work.
- Pi-reported display area and USB descriptors are not mechanical dimensions;
  enclosure CAD uses direct physical measurements.

## Checkpoint 1 - Physical Inventory and Measurements

Record the installed orientation, maximum extents, mounting-hole locations,
connector keep-outs, cable exits, bend radii, and service-clearance needs for:

- Four camera sensors, flex cables, and XIAO ESP32S3 Sense boards
- Raspberry Pi 4 and its installed connectors/media
- 800x480 display, bezel, active area, touch interface, and mounting points
- Final powered USB hub, downstream hub/cabling, and product USB drive
- Shared-trigger hardware and physical shutter
- Both external battery-pack supply connections

Exit gate: a dated dimensioned inventory covers every part that enters, mounts
to, or passes through the enclosure; unknown dimensions are not guessed.

## Checkpoint 2 - Layout and Mechanical Risk Review

Create a dimensioned internal layout that:

- Keeps the four optical axes straight and the sensor centers at the measured
  approximately 4 cm pitch
- Prevents flex-cable pinching and respects cable/connector bend clearances
- Provides removable-media access without opening the enclosure
- Provides airflow and avoids trapping known heat sources against plastic or
  sensitive camera/display components
- Allows assembly, service, and fastener access in a defined order
- Strain-relieves the two external power leads independently

Exit gate: the layout has no unresolved part overlap, connector obstruction,
assembly dead-end, or unsupported load on a ribbon cable or port.

## Checkpoint 3 - CAD and Fit Checks

Model the shell, camera carrier, display mount, shutter mount, media opening,
ventilation, cable routes, fasteners, and alignment features. Print small fit
coupons or partial sections for high-risk interfaces before a complete shell.
Record printer, material, layer settings, revision, measured fit, and changes.

Exit gate: physical fit checks pass for camera spacing/alignment, display,
shutter, board/hub mounting, USB media, power-lead routes, and closure features.

## Checkpoint 4 - Enclosed-System Acceptance

Assemble the complete enclosure and verify:

1. Boot reaches the accepted logo/application presentation.
2. All four stable camera identities enumerate and GPIO17 idles LOW.
3. Physical-shutter and touchscreen actions each produce a valid four-camera
   set and ordered GIF on the removable product drive.
4. The display, shutter, product USB drive, and power connections remain usable
   without opening the enclosure.
5. Repeated captures do not cause cable movement, connector faults, camera
   misalignment, UI/service failure, or unacceptable enclosure temperature.
6. A power-off/restart leaves the product FAT and application state healthy.

Exit gate: the assembled V1 enclosure passes the functional checks, has no
unsafe hot spot or mechanical interference, and retains dated photos, CAD/print
revision, dimensions, and capture evidence.
