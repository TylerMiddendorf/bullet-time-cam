# Milestone 4 Plan - Compact Version 1 Enclosure

Status: active July 18, 2026

## Outcome

Produce a simple, reasonably compact, box-shaped 3D-printed enclosure for the
validated four-camera V1 rig. Preserve the straight approximately 40 mm sensor
spacing, expose all required controls and media access, protect wiring and
camera ribbons, and support the selected external two-output battery pack
without enclosing it.

The plan deliberately separates the precision camera carrier from the outer
shell. Camera alignment can then be developed and validated without printing a
complete enclosure, and later shell revisions will not move the four optical
datums.

## Confirmed Boundaries

- Four sensors remain in a straight horizontal line at approximately 40 mm
  center spacing; the exact as-built pitch is measured before CAD is fixed.
- All four optical axes point straight ahead. A curved array is outside V1.
- The 800x480 display, physical shutter, removable product USB drive, and camera
  apertures are user-accessible as appropriate.
- The external battery pack remains outside the enclosure. Separate supply
  leads reach the Raspberry Pi and powered USB hub through strain-relieved
  openings.
- The Raspberry Pi boot microSD remains protected inside the enclosure.
- The final installed USB hub and cabling are design inputs, not placeholders.
- Integrated lighting, tripod mounting, weather sealing, refined ergonomics,
  and weight optimization remain later-revision work.
- Pi-reported display area and USB descriptors are not mechanical dimensions;
  enclosure CAD uses direct physical measurements.
- No camera board, display, hub, or Raspberry Pi port carries enclosure loads.

## Planning Assumptions to Verify

These assumptions keep CAD moving but are not product decisions until the fit
checks pass:

- Use a removable front optical carrier, an internal electronics tray, and a
  screw-fastened rear shell or back panel.
- Orient the display on the user-facing rear surface and the four lenses on the
  opposing front surface.
- Prototype in PLA or PLA+ if that is the material already understood on the
  printer. Use PETG for the final enclosure if its coupons, bridges, fastener
  features, and closed-system thermal test pass. Do not mix calibration data
  between materials.
- Use mechanical fasteners for all service joints. Prefer captive nuts or
  proven heat-set inserts over repeatedly driving screws into printed plastic.
- Keep the shutter location parametric until a cardboard layout can be held in
  both hands without obscuring cameras, vents, display, or removable media.

## Required Design Records

Create `designs/enclosure/` when CAD work begins and retain:

- Native parametric CAD source
- A neutral STEP export for every release candidate
- Print-ready 3MF files that preserve orientation and slicer settings
- STL exports only where a printer workflow requires them
- A dimensioned component inventory
- Printer/material calibration results
- A revision log with the defect, changed parameter, print result, and decision
- Photos of every accepted fit coupon and assembled revision

Use revision names such as `M4-R01-optical-carrier` rather than `final` or
`final-v2`. Every physical part should have its revision embossed or written on
it and be traceable to its CAD and slicer profile.

## Printer Characterization - Ender 3 V3 SE

Creality specifies a standard 0.4 mm nozzle, 0.1-0.35 mm layer range, and
advertised +/-0.1 mm printing precision for the Ender 3 V3 SE. The advertised
number is not a guaranteed fit allowance for holes, slots, first layers,
overhangs, or different materials. Establish enclosure-specific allowances
with physical coupons.

### Freeze a baseline profile

Before dimensional testing:

1. Record printer firmware, slicer and version, nozzle size and age, build
   surface, filament brand/type/color, and whether the filament was dried.
2. Check that the gantry and bed are mechanically sound, clean the nozzle and
   build surface, run automatic leveling, and inspect the first layer.
3. Start with the material manufacturer's temperature range and a conservative
   speed profile. Dimensional coupons and enclosure parts use the same wall
   order, line width, layer height, cooling, and horizontal-expansion settings.
4. Use 0.20 mm layers as the initial general-purpose profile with the standard
   0.4 mm nozzle. Use slower external walls for fit-critical parts.
5. Do not change more than one printer or slicer variable between comparable
   coupon runs.

### Print the calibration set

Print at least two copies, placed in different bed regions, of one compact
coupon set containing:

- External 10, 20, and 40 mm X/Y dimensions
- A 10 or 20 mm Z step that does not include first-layer elephant foot in the
  measurement
