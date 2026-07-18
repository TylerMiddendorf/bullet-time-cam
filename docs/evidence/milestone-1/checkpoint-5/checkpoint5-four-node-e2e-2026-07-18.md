# Milestone 1 Four-Node End-to-End Evidence

Date: July 18, 2026

Status: Checkpoints 5, 6, and 7 hardware acceptance complete. The complete
four-node path is reliable, but its measured 3.25-second median remains above
the soft two-second shutter-to-review target.

## Validated system

- Raspberry Pi checkout and `origin/main`: `710eadd`
- Camera firmware: 0.2.3 on all four XIAO ESP32S3 Sense nodes
- Firmware application SHA-256:
  `7c6397322666c8965f808ad0bb380a90c15cefe25fb9e87c96252bb56962ef3a`
- Firmware build: 371,441 flash bytes and 33,368 dynamic-memory bytes
- Capture storage: `/dev/sda1`, mounted at `/media/username/USB DISK`, with
  capture sets under `BulletTime/`
- Logical identity map:

  | Camera | Stable UID |
  | --- | --- |
  | 1 | `E072A1F9B3E4` |
  | 2 | `E072A1F9A190` |
  | 3 | `E072A1F99CC0` |
  | 4 | `E072A1F99CF8` |

Every qualifying artifact was validated from persisted bytes rather than from
process exit status. The validator decoded every original and GIF, recomputed
lengths and CRC32 values, checked the `1,2,3,4,3,2` animation order, rejected
leftover partial files and duplicate node transactions, and verified the stable
logical mapping. The completed scenario ledger is
[`four-node-e2e-ledger.json`](four-node-e2e-ledger.json), and the retained
validator output is [`validator-result.json`](validator-result.json).

## Normal reliability and timing

The qualifying reliability run produced 25/25 complete capture sets: 100
original JPEGs, 25 six-frame GIFs (150 decoded frames), zero failed cameras,
zero leftover `.part` files, and 100 unique node transactions. Capture IDs are
listed in the ledger, and the raw application output is
[`normal-25-final.log`](normal-25-final.log).

Capture-set completion time from the first node's `CAPTURE_STARTED` event was:

- minimum: 3,201.312 ms
- median: 3,250.161 ms
- maximum: 3,288.951 ms
- complete-set failure count: 0/25

The batch was initiated through normal GPIO17 hardware pulses. Separate
byte-valid product captures proved both user trigger sources:

- physical shared shutter: `20260718T051907Z_50cdc484`
- normal touchscreen/GPIO17 action: `20260718T052128Z_0f21e734`

The physical evidence confirms reliable product behavior but not the soft
two-second target. Acquisition and concurrent USB transfer remain the dominant
latency stages; later optimization must not be represented as already complete.

## Required fault and recovery scenarios

### Data-only camera disconnects

Each selected board remained powered and connected to the shared trigger while
its serial data path was made unavailable. Every result preserved the other
three originals, created a usable GIF, and named only the expected camera:

- Camera 1: `20260718T045407Z_6fe06643`
- Camera 2: `20260718T045453Z_32453977`
- Camera 3: `20260718T045549Z_7dc8b5c8`
- Camera 4: `20260718T045238Z_a397622e`

A literal Camera 4 USB power unplug was rejected as qualifying evidence because
the unpowered board clamped the shared trigger. Controlled exclusive serial
access was used for the data-only cases so the camera stayed powered and the
trigger topology remained valid. Diagnostic capture
`20260718T043028Z_737247ae` demonstrated the corrected behavior but is not used
in the final ledger.

### Corrupt transfer

- qualifying fault: `20260718T050440Z_8083cd05`
- failed camera: Camera 1
- typed error: `jpeg_checksum_mismatch`
- complete recovery: `20260718T050503Z_ebe7c7e6`

The first attempted corruption scenario, `20260718T050343Z_5d5e9424`, also
timed out Camera 2 and was rejected. Capture `20260718T050419Z_49b6f04d`
confirmed recovery before the qualifying single-fault rerun.

### Truncated transfer

- qualifying fault: `20260718T051511Z_b5eecd65`
- failed camera: Camera 1
- typed error: `transfer_truncated`
- stream closed at 65,536 of 498,023 payload bytes
- complete recovery without Pi or node reboot: `20260718T051549Z_b662dd29`

No Camera 1 JPEG or `.part` file was published for the truncated transaction.
The host-side truncation hook is inert unless `--truncate-camera-id` is supplied
and is not present in the product service command.

### Reboot identity

- before reboot: `20260718T050531Z_cb98370e`
- after reboot: `20260718T050615Z_35b94d04`
- Camera 4 UID: `E072A1F99CF8` before and after
- boot ID: `2302327597` before, `2564730693` after

The UID-to-Camera-4 mapping remained stable while the boot ID changed.

## Touchscreen evidence and defect found

The normal review photograph is
[`ui-normal-review-20260718.jpeg`](ui-normal-review-20260718.jpeg). A controlled
Camera 4 unavailability initially exposed a real presentation defect: the
camera-specific partial-result message was replaced by a later generic serial
retry error. The pre-fix screen is retained as
[`ui-partial-reconnect-overlay-before-fix-20260718.jpeg`](ui-partial-reconnect-overlay-before-fix-20260718.jpeg).

Commit `710eadd` makes the presentation state retain the current review message
and color while background reconnect attempts continue. The product owner then
confirmed the corrected emitted screen in
[`ui-partial-review-20260718.jpeg`](ui-partial-review-20260718.jpeg). Its saved
capture, `20260718T053522Z_f906ef32`, was independently validated as a partial
GPIO17 capture with successful Cameras 1-3 and failed Camera 4.

## Automated acceptance and postflight

- Normal local suite: 68 tests discovered, with 67 passing and the
  environment-gated live test skipped when evidence paths are absent.
- Environment-gated physical-rig suite:
  `test_required_live_scenarios_and_persisted_artifacts ... ok` (37.888 s).
- Direct validator: 35 named captures checked, including 25 normal captures and
  six partial captures; status `pass`.
- Camera 4 post-test smoke: camera ready at 2048x1536 JPEG, BTC1 UID
  `E072A1F99CF8`, and shared-trigger ready; firmware 0.2.3.
- Final Pi state: `bullet-time-ui.service` active, temporary Camera 4 lock
  inactive, GPIO17 configured as output LOW.

The first local SSH wrapper around the final 25-capture batch reached its own
timeout while the bounded Pi process continued normally. Completion was judged
from the finished Pi log, all 25 persisted capture directories, and the byte
validator—not from that wrapper's exit status.
