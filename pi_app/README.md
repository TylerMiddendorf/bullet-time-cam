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