- Round holes at 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, and 6.0 mm
- Rectangular slots at the same critical sizes expected in the enclosure
- Male/female sliding pairs at 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, and 0.40 mm
  clearance per side
- A 1.6 mm PCB-edge groove series and one display/bezel step representative of
  the planned mounting orientation
- Candidate M2, M2.5, and M3 clearance holes, captive-nut pockets, and insert
  bosses for only the fasteners actually being considered
- A short bridge, vertical slot, and horizontal slot to expose orientation-
  dependent behavior

Use a 0-150 mm digital caliper with 0.01 mm display resolution if available.
Measure each feature three times after the part has cooled, record the median,
and note print orientation. Caliper resolution does not imply equivalent part
accuracy.

### Convert results into CAD parameters

Keep these parameters near the top level of the model:

- `fit_slip_xy`
- `fit_service_xy`
- `hole_compensation_xy`
- `elephant_foot_relief`
- `insert_or_nut_pocket_allowance`
- `panel_gap`
- `camera_pitch`
- `wall_thickness`

Do not globally scale the enclosure to repair a local hole or first-layer
problem. Correct the printer/profile first when errors are large or inconsistent;
otherwise adjust the relevant CAD allowance or documented slicer compensation.

### Initial fit allowances before coupon data

The following are deliberately conservative starting points, not claims about
the printer. Each value is radial or per side unless stated otherwise.

| Interface | Initial CAD allowance | Intended result |
| --- | ---: | --- |
| Printed locator fitted once | 0.15-0.20 mm/side | Snug, hand-assembled fit |
| Removable sliding or service part | 0.25-0.30 mm/side | Repeatable slip fit |
| Large panel/shell nesting joint | 0.30-0.40 mm/side | No sanding needed after long prints |
| PCB edge or noncritical component pocket | 0.30 mm/side plus measured board variation | Retained without squeezing parts |
| Display bezel opening | 0.40-0.50 mm/side | Avoid glass/bezel loading |
| Cable pass-through | At least 0.50 mm/side beyond measured maximum | No insulation abrasion |
| Screw clearance hole | Use standard fastener clearance, then coupon-correct | Screw never cuts unintended threads |
| Captive nut or heat-set insert | Manufacturer geometry plus coupon result | No cracked boss or spinning hardware |

For example, a 20.00 mm removable rectangular part starts with a 20.50-20.60 mm
opening. This table must be replaced by measured project values before the
complete enclosure is released.

## Mechanical Architecture

### 1. Optical carrier

Make the camera array a short, stiff, independently removable rail or carrier:

- Define the four sensor centers from one master datum at measured `camera_pitch`.
- Locate each module against hard printed datum faces; use fasteners, light
  spring pressure, or compliant pads only to hold it against those datums.
- Do not clamp the lens, image sensor, flex cable, or connector.
- Add small adjustment slots only where real module variation requires them.
  Lock the accepted position mechanically after alignment.
- Support each camera flex cable immediately behind the module while preserving
  a relaxed service loop and the measured minimum bend radius.
- Key or label Cameras 1-4 so a serviced node returns to the correct position.
- Recess or hood the four lens openings enough to protect the lenses, but verify
  the hood never enters the field of view at image corners.
- Use a dark, matte inner surface around the apertures to limit internal
  reflections; do not place clear printed plastic in front of the lenses.
- Attach the carrier to the shell at three or more well-spaced points without
  warping it.

### 2. Display bezel and rear interface

- Support the display by its measured frame or mounting points, never by the
  active glass or touch surface.
- Keep a continuous relief gap around glass and fragile bezel edges.
- Prevent assembly screws from bottoming into the display.
- Expose the complete active/touch area and check edge gestures or controls.
- Make the display removable without first disturbing the camera carrier.
- Route HDMI and touch/power cables with connector keep-outs and service loops.

### 3. Electronics tray

- Mount the Pi, powered hub, downstream hub/cabling, trigger transistor/resistors,
  and XIAO boards to one removable tray or a small number of defined brackets.
- Use board mounting holes where available. Edge clips may locate boards but
  must not press components or solder joints.
- Orient high-use ports toward service openings or panel extensions.
- Restrain cable mass independently of USB, HDMI, and power connectors.
- Keep the Pi microSD internal while retaining a documented service path.
- Preserve access to fasteners and connectors in the reverse of the defined
  assembly order.

### 4. Removable USB media

