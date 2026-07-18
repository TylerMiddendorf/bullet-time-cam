# Milestone 3 Plan - Aggregate Power and Safe Battery Integration

Status: closed July 18, 2026 by product-owner decision; measurement plan retired for V1

## Closure Decision

The product owner confirmed that the external battery pack is the selected V1
power solution. It supplies the Raspberry Pi and powered USB hub from separate
rated 5 V / 2 A outputs and includes its own battery-percentage display. The
owner directed that further power work be ignored because power is handled.

Accordingly, aggregate measurement, internal battery/charging integration,
fuel-gauge work, single-control power sequencing, and automatic low-battery
shutdown are no longer V1 gates. No aggregate measurements or coordinated
shutdown demonstrations were completed, so this closure records a changed
requirement rather than electrical validation.

The remainder of this document is retained as the superseded measurement and
integration plan in case the requirement is reopened for a later revision.

## Original Outcome - Retired

Measure the complete final V1 bench chain electrically, use that evidence to set
a runtime target and power budget, then select and validate battery, regulation,
USB-C charging, monitoring, orderly shutdown, and final load cutoff. Software
resource counters and USB descriptor maxima are not electrical measurements.

## Checkpoint 1 - Measurement Boundary and Instrument

Before connecting an instrument:

1. Draw the present bench power tree and identify every source feeding the
   Raspberry Pi, 800x480 display/backlight and touch controller, final hubs,
   four camera nodes, removable product USB drive, and trigger circuitry.
2. Prefer one regulated source and one inline logger around the complete load.
   If the current bench wiring has independent rails that cannot safely be
   combined, measure every rail over the same scripted state sequence and state
   explicitly that the aggregate is reconstructed rather than simultaneous.
3. Record instrument make/model, serial if available, calibration status,
   voltage and current range, resolution, sampling/logging rate, burden voltage,
   connection point, cable, and connector ratings.
4. Confirm the instrument and wiring are rated above the source voltage and
   expected current with margin. Add current limiting and polarity verification
   before energizing the rig. Do not route load current through an unfused
   low-current multimeter input.
5. Record source voltage both before the test and at the load during the highest
   observed demand.

Exit gate:

- The measurement boundary contains every V1 load or names every separately
  measured rail, and the instrument can log voltage/current/power fast enough
  to distinguish idle, capture, transfer, processing, and review.

## Checkpoint 2 - Repeatable Electrical Workload

Use the deployed app and final hub/cabling/product USB chain. Before each run,
record revision, boot ID, app/firmware versions, service state, GPIO17 LOW, all
four stable camera identities, product-drive identity/mount, display brightness,
and Pi `get_throttled` state.

Measure and timestamp:

1. Power-off/source baseline and instrument zero.
2. Cold boot through logo and ready screen.
3. Stable ready/idle for at least 60 seconds.
4. One actual touchscreen/GPIO17 four-camera capture through loading, USB
   transfer, GIF processing, product-drive commit, and animated review.
5. Animated review for at least 30 seconds.
6. At least ten repeated captures at the normal rearm interval, retaining the
   capture IDs and app timestamps needed to align electrical samples with
   capture stages.
7. Orderly application/system shutdown if the present bench source permits it;
   do not cut power to a running Raspberry Pi merely to complete this row.

Retain raw timestamped samples. Report voltage, current, and power for each
state using stable idle mean/median, capture mean, observed maximum, duration,
and energy per complete capture where the instrument supports integration.
Record minimum load voltage and any undervoltage/throttling indication.

Exit gate:

- Raw logs support a reproducible complete-system idle value, representative
  capture/processing energy, and observed peak demand with no hidden load or
  estimated descriptor substituted for a measurement.

## Checkpoint 3 - Power Budget and Runtime Requirement

After the electrical evidence exists:

1. Set an explicit user runtime or captures-per-charge target with the product
   owner.
2. Add conversion, battery-discharge, temperature, aging, and reserve margins;
   keep measured load separate from engineering margins.
3. Define continuous and transient regulator ratings, required output rails,
   allowable voltage droop, thermal limits, and quiescent/off-state behavior.
4. Compare the Raspberry Pi candidate and installed hubs against the measured
   budget before treating them as final production selections.

Exit gate:

- A traceable energy/power budget and confirmed runtime requirement exist before
  any battery or regulator purchase.

## Checkpoint 4 - Battery, Charging, Monitoring, and Safe Cutoff

Select and bench-validate the power subsystem against the measured budget:

- Internal rechargeable battery with protected cells
- Mandatory USB-C charging; operation while charging is not required
- Regulation sized for continuous and transient demand
- Fuel/voltage monitoring with an orderly low-battery threshold above brownout
- One user-facing power control
- Hardware supervisor/controller that requests Raspberry Pi shutdown, waits for
  completion, stops camera nodes, and only then disconnects the load
- Fail-safe timeout and recovery behavior that never makes routine shutdown an
  uncontrolled Raspberry Pi power cut

The detailed electrical design, component choice, and destructive/fault test
procedure must be reviewed after Checkpoints 1-3. No purchase is authorized by
this planning document alone.

## Current Instrumentation Finding - July 18, 2026

Read-only Pi inventory at revision `8fd1f17` found no Linux `power_supply`
entries, no `hwmon` voltage/current/power inputs, and no USB device identifiable
as a power meter. The two exposed I2C controllers have no repository-defined
power monitor. `vcgencmd get_throttled` returned `0x0`, which only shows that the
Pi reported no current/historical throttling flags; it does not measure
aggregate electrical demand. A suitable external inline instrument and the
physical power-tree mapping are therefore required to begin Checkpoint 1.
