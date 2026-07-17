# USB Storage Bring-Up - 2026-07-17

## Scope

This evidence covers Raspberry Pi enumeration of the newly added removable USB drive and the automatic-mount mechanism used by the application. It does not claim that the uncommitted application changes were deployed or that a JPEG/GIF was written by the application.

## Device Evidence

Read-only inspection over the pinned `camerapi` SSH alias reported:

- Disk: `/dev/sda`, USB transport, removable, 231 GB
- Partition: `/dev/sda1`, FAT (`vfat`), label `USB DISK`, UUID `B67C-53C4`
- Initial state: not mounted
- Raspberry Pi boot media: `/dev/mmcblk0`, confirming the user drive and protected boot microSD are distinct block devices
- `udisksctl`: installed at `/usr/bin/udisksctl`
- Application user: `username`, UID/GID 1000, member of `plugdev`

The resolved sysfs device path was:

```text
/sys/devices/platform/scb/fd500000.pcie/pci0000:00/0000:00:00.0/0000:01:00.0/usb1/1-1/1-1.4/1-1.4:1.0/host0/target0:0:0/0:0:0:0/block/sda/sda1
```

This satisfies the application's USB-ancestry test for major/minor device `8:1`.

## Mount Evidence

An SSH-process invocation was denied by Polkit because that process was not part of the active local graphical session. The same command was then run through the camera user's systemd user-service manager, matching the application service context:

```bash
XDG_RUNTIME_DIR=/run/user/1000 systemd-run --user --wait --pipe \
  /usr/bin/udisksctl mount --no-user-interaction --block-device /dev/sda1
```

Result:

```text
Mounted /dev/sda1 at /media/username/USB DISK
Finished with result: success
```

Follow-up inspection reported `/dev/sda1` mounted at `/media/username/USB DISK` as read/write FAT with `uid=1000,gid=1000`; `test -w` passed for user `username`.

## Automated Software Evidence

From the Windows repository checkout:

```text
python -m unittest discover -s pi_app/tests -v
Ran 19 tests in 0.027s
OK
```

Storage coverage includes mountinfo parsing and escaped mount names, USB-only selection, the configured preferred drive, automatic-mount rescan, capture-root path confinement, and refusal to fall back to boot storage.

## Open Validation

- Commit/push the code and pull it through the project's Git-only Pi deployment flow.
- Run the camera service with the new configuration and commit a real original/manifest to `BulletTime/`.
- Verify manifest storage metadata and touchscreen review from the USB-backed file.
- Test service restart and physical USB unplug/replug.
- Test missing, full, read-only, corrupt, and removal-during-write behavior without accepting a partial or falling back to the boot microSD.