- The product USB drive must be inserted and removed without opening the case.
- Prefer a short panel-mount extension or a captive internal receptacle over
  using the drive as a lever directly on the Pi or hub.
- Add finger clearance, an orientation key or label, and enough extraction
  space for the actual drive body.
- Retain the internal cable so routine drive removal does not move the hub.
- Do not create a nearby opening that makes the protected Pi boot card look
  user-removable.

### 5. Shutter and power entry

- Mount the shutter to a rigid wall or bracket and provide a positive travel
  stop so pressing it does not load solder joints.
- Keep its wiring away from sharp printed edges and give it a service connector
  or enough slack for opening the case.
- Give the Pi and powered-hub leads separate, labeled entries and separate
  strain relief. Pull force must be reacted by the enclosure, not either port.
- Make wrong-port insertion difficult through placement, labels, connector
  choice, or keying.

### 6. Cooling and structure

- Keep existing Pi and hub airflow paths open; do not sandwich heat sources
  against the display, camera sensors, or unsupported plastic walls.
- Place lower intake and upper/rear exhaust vents where practical, with enough
  solid perimeter and ribs to preserve shell stiffness.
- Avoid vents directly above exposed electronics if ordinary spills are a
  likely use condition, while recognizing that V1 is not weather-resistant.
- Begin with approximately 2.4 mm walls (six 0.4 mm line widths) and add local
  ribs/bosses instead of thickening the entire shell. Confirm the slicer's
  actual line count.
- Use generous internal fillets at bosses and load-bearing corners. Keep screw
  bosses separated from exterior walls to reduce cracking and visible sink.
- Avoid long unsupported horizontal roofs; split or orient parts to minimize
  support inside functional surfaces.

## Checkpoint 1 - Physical Inventory and Measurements

### Procedure

1. Photograph the complete working bench rig from front, rear, top, and both
   sides before disassembly. Label both ends of every cable.
2. Give every physical item an inventory identifier and record quantity,
   orientation, mass if a scale is available, and whether it is final V1
   hardware.
3. Measure maximum X/Y/Z extents at three locations when molded housings are
   tapered or irregular. Record the largest value rather than an average.
4. Measure mounting-hole diameter and center locations from one repeatable
   component datum. For undocumented boards, verify hole spacing twice from
   different reference edges.
5. Record connector body, plug, latch, cable, and insertion/removal envelopes;
   connector locations alone are insufficient.
6. Establish the relaxed bend radius and desired service loop for every flex and
   cable using the installed part, without sharply creasing it.
7. Measure the true display outer bezel, active area location, depth, rear-board
   protrusions, cable exits, and mounting points.
8. Measure each camera module separately and the present sensor-to-sensor pitch.
   Record module variation rather than assuming all four are identical.
9. Measure the actual USB drive body and the finger space needed to remove it.
10. Measure the installed hub stack and both external battery lead plugs, not
    catalog photos or Pi-reported descriptors.

### Inventory fields

| Field | Required content |
| --- | --- |
| Part ID and revision | Marking that maps measurement to the real component |
| Maximum envelope | X/Y/Z and measurement method |
| Functional datums | Edges, faces, centers, or holes used to locate it |
| Fasteners | Size, thread, head diameter/height, engagement depth |
| Keep-outs | Connector insertion, cable bend, button travel, airflow |
| Access class | User, routine service, or sealed/internal |
| Tolerance source | Measured variation, datasheet, or coupon-derived allowance |
| Notes/evidence | Photo filename and measurement uncertainty |

Exit gate: a dated, dimensioned inventory covers every part that enters,
mounts to, or passes through the enclosure. Every CAD-driving dimension has a
source; unknown dimensions are not guessed.

## Checkpoint 2 - Layout and Mechanical Risk Review

### Full-scale layout

1. Create simplified envelope models from the measurement inventory. Keep those
   models separate from printable geometry.
2. Arrange the camera carrier first, because the 40 mm-class pitch and straight
   optical axes are the least negotiable dimensions.
3. Place a full-scale paper or cardboard display and shell outline behind it.
   Add foam/card blocks for the Pi, hubs, drive, plugs, and cable volumes.
4. Hold the mock-up as intended and test shutter reach, display visibility,
   cable exits, USB removal, and whether fingers cover lenses or vents.
5. Create at least two internal layouts before choosing one. Compare enclosure
   dimensions, cable complexity, thermal path, assembly order, and service risk.
