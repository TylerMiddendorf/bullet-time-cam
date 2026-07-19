# Raspberry Pi Product-Boot Runbook

This runbook reproduces the visually accepted Raspberry Pi boot state for the Bullet-Time camera. It covers a fresh Pi, verification, recovery, and the hardware-specific decisions behind the configuration.

## Accepted Result

On the validated Raspberry Pi 4 and 800x480 HDMI touchscreen, a normal cold boot now behaves as follows:

1. The display remains blank/black during the early firmware and kernel phase.
2. `assets/Logo_800x480.png` fills the display as soon as the dedicated graphical session starts.
3. The application owns the same logo as its first full-screen frame, avoiding a desktop-colored handoff.
4. The application transitions directly to the camera interface.

No Raspberry Pi rainbow artwork, boot log, filesystem status, cloud-init stage text, login prompt, panel, file-manager desktop, loading diagnostic, or pointer is visible. The product owner visually accepted this sequence on July 17, 2026.

This is intentionally a black-to-logo-to-app sequence, not a logo-throughout-kernel-boot sequence. On the validated OS/kernel, both tested early-logo mechanisms prevented the Pi from reaching userspace. Reliability and the absence of visible operating-system content take priority over an earlier logo.

## Proven Baseline

| Component | Validated value |
| --- | --- |
| Board | Raspberry Pi 4 Model B Rev 1.1, 2 GB |
| Display | 800x480 HDMI video with USB touch |
| Image | Raspberry Pi reference `2026-06-18`, `pi-gen` stage 4 |
| OS | Debian 13.5 (Trixie), 64-bit Raspberry Pi OS desktop stack |
| Kernel | `6.18.34+rpt-rpi-v8` |
| Display manager | LightDM `1.32.0-6+rpt2` |
| Compositor | labwc `0.9.7-1+rpt1` |
| Python | 3.13.5 |
| Logo | `assets/Logo_800x480.png` |
| Validated source | commit `0068220807824f11923a5fdb4d361d90094036fc` plus subsequent runbook/installer hardening |
| Final visual boot ID | `3b377b08-599e-434e-bc40-948f24710254` |

The visually accepted boot used labwc 0.9.7. During the later reproducibility audit, Debian offered labwc 0.9.8; the upgraded live Pi cold-booted successfully as boot ID `a067e50f-99de-4080-b2fa-3198eec8e80a`, passed all 28 expanded checks, ran only the four intended session processes, and emitted no cloud-init stage messages. The installer now uses `apt-get install --no-upgrade` so rerunning it does not silently replace desktop/session packages already supplied by the selected image.

Use the same Raspberry Pi OS desktop image when exact reproducibility is more important than upgrading. If a later image or kernel is used, treat the first cold boot as a new hardware validation; do not assume its initramfs, Plymouth, console, or compositor behavior is identical.

## Fresh-Pi Installation

### 1. Image and provision the card

Use Raspberry Pi Imager to install a 64-bit Raspberry Pi OS image with the desktop stack. Do not use Raspberry Pi OS Lite for this procedure.

In Imager, configure:

- A non-root username and password
- Hostname, Wi-Fi country, network, locale, and time zone
- SSH with key authentication when remote recovery is desired

The username may differ from the validated bench username. The installer derives the application user and home directory from the account that invokes `sudo`.

Insert the card, connect HDMI and USB touch, and allow the Pi to complete one ordinary first boot. Confirm that networking, SSH, and touch work before changing the product-boot path.

### 2. Clone to the required stable path

The checked-in systemd service uses `%h/bullet-time-cam`, so the checkout location is part of the deployment contract:

```bash
sudo apt-get update
sudo apt-get install -y git
cd "${HOME}"
git clone https://github.com/TylerMiddendorf/bullet-time-cam.git
cd "${HOME}/bullet-time-cam"
git switch main
```

Do not rename the checkout. The installer refuses a different location instead of creating a service that will fail later.

### 3. Configure stable camera identities

Confirm `pi_app/config.json` before installation. `logical_cameras` maps each
stable eFuse UID to a logical camera number. The validated four-node rig uses:

```json
"logical_cameras": {
  "E072A1F9B3E4": 1,
  "E072A1F9A190": 2,
  "E072A1F99CC0": 3,
  "E072A1F99CF8": 4
}
```

