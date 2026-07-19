# Raspberry Pi Bullet-Time Application

This application receives framed JPEG streams over USB CDC, validates and atomically preserves originals on removable USB storage, records timing/resource evidence, and displays results on the Raspberry Pi touchscreen. The product coordinator groups all four registered nodes into one atomic capture set and ordered GIF while preserving usable partial sets with camera-specific errors. Normal touchscreen capture pulses Raspberry Pi BCM GPIO17 high for 100 ms; the approved 2N3904 stage converts that into an active-low pulse on the shared camera trigger bus.

Runtime responsibilities are split across focused modules under
`pi_app/bullettime/`: `main.py` owns CLI/configuration, `receiver.py` owns serial
transactions, `ui.py` owns the headless entry point and Qt migration shim,
`qt_ui.py` bridges queue events into Qt Quick, `ui_model.py` reduces workflow
state, and `media_catalog.py` reads published USB capture sets and performs
guarded, confirmed whole-set deletion. Protocol, GPIO, capture control, storage,
discovery, and metrics remain
separate modules.

Run tests from the repository root:

```bash
python3 -m unittest discover -s pi_app/tests -v
```

The normal local run currently discovers 118 tests: 117 pass and one
environment-gated physical-rig test is skipped until a live ledger is supplied.
Coverage includes Qt state/routes, detached playback, historical USB catalog
browsing and deletion, corrupt and removed catalog entries, grouping, persistence,
protocol, GPIO, and evidence validation.

Run the application:

```bash
python3 -m pi_app.bullettime.main --config pi_app/config.json
```

Use `--headless` for receiver/storage testing without the fullscreen UI. The application searches `/dev/serial/by-id`, `/dev/ttyACM*`, and `/dev/ttyUSB*`; the node UID in the protocol, not the Linux device number, controls logical camera identity.

## Removable USB Storage

Insert a writable USB mass-storage drive before capturing. For every commit, the application reads Linux mount information and sysfs, accepts only filesystems backed by an actual USB block device, and writes the capture set below `BulletTime/` on that drive. If no suitable filesystem is mounted, it asks `udisks2` to mount detected USB media and rescans. The product installer includes `udisks2`.

The application deliberately does not fall back to the Raspberry Pi boot microSD. A touchscreen capture is blocked with a visible error when USB storage is unavailable. If a physical shutter capture arrives while storage is unavailable, the Pi sends a NACK and does not commit the JPEG internally.

Storage behavior is configured in `pi_app/config.json`:

```json
"usb_storage": {
  "capture_directory": "BulletTime",
  "preferred_mount_name": "USB DISK",
  "auto_mount": true,
  "stale_staging_seconds": 3600
}
```

The repository configuration prefers the added drive's `USB DISK` mount-directory name (normally derived from its label below `/media/<user>/`). This is a preference rather than a hard requirement, so another writable USB drive can still be selected if that drive is absent. With no preference, the application selects deterministically by mount path. Each capture manifest records the selected device, filesystem, mountpoint, and capture root.

Do not remove the drive while the loading screen is active during normal use.
Deleting a library item requires confirmation and permanently removes that
capture set's original JPEGs, animation GIF, and manifest together. The delete
path revalidates that the set is published directly below the active removable
USB capture root; it cannot target the Pi boot card or arbitrary paths.
The real-drive qualification covers missing, full, read-only,
corrupt/unmountable, and removal-during-write behavior. Storage failures use
bounded actionable touchscreen messages while full details remain in the
service journal. Capture staging directories with the exact generated naming
form are removed when they are older than the configured threshold; fresh and
unrelated `.part` content is retained. See the completed
[`Milestone 2 plan`](../docs/MILESTONE_2_PLAN.md) and its linked evidence.

GPIO17 is claimed as an output LOW before the receiver starts, remains LOW while idle, and is returned LOW during pulse-error and application-shutdown cleanup. The backend is the Raspberry Pi OS Trixie `python3-lgpio` package pinned in `system-requirements.txt`. Do not connect GPIO17 directly to the trigger bus; follow [`docs/TRIGGER_CIRCUIT.md`](../docs/TRIGGER_CIRCUIT.md). The product owner reports that its complete unpowered multimeter checklist passes.

`--trigger-once` and `--trigger-count N` use hardware pulses. The legacy USB command remains only as explicit test scaffolding: add `--diagnostic-usb-trigger` to one of those options when a diagnostic `CAPTURE_REQUEST` is specifically intended. Never use both paths for one capture action.

The live fault suite also provides inert-by-default test scaffolding. `--corrupt-next-payload` arms the selected firmware corruption hook, while `--truncate-camera-id N` closes Camera N's host serial stream after at least 64 KiB of its IMAGE payload has arrived. The latter must produce a typed `transfer_truncated` partial set without committing truncated bytes or `.part` files. Neither option belongs in the product service command.

## Product Boot Experience

The camera boot path suppresses Raspberry Pi firmware artwork, Plymouth,
cursors, systemd/udev status, and completed cloud-init stages. The dedicated
labwc session shows `assets/Logo_800x480.png`, then starts Qt with
`QT_QPA_PLATFORM=wayland`. The receiver starts only after Qt swaps its first
matching logo frame. Tk/X11 remain installed solely as a rollback path.

Install from the Git checkout on the Raspberry Pi:

```bash
cd /home/username/bullet-time-cam
sudo pi_app/scripts/install_boot_experience.sh
sudo reboot
```

After reconnecting over SSH, verify the persistent configuration and running service:

```bash
cd /home/username/bullet-time-cam
pi_app/scripts/verify_boot_experience.sh
```

The installer keeps timestamped copies of the previous boot and session files under `/var/lib/bullet-time-boot-backups/`. HDMI console output and the TTY1 login prompt are suppressed, while SSH and the serial console remain available for recovery.

For a fresh card, exact validated software baseline, camera-identity setup, installer ownership, rejected alternatives, visual acceptance test, rollback, and offline SD-card recovery, follow [`docs/RASPBERRY_PI_BOOT_RUNBOOK.md`](../docs/RASPBERRY_PI_BOOT_RUNBOOK.md).