6. Draw the assembly sequence and the reverse service sequence. A part is not
   serviceable if a hidden fastener or trapped cable prevents either sequence.

### CAD interference review

- Run solid interference checks with plugs and cables in both installed and
  removal positions.
- Include fastener-driver access cylinders and finger-access volumes.
- Include flex-cable swept volumes rather than modeling ribbons as zero-thickness
  lines.
- Add a minimum clearance envelope around heat sinks, moving button parts, and
  removable media.
- Check lens apertures using the actual captured image after a partial print;
  CAD line of sight alone does not prove absence of vignetting.
- Verify no screw can reach a PCB, display, cable, or battery lead if the wrong
  length is installed.

Exit gate: the selected layout has no unresolved part overlap, connector
obstruction, assembly dead-end, unsupported connector load, blocked field of
view, or unrelieved cable bend. The selection and rejected alternative are
recorded with reasons.

## Checkpoint 3 - CAD and Iterative Fit Checks

Do not print the whole enclosure until Stages A-E pass.

### Stage A - Printer and material coupons

Print and record the characterization set. Select the actual slip-fit, panel,
hole, fastener, and elephant-foot parameters for this material/profile.

Pass: duplicate coupons agree within 0.10 mm on fit-critical X/Y dimensions, or
the inconsistency is understood and the design allowances cover it.

### Stage B - Optical carrier

Print the carrier alone, preferably with replaceable camera saddles if module
variation is significant. Install all four cameras and capture a high-contrast
grid or level target near the typical 1.07 m subject distance and again farther
away.

Check:

- Sensor centers match the measured pitch within +/-0.25 mm after assembly.
- Each module seats without flex-cable force changing its position.
- Image horizons and vertical features reveal no visible roll or yaw mismatch
  caused by the carrier.
- No lens hood or aperture appears in any image corner.
- Each camera can be removed and returned to its keyed position repeatably.

Pass: mechanical measurements and image evidence are accepted before the shell
interface is added.

### Stage C - Interface slices

Print only 10-25 mm-deep sections of the highest-risk interfaces:

- One outer and one inner camera aperture plus carrier attachment
- One display corner, bezel lip, and mounting feature
- Shutter wall and travel stop
- USB-drive opening and finger relief
- Each external power-entry/strain-relief geometry
- One representative shell joint, screw boss, and captive nut or insert
- Vent/rib section if bridging or support removal is uncertain

Pass: each real component installs and can be serviced without sanding a datum
surface, loading glass, stressing a port, or damaging a cable.

### Stage D - Electronics tray

Print the tray and brackets without the outer shell. Install all electronics and
the final cables. Verify connector access, bend radii, retention, and assembly
order. Power the open tray and complete one physical-shutter and one touchscreen
capture before proceeding.

Pass: all stable camera identities enumerate, both captures make valid
four-camera sets, and moving the tray gently does not interrupt USB devices or
move a camera module.

### Stage E - Shell belt or corner prototype

Print a narrow perimeter belt or representative corners at full width and depth
to prove build-plate fit, wall stiffness, seam registration, warping behavior,
and closure alignment. If a single part approaches the 220 x 220 mm build area,
include brims/clearance and verify the sliced toolpath stays inside the printer's
usable area; split the shell if margin is poor.

Pass: the prototype is dimensionally stable, the closure operates repeatedly,
and actual measured assembled dimensions match the layout envelope.

### Stage F - Complete prototype enclosure

Print the first full shell only after A-E pass. Assemble it with all hardware,
but do not apply threadlocker or permanent adhesive. Record actual filament use,
print duration, supports, failed features, post-processing, gaps, and mass.

Classify every issue before revising:

- CAD geometry error
- Wrong measured input
- Printer/profile error
- Material/thermal behavior
- Assembly-sequence issue
- Cosmetic-only issue

Change only the parameters related to the classified failure. Reprint the
smallest representative part or slice before committing to another full shell.

Checkpoint exit gate: camera carrier, display, shutter, electronics tray, USB
media, power entries, cooling features, and closure pass physical fit checks.
The accepted revision has native CAD, STEP, 3MF, settings, measurements, and a
completed issue log.

## Checkpoint 4 - Enclosed-System Acceptance

### Mechanical and usability checks

1. Inspect for pinched cables, exposed sharp edges, loose hardware, stressed
   connectors, rattles, and fasteners that can contact electronics.
2. Open and close every service joint three times. Confirm inserts/nuts do not
   spin and no plastic cracks or delaminates.