If a replacement rig uses different boards, update all four entries from
verified startup output before installation. A four-node rig must contain four
unique UID-to-camera mappings. Linux names such as `/dev/ttyACM0` are
deliberately not used as identity.

### 4. Run the product-boot installer

Run the installer from the intended desktop/application account:

```bash
cd "${HOME}/bullet-time-cam"
sudo ./pi_app/scripts/install_boot_experience.sh
sudo reboot
```

The installer is idempotent and creates a new timestamped backup before every run. It also installs the Python runtime and pinned `pi_app/requirements.txt` dependencies under `${HOME}/esp32cam-tools`. Existing image packages are not upgraded as a side effect of installation.

### 5. Verify after reboot

Reconnect through SSH and run:

```bash
cd "${HOME}/bullet-time-cam"
./pi_app/scripts/verify_boot_experience.sh
```

All checks must report `PASS`. Also perform one physical cold-boot
observation. The automated checks prove configuration and process state; only a
person or recorded video proves that no transient frame was visible.

Expected live processes are:

- `labwc --config-dir ~/.config/bullet-time-labwc`
- `swaybg` displaying `assets/Logo_800x480.png`
- the Python camera application
- the Qt Quick application using the native Wayland platform plugin

`wf-panel-pi`, `pcmanfm`, and other Raspberry Pi desktop components must not be
running. Xwayland and Tk remain installed as rollback dependencies but are not
required by the Qt runtime. `bullet-time-ui.service` is expected to be active
but disabled.

## What the Installer Owns

`pi_app/scripts/install_boot_experience.sh` performs all persistent changes needed for the accepted state:

- Verifies that it is running on a Raspberry Pi from `${HOME}/bullet-time-cam` via `sudo` from the intended user.
- Backs up boot, LightDM, labwc, and user-service files under `/var/lib/bullet-time-boot-backups/<UTC timestamp>/`.
- Installs the session prerequisites, Debian PySide6/Qt Quick and Qt Wayland
  packages, the Python virtual environment, and pinned application packages;
  Tk/X11 remain available for rollback.
- Adds the application user to `dialout`, `input`, `render`, and `video` where those groups exist.
- Retires Raspberry Pi Imager's completed NoCloud/cloud-init datasource and creates `/etc/cloud/cloud-init.disabled`.
- Removes `rpi-splash-screen-support`, its initramfs hook, and its TGA payload if present.
- Restores the distro `pix` Plymouth theme as a safe package default but disables Plymouth for product boot.
- Sets a single-line kernel command line containing the quiet, zero-log-level, hidden-status, hidden-cursor, retained-`tty1`, and `cloud-init=disabled` options.
- Sets `auto_initramfs=0` and `disable_splash=1` in `/boot/firmware/config.txt`.
- Does **not** regenerate initramfs; a freshly regenerated initramfs prevented this hardware from reaching userspace.
- Installs the `bullet-time` Wayland session and configures immediate LightDM autologin to it.
- Uses an isolated labwc configuration directory so Raspberry Pi's panel and desktop autostart are never merged.
- Creates a transparent Xcursor theme before labwc starts any visible client.
- Starts the logo background first, then the camera user service.
- Masks the HDMI `tty1` getty and automatic virtual-terminal login prompt while preserving serial-console and SSH recovery.

The application separately forces a blank Qt cursor and renders the same logo
as its first native Wayland frame before starting the receiver. The compositor
theme is still required because labwc and the logo background exist before Qt.

## Final Boot Decisions

