# Camera USB Controller Recovery - 2026-07-19

## Failure and root cause

At 15:34 EDT the running Pi application reported no camera nodes. Read-only
inspection showed that Linux still enumerated the upstream VIA Labs
`2109:3431` hub and product USB drive, but the Terminus `1a40:0101` downstream
hub, all four Espressif `303a:1001` devices, and the USB touchscreen were absent.
The application service was active and had no serial devices to discover.

The persistent kernel journal identified the lower-level failure. At 14:44 it
recorded repeated transaction-translator `error -71` messages, disconnected
`1-1.2` and its four camera children, then repeatedly reported xHCI `Setup
ERROR`, `device not accepting address ... error -22`, `invalid context state`,
and `unable to enumerate USB device`. This was an xHCI/controller enumeration
failure, not a BTC1 identity or Python re-index failure.

A guarded manual xHCI unbind/rebind restored the Terminus hub, touchscreen,
product drive, four stable `/dev/serial/by-id` identities, and the application
sessions. This established the recovery operation implemented in app 0.2.7.

## Implemented recovery boundary

Commits `fbc84aa`, `544db8f`, `bb643cc`, `dda2b7f`, and `83cfda4` implement and
harden the recovery path. Settings now contains an idle-only, single-flight
`RECONNECT CAMERAS` action. It invokes only this approved command:

```text
/usr/bin/systemctl start --no-block bullet-time-usb-recovery.service
```

The product owner explicitly approved the persistent privilege on July 19. The
installed sudoers entry permits only that exact root command; it does not allow
a shell, alternate arguments, or arbitrary sudo. The root-owned one-shot helper:

1. stops `bullet-time-ui.service`;
2. syncs and cleanly unmounts every mounted USB-backed partition;
3. unbinds and rebinds the installer-validated single PCI xHCI controller;
4. waits for four Espressif USB devices and four serial ports that the product
   user can read and write; and
5. restarts the UI on success or through an exit trap on failure.

The installer initially failed closed because its sysfs scan counted the
driver's generic `module` symlink. Commit `dda2b7f` restricts selection to PCI
address names. The first live one-shot then safely unmounted storage, reset the
controller, and restarted the UI through its trap, but exited early when
`pipefail` treated the expected first zero-device polling instant as fatal.
Commit `83cfda4` makes an empty poll nonfatal and waits for usable serial ACLs,
preventing the UI from restarting before the ports are accessible.

## Final Pi evidence

The final button-equivalent recovery began at 16:00:11 EDT on `camerapi`:

- result `success`, exit status `0`;
- `/dev/sda1` was reported unmounted before reset;
- the helper reported `4/4 ESP32 nodes and serial ports ready`;
- UI PID changed from `6985` to `7331`;
- the restarted UI owned four `ttyACM` file descriptors;
- `/dev/sda1` remounted read/write at `/media/username/USB DISK`;
- GPIO17 remained output LOW; and
- the root recovery service returned to inactive after its successful one-shot.

Native Wayland rendering found `cameraRecoveryButton`, swapped a frame at
800x480 with zero QML errors, and produced transient Pi artifact
`/tmp/settings-camera-recovery-800x480.png`, SHA-256
`d70939d8f9568e4b09365079b37e583bbd5865e0ccbb999526a1b4872aec9c3b`.

Post-recovery GPIO17 capture `20260719T200154Z_65b3fe04` completed all four
stable camera UIDs with unique transactions. App 0.2.7 committed four validated
JPEGs and a six-frame GIF in 2365.373 ms. The current evidence validator passed
all file sizes and CRCs and confirmed GIF camera order `[1, 2, 3, 4, 3, 2]`.

The product FAT was then checked offline. A dirty bit was found, so all current
drive content was copied to
`/home/username/usb-recovery-backups/20260719T1605-camera-recovery` on the Pi
boot filesystem before repair. The source and backup contained 20 regular
files and `diff -qr` passed before repair. `fsck.vfat -a /dev/sda1` cleared the
dirty bit; a separate offline `fsck.vfat -n` returned clean, and `diff -qr`
passed again after the application automatically remounted the drive. The
backup is retained.

Final validation at commit `83cfda4` passed 125 deterministic tests with the
one expected live-ledger test skipped, all 39 boot/session checks, active native
Wayland UI, four camera file descriptors, read/write removable storage, clean
Git state, and GPIO17 output LOW.

## Retained limitation

The legacy `pi_app.tools.summarize_captures` utility raised `KeyError: 'node'`
after the successful capture because it expects an obsolete one-node manifest
shape. Publication and the current artifact validator were unaffected. The
utility remains follow-up maintenance and is not represented as fixed here.