3. Insert and remove the product USB drive ten times while watching the internal
   receptacle and cable. Neither may move or load the hub/Pi connector.
4. Apply a gentle pull and side load to each external power lead. Strain relief,
   not the electrical port, must react it.
5. Press the shutter 25 times from normal holding positions. It must not bind,
   rotate, or move the camera carrier.
6. Confirm the display remains fully visible and touch works at edges and
   corners.

### Optical checks

1. Place a level grid target near 1.07 m and capture all four views.
2. Repeat after opening/reclosing the enclosure and after normal handling.
3. Compare horizon angle, target height, camera order, aperture occlusion, and
   sensor pitch evidence with the accepted bare-carrier result.

Pass: enclosure assembly and handling introduce no visible carrier movement,
roll/yaw shift, or vignetting.

### Functional checks

1. Cold boot reaches the accepted blank/logo/application presentation.
2. All four stable camera identities enumerate and GPIO17 idles LOW.
3. One physical-shutter action produces one valid four-camera set and ordered
   GIF on the removable product drive.
4. One touchscreen action produces the same valid result.
5. Remove and reinstall the USB drive while idle, confirm automatic recovery,
   and complete another valid capture.
6. Confirm display, shutter, product USB drive, power connections, and intended
   service interfaces work without opening the enclosure.
7. Power off cleanly, restart, and confirm the application and product media are
   healthy.

### Thermal and repeated-capture checks

Test in the intended room environment with the enclosure fully closed:

1. Record ambient temperature, material, vent configuration, and open-bench Pi
   temperature for comparison.
2. Run closed for 30 minutes with the normal application displayed.
3. Perform 20 captures at a repeatable practical interval while logging Pi
   temperature, `get_throttled`, USB disconnects, capture errors, and enclosure
   observations.
4. Continue until temperature is visibly approaching a plateau; if it is still
   rising materially at the end, extend the run or revise ventilation.
5. Inspect for hot spots, plastic softening/warping, display artifacts, camera
   noise/failure, cable movement, and hub resets.

Pass: no current or historical Pi throttling bit appears during the test, no USB
or capture failure is attributable to enclosure heat or cable placement, the
temperature trend stabilizes, and no enclosure surface or printed feature shows
unsafe heat, softening, or deformation. Retain the log rather than claiming an
unmeasured thermal margin.

### Final exit gate

The assembled V1 enclosure passes mechanical, optical, functional, removable-
media, restart, and thermal checks. Retain dated photos, CAD/print revision,
dimensions, slicer/material profile, temperature log, and named capture-set
evidence. Update `PROJECT_CONTEXT.md`, `ROADMAP.md`, `CURRENT_SESSION.md`, and
`README.md` only after this evidence exists.

## Revision Decision Rules

- Reprint a coupon when the uncertainty is a fit, hole, insert, bridge, or
  material question.
- Reprint an interface slice when the uncertainty is component access or local
  geometry.
- Reprint the carrier when the uncertainty can alter camera pose or pitch.
- Reprint the tray when cable routing or board retention changes.
- Reprint a full shell only when its overall envelope, seam, stiffness, thermal
  path, or assembled interaction must be tested.
- Reject a revision immediately if it relies on a flex cable or electrical port
  as a structural member.
- Do not hide a poor fit with permanent adhesive until the accepted design has a
  documented service strategy.
- Record unresolved failures beside successes so a partial fit check cannot be
  mistaken for milestone completion.

## Suggested Working Sequence

1. Half day: photograph, label, and measure the assembled rig.
2. Half day: service the printer as needed and freeze the initial slicer profile.
3. One short print cycle: dimensional/fastener coupons and measurement.
4. One CAD session: component envelopes, two packaging layouts, and cardboard
   handling mock-up.
5. One to two short print cycles: optical carrier and corrected carrier.
6. Several small prints: display, USB, shutter, power, seam, and fastener slices.
7. One medium print: electronics tray and open-tray functional test.
8. One shell-section print: belt/corners and closure test.
9. One full prototype: assembly, issue classification, and only targeted reprints.
10. One release candidate: complete enclosed-system acceptance and documentation.

This is a gate sequence rather than a calendar commitment. A failed short coupon
should delay an expensive full print; a cosmetic imperfection that does not
affect V1 safety, function, alignment, service, or reasonable compactness need
not delay acceptance.
