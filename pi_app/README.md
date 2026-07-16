# Raspberry Pi Checkpoint 4 Application

This application receives one camera node's framed JPEG stream over USB CDC, validates and atomically preserves the original, records timing/resource evidence, and displays the result on the Raspberry Pi touchscreen.

Run tests from the repository root:

```bash
python3 -m unittest discover -s pi_app/tests -v
```

Run the application:

```bash
python3 -m pi_app.bullettime.main --config pi_app/config.json
```

Use `--headless` for receiver/storage testing without the fullscreen UI. The application searches `/dev/serial/by-id`, `/dev/ttyACM*`, and `/dev/ttyUSB*`; the node UID in the protocol, not the Linux device number, controls logical camera identity.

## Product Boot Experience

The camera boot path uses the same `assets/Logo_800x480.png` at three handoff points: Raspberry Pi early boot, a static Plymouth theme, and the application's first full-screen frame. A minimal labwc autostart omits the desktop panel and file-manager desktop, uses the logo as the compositor background, and launches the camera service as soon as the graphical session exists.

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