| Decision | Reason and evidence |
| --- | --- |
| Retain `console=tty1` | Every console-less trial remained black and never reached networking. The otherwise identical `tty1` boot repeatedly succeeded. The console is retained but silenced and has no getty. |
| Disable firmware splash | `disable_splash=1` removes Raspberry Pi firmware artwork. |
| Disable Plymouth | A custom static Plymouth script theme crashed Plymouth 24.004.60 in `libply-splash-core`/`libply` and exposed a backtrace. |
| Reject Raspberry Pi's early fullscreen-logo helper | The helper's TGA/initramfs path produced a blank display and never reached networking. |
| Boot without initramfs | Regenerating an already-clean initramfs again prevented userspace startup. `auto_initramfs=0` restored reliable direct-kernel boot and reduced kernel startup time. |
| Disable cloud-init after provisioning | Raspberry Pi Imager's NoCloud service printed `Completed socket interaction for boot stage local/network` directly to `/dev/console` on every boot. Provisioning was already complete. |
| Use a dedicated labwc session | The normal Raspberry Pi desktop session starts panel and file-manager desktop components and can expose OS chrome during handoff. |
| Use logo in compositor and application | Matching images prevent a desktop-colored or blank frame between graphical-session startup and Tk mapping. |
| Use a transparent compositor cursor theme | Tk's `cursor=none` begins too late to hide labwc's pointer over the background logo. |
| Keep SSH and serial recovery | Display silence must not remove non-display diagnostic paths. |

## Recovery and Rollback

### Restore the most recent installer backup

List backups:

```bash
sudo ls -1dt /var/lib/bullet-time-boot-backups/*
```

Choose the intended timestamp and restore the boot and LightDM files:

```bash
BACKUP=/var/lib/bullet-time-boot-backups/YYYYMMDDTHHMMSSZ
sudo install -m 0644 "${BACKUP}/cmdline.txt" /boot/firmware/cmdline.txt
sudo install -m 0644 "${BACKUP}/config.txt" /boot/firmware/config.txt
sudo install -m 0644 "${BACKUP}/lightdm.conf" /etc/lightdm/lightdm.conf
```

Restore optional user files only when they exist in that backup. If they do not exist, they were newly created by the installer and can be removed when a complete rollback is desired:

```bash
sudo systemctl unmask getty@tty1.service autovt@tty1.service
sudo rm -f /usr/local/bin/bullet-time-session
sudo rm -f /usr/share/wayland-sessions/bullet-time.desktop
sudo rm -rf /usr/share/icons/BulletTimeInvisible
sudo reboot
```

Do not restore or remove cloud-init casually after the device has been provisioned. Re-enabling it can reapply stale Imager data. If it must be restored for reprovisioning, remove both `/etc/cloud/cloud-init.disabled` and `cloud-init=disabled`, then validate networking and identity settings again.

### Recover a black/offline Pi from another computer

1. Power the Pi off; do not remove a powered SD card.
2. Insert the boot card into another computer and back up `cmdline.txt` and `config.txt` before editing.
3. Keep `cmdline.txt` on one physical line.
4. Ensure it contains `console=tty1`, `quiet`, `plymouth.enable=0`, `rd.plymouth=0`, `loglevel=0`, `systemd.show_status=false`, `udev.log_level=0`, and `cloud-init=disabled`.
5. Remove any `fullscreen_logo=1`, `fullscreen_logo_name=...`, standalone `splash`, or `ds=nocloud...` token.
6. Ensure `config.txt` contains `auto_initramfs=0` and `disable_splash=1` in an active `[all]` section.
7. Safely eject the card, reinstall it, and boot.

Never replace the whole command line with an example from another card: the `root=PARTUUID=...`, Wi-Fi country, and serial-console values are installation-specific.

## Upgrade Discipline

- Keep a boot-card image or known-good backup before changing the kernel, Raspberry Pi firmware, LightDM, labwc, Plymouth, or initramfs packages.
- Do not run `update-initramfs` or enable either rejected splash mechanism on the only working product card.
- After an OS or kernel upgrade, rerun the verifier and film a complete cold boot before accepting the update.
- Preserve the serial console and SSH path until the upgraded image has passed physical boot validation.
- Treat a source update as deployed only after the Pi checkout is pulled to the intended commit and the verifier passes.

## Reference Sources

- Raspberry Pi `config.txt`, `auto_initramfs`, and `disable_splash`: <https://www.raspberrypi.com/documentation/computers/config_txt.html>
- Raspberry Pi boot-partition and image layout: <https://www.raspberrypi.com/documentation/configuration/computers/raspberry-pi.html>
- cloud-init supported disable mechanisms: <https://cloudinit.readthedocs.io/en/21.2/topics/boot.html>
- labwc environment and cursor variables: <https://labwc.github.io/labwc-config.5.html>
