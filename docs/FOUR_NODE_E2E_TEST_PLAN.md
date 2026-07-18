# Four-Node V1 End-to-End Acceptance Tests

## Purpose

This is the executable acceptance gate for Milestone 1 Checkpoints 5-7. It verifies persisted JPEG/GIF bytes and stable camera identities after real hardware scenarios; a successful process exit or a plausible UI screen is not sufficient evidence.

The repository has two layers:

- `pi_app/tests/test_e2e_validation.py` exercises the evidence validator deterministically, including corrupt/truncated files and cross-capture transaction reuse.
- `pi_app/tests/e2e/test_four_node_hardware.py` validates the capture sets and scenario ledger produced by the physical rig. It is skipped unless live evidence paths are supplied.

The live suite is an acceptance target for the four-node product coordinator. Its existence does not mark Checkpoint 5 complete: the current checked-in application must first be extended from its one-node workflow to write the four-camera manifest contract below.

## Persisted Capture Contract

Every tested capture directory must contain `manifest.json`, every successfully received `camera_0N.jpg`, and `bullet_time.gif` whenever at least two views succeeded. No `.part` file may remain.

The four-node manifest extends the one-node schema with:

- `capture_id` matching the directory name
- `status`: `complete` or `partial`
- exactly four `cameras` records containing `logical_camera_id` and `status`
- successful camera records containing stable `node_uid`, `boot_id`, and `capture_seq`
- one `files` record per committed original with `role`, `logical_camera_id`, byte count, and CRC32
- one animation record with `role: animation`, `path: bullet_time.gif`, byte count, CRC32, frame count, and the logical `camera_sequence` when two or more images succeeded; a complete set uses `1,2,3,4,3,2`
- one camera-specific `errors` record for every failed camera

The validator decodes every JPEG and GIF, recomputes every original's byte count and CRC32, checks the stable UID mapping, and rejects duplicate node transactions assigned to different capture sets.

## Live Scenario Sequence

Use a fresh evidence directory on the removable USB drive and retain the application logs and final ledger alongside it.

1. **Normal reliability:** Make at least 25 four-camera captures. Include both the physical shutter and normal touchscreen/GPIO17 path. Every set must contain Cameras 1-4, four originals, one GIF, no errors, and no partial file.
2. **Each camera missing:** Disconnect Camera 1, capture once, reconnect and confirm its stable identity; repeat separately for Cameras 2, 3, and 4. Each result must preserve the other three originals, generate a usable GIF, and identify only the disconnected logical camera.
3. **Corrupt transfer:** Use the inert-until-commanded firmware fault hook on one selected node. The bad image must be NACKed and omitted, the other three originals and partial GIF must remain usable, and the next ordinary capture must recover.
4. **Truncated transfer:** Interrupt one selected node after its transfer begins. No truncated JPEG or `.part` file may be committed. The other three views must remain usable and the app must recover without a Pi reboot.
5. **Node reboot:** Record a complete capture, reboot one camera node, then record another complete capture. Its `node_uid` and logical camera number must remain unchanged while its `boot_id` changes.
6. **Set isolation:** Across all scenarios, no `(node_uid, boot_id, capture_seq)` transaction may appear in more than one capture set. No original may be assigned to the wrong set, and no test capture ID may be reused for two scenarios.
7. **UI behavior:** The touchscreen enters `LOADING` on the first capture-start event, remains there while progress continues, shows the complete or partial GIF without desktop interaction, and identifies camera-specific failures. Film or photograph representative normal and partial cases because the artifact validator cannot prove emitted photons.

Do not deliberately unplug shared power or disturb the trigger wiring during a fault case. Disconnect only the selected camera's USB data connection after the current set has closed, except for the explicitly controlled truncated-transfer case.

For the controlled truncated-transfer case, run one bounded normal hardware capture with `--truncate-camera-id N`. This test-only host hook is inert by default and closes only the selected live serial stream after at least 64 KiB of its IMAGE payload has arrived. Retain the emitted byte-progress message, require the selected camera's manifest error code to be `transfer_truncated`, verify that no selected-camera JPEG or `.part` file was committed, then run an ordinary capture without the option to prove recovery.

## Scenario Ledger

Copy `pi_app/tests/fixtures/four_node_e2e_ledger.example.json` into the live evidence directory and replace every placeholder with the actual capture ID, assigned UID, and selected failed camera. Record the expected camera-specific error code and a subsequent complete recovery capture for both corrupt and truncated transfer cases. The 25 normal IDs and all fault, recovery, and reboot IDs must be distinct.

Run the artifact validator on the Raspberry Pi:

```bash
cd /home/username/bullet-time-cam
python3 -m pi_app.tools.validate_four_node_e2e \
  --capture-root '/media/username/USB DISK/BulletTime' \
  --ledger '/path/to/four-node-e2e-ledger.json'
```

Or run the environment-gated unittest:

```bash
cd /home/username/bullet-time-cam
FOUR_NODE_E2E_CAPTURE_ROOT='/media/username/USB DISK/BulletTime' \
FOUR_NODE_E2E_LEDGER='/path/to/four-node-e2e-ledger.json' \
python3 -m unittest pi_app.tests.e2e.test_four_node_hardware -v
```

## Exit Evidence

Retain:

- the completed scenario ledger
- validator JSON showing `status: pass`
- all named capture directories and manifests
- application/service logs spanning the run
- UI images/video for normal loading/review and a camera-specific partial result
- timing summary with median, slowest, and failure count
- explicit notes for any limitation or rerun

Only the live hardware result can satisfy the Checkpoint 5/7 gate. The deterministic local suite proves the validator itself and remains part of every normal application test run.
