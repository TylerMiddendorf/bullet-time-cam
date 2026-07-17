# Raspberry Pi Checkpoint 4 Application

This application receives one camera node's framed JPEG stream over USB CDC, validates and atomically preserves the original on removable USB storage, records timing/resource evidence, and displays the result on the Raspberry Pi touchscreen. Normal touchscreen capture pulses Raspberry Pi BCM GPIO17 high for 100 ms; the approved 2N3904 stage converts that into an active-low pulse on the shared camera trigger bus.

Run tests from the repository root:

```bash
python3 -m unittest discover -s pi_app/tests -v
```

The normal local run currently passes 23 tests and skips one environment-gated physical-rig test. The E2E evidence validator checks at least 25 normal four-camera sets, one disconnect per camera, corrupt and truncated transfers, stable identity across a node reboot, JPEG/GIF integrity, leftover partial files, and cross-capture transaction isolation. Follow [`docs/FOUR_NODE_E2E_TEST_PLAN.md`](../docs/FOUR_NODE_E2E_TEST_PLAN.md) to collect the live ledger and enable the hardware test after the four-node coordinator is implemented.

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
  "auto_mount": true
}
```

The repository configuration prefers the added drive's `USB DISK` mount-directory name (normally derived from its label below `/media/<user>/`). This is a preference rather than a hard requirement, so another writable USB drive can still be selected if that drive is absent. With no preference, the application selects deterministically by mount path. Each capture manifest records the selected device, filesystem, mountpoint, and capture root.

Do not remove the drive while the loading screen is active. Missing/unplugged-drive handling is implemented, but actual-drive tests for full, read-only, corrupt, and removal-during-write cases remain part of the removable-media milestone.

GPIO17 is claimed as an output LOW before the receiver starts, remains LOW while idle, and is returned LOW during pulse-error and application-shutdown cleanup. The backend is the Raspberry Pi OS Trixie `python3-lgpio` package pinned in `system-requirements.txt`. Do not connect GPIO17 directly to the trigger bus; follow [`docs/TRIGGER_CIRCUIT.md`](../docs/TRIGGER_CIRCUIT.md). The product owner reports that its complete unpowered multimeter checklist passes.

`--trigger-once` and `--trigger-count N` use hardware pulses. The legacy USB command remains only as explicit test scaffolding: add `--diagnostic-usb-trigger` to one of those options when a diagnostic `CAPTURE_REQUEST` is specifically intended. Never use both paths for one capture action.

## Product Boot Experience

The camera boot path suppresses Raspberry Pi firmware artwork, Plymouth, cursors, systemd/udev status, and the completed Raspberry Pi Imager cloud-init stages. Hardware trials showed that this exact Raspberry Pi OS Trixie/kernel build does not reach userspace when every virtual-terminal console is removed, so one `tty1` console is retained but silenced with kernel/udev log level 0, `quiet`, hidden status, a hidden cursor, and a masked getty. A dedicated LightDM/labwc camera session does not merge Raspberry Pi's system desktop autostart, so the panel and file-manager desktop never launch. It loads a transparent compositor cursor theme before showing `assets/Logo_800x480.png` as the background, then launches the camera service as soon as the graphical session exists; the application renders the same logo as its first full-screen frame and independently hides its Tk cursor. Both custom Plymouth and Raspberry Pi's initramfs early-fullscreen-logo path prevented normal startup during hardware trials, and a later clean initramfs regeneration also prevented userspace startup. The installer therefore removes the early-logo integration and sets `auto_initramfs=0` so this product image boots the kernel directly.

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
