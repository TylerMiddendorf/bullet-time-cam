# Raspberry Pi Qt Deployment and Rollback Checklist

Status: unexecuted operator checklist. It describes a future commit-push-pull
deployment; this validation track has not deployed Qt to the Pi.

The deployment is accepted only if every required value and artifact is copied
into a dated evidence record. Stop at the first failed gate and leave the
known-good Tk service recoverable.

## Verified starting facts to preserve

The following acceptance facts were verified on the Pi at clean Git commit
`1e6a6e7` before this checklist was written:

| Fact | Verified value |
| --- | --- |
| Git | clean `1e6a6e7` |
| UI service | healthy, PID `5111` |
| Trigger output | GPIO17 output LOW |
| Cameras | all four stable UIDs present |
| Serial ownership | UI is the only serial owner |
| Product storage | removable product USB mounted read-write |
| Available memory | 1.4 GiB |
| Root filesystem free | 6.5 GiB |
| Temperature / throttling | 37 C; `get_throttled=0` |

These are the pre-switch baseline, not permission to skip revalidation. A prior
transient Terminus hub `error -71` caused disconnect/recovery. Capture kernel
and service logs before the switch, watch for recurrence throughout the run,
and prove all four stable UIDs plus exclusive UI serial ownership after any
recovery. Do not rewrite the transient as a permanently resolved fault.

## 1. Workstation release gate: commit and push

- [ ] Worktree is on the intended `codex/qt-touchscreen-validation` history.
- [ ] `docs/MILESTONE_4_PLAN.md` has no diff.
- [ ] Contract validator, focused tests, full deterministic suite, hooks, and
      bounded offscreen QML smoke pass.
- [ ] Seven screenshots and evidence JSON are complete.
- [ ] No QML imports `QtMultimedia`; no source claims live preview, battery,
      hotspot, or 12-camera behavior.
- [ ] Every unsupported setting is disabled and the node-command test sink is
      empty.
- [ ] Commit the coherent revision and record `git rev-parse HEAD` as
      `EXPECTED_DEPLOY_SHA`.
- [ ] Push that exact commit. Record remote, branch, push output, and
      `git ls-remote <remote> refs/heads/<branch>`; the remote SHA must equal
      `EXPECTED_DEPLOY_SHA`.

Do not copy source files to the Pi. Git is the deployment source of truth.

## 2. Pi preflight and rollback capture

Run read-only checks before package installation or service changes:

```bash
cd <pi-repository>
git status --short
git rev-parse HEAD
systemctl --user show bullet-time-ui.service -p ActiveState -p SubState -p MainPID
systemctl --user cat bullet-time-ui.service
systemctl --user show-environment
free -h
df -h /
vcgencmd measure_temp
vcgencmd get_throttled
findmnt -no SOURCE,FSTYPE,OPTIONS,TARGET <product-usb-mount>
```

- [ ] Working tree is clean and pre-switch SHA is recorded. Expected baseline is
      `1e6a6e7`; explain any difference before continuing.
- [ ] Service is active and healthy. If it has not restarted, baseline PID is
      `5111`; a changed PID is not automatically a failure but must be explained.
- [ ] GPIO17 is configured as output LOW using the repository's existing GPIO
      verifier/backend, not inferred from UI text.
- [ ] All four configured stable UIDs are present in discovery/service evidence.
- [ ] For every camera `/dev/serial/by-id` target, `fuser`/`lsof` shows only the
      UI PID. Stop if another observer owns a serial port.
- [ ] Product USB is the configured USB-backed filesystem, mounted read-write;
      no capture path resolves to `/` or boot microSD.
- [ ] Record memory, root free space, temperature, and `get_throttled`. The
      verified baseline was 1.4 GiB free RAM, 6.5 GiB free root, 37 C, and zero.
- [ ] Save bounded `journalctl --user -u bullet-time-ui.service` and kernel logs,
      including any `error -71`, USB disconnect, and recovery lines.

Create a dated rollback directory outside the checkout. Copy the installed
user unit, environment/config files, session launcher, package inventory,
pre-switch SHA, unit properties, and checksums. Record the exact commands and
destination; do not include private SSH keys or user media.

## 3. Install the minimum Trixie arm64 runtime

The explicit package set is intentionally small; apt supplies transitive Qt
6.8/PySide6 dependencies:

Debian's Trixie package index is the version authority for
[`python3-pyside6.qtquick`](https://packages.debian.org/trixie/python3-pyside6.qtquick),
[`qml6-module-qtquick-controls`](https://packages.debian.org/trixie/qml6-module-qtquick-controls),
[`qml6-module-qtquick-layouts`](https://packages.debian.org/trixie/qml6-module-qtquick-layouts),
[`qml6-module-qtqml-workerscript`](https://packages.debian.org/trixie/qml6-module-qtqml-workerscript),
and [`qt6-wayland`](https://packages.debian.org/trixie/qt6-wayland). Record the
versions apt actually selects rather than copying a version from this plan.

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends \
  python3-pyside6.qtquick \
  qml6-module-qtquick-controls \
  qml6-module-qtquick-layouts \
  qml6-module-qtqml-workerscript \
  qt6-wayland
```

- [ ] Before installing effects, search QML imports. Install
      `qml6-module-qtquick-effects` only when `QtQuick.Effects` is actually
      imported; otherwise leave it absent from the explicit set.
- [ ] Record `dpkg-query` versions and architecture for every explicit package.
      Expected family is Qt 6.8 / PySide6 6.8 on arm64; record actual versions.
- [ ] Import QtCore/QtGui/QtQml/QtQuick from the same `/usr/bin/python3` the
      user service will execute.
- [ ] Retain the known Tk/X11 packages, units, and launch path during migration.
      Do not autoremove them until Qt/Wayland plus rollback acceptance is closed.

## 4. Fast-forward-only Git pull

With the Tk service still selected and the Pi checkout clean:

```bash
cd <pi-repository>
PRE_PULL_SHA=$(git rev-parse HEAD)
git fetch origin codex/qt-touchscreen-validation
git pull --ff-only origin codex/qt-touchscreen-validation
POST_PULL_SHA=$(git rev-parse HEAD)
git status --short
printf '%s\n' "$PRE_PULL_SHA" "$POST_PULL_SHA"
```

- [ ] Record `PRE_PULL_SHA`, `POST_PULL_SHA`, remote URL, branch, fetch output,
      pull output, and clean status.
- [ ] `POST_PULL_SHA` exactly equals workstation `EXPECTED_DEPLOY_SHA` and the
      pushed remote SHA. Stop on a merge, divergence, dirty tree, or mismatch.
- [ ] Run the dependency-free validator and deterministic tests from this exact
      checkout before changing the service.

## 5. Pre-activation QML smoke

Run the bounded smoke in the graphical user/Wayland environment while leaving
Tk selected for normal boot:

```bash
QT_QPA_PLATFORM=wayland python3 -m pi_app.tools.smoke_qt_qml \
  --qml pi_app/qt_ui/Main.qml \
  --platform wayland \
  --timeout-ms 5000 \
  --required-object startupLogo \
  --screenshot <evidence>/first-frame-wayland.png
```

- [ ] Environment explicitly contains `QT_QPA_PLATFORM=wayland` before PySide6
      import.
- [ ] Smoke returns PASS with zero QML warnings, at least one root object,
      `startupLogo` found, native 800x480 geometry, and `frame_swapped=true`.
- [ ] Screenshot is the opaque first logo frame and has a recorded SHA-256.
- [ ] `pgrep -a Xwayland` returns no process for the product session. Any
      Xwayland dependency fails the switch gate.

## 6. Staged service activation

- [ ] Install a separately named Qt unit or preserve a byte-for-byte restorable
      Tk unit. Never overwrite the only recovery copy.
- [ ] Qt unit uses the repository checkout at `POST_PULL_SHA`, `/usr/bin/python3`,
      and explicit `Environment=QT_QPA_PLATFORM=wayland`.
- [ ] Stop Tk cleanly and prove its receiver stopped, worker joined, serial
      handles closed, and GPIO17 returned/remained output LOW.
- [ ] Start Qt and prove it is the only UI process and only serial owner.
- [ ] Service remains active beyond startup timeout; no QML warning, traceback,
      restart loop, or GUI-thread stall appears.
- [ ] First compositor-to-Qt handoff shows the repository logo directly: no OS
      text, desktop, pointer, white/transparent flash, or stale Tk frame.
- [ ] Record first `frameSwapped` monotonic timing separately from the visual
      first-logo-frame observation.

## 7. Actual touchscreen and hardware acceptance

Execute on the physical 800x480 panel and real rig, not through synthetic
clicks alone:

1. Tap outside capture; prove no command. Tap capture once; prove one GPIO17
   pulse and one complete four-camera capture/committed GIF.
2. Press the physical shutter; prove one complete capture independent of Qt
   touch handling.
3. Exercise a controlled camera-unavailable case; prove partial review names
   the stable logical camera and preserves successful views.
4. Load a real committed GIF, then remove/unbind product media only after decode;
   prove animation/event polling continues from detached data and the next
   storage state is truthful. Restore media and prove recovery capture.
5. Exercise the read-only library against product USB; prove no boot-card entry,
   mutation, or open file handle survives detachment.
6. If Terminus `error -71` recurs, preserve kernel/service timestamps, prove
   disconnect UI, automatic rediscovery of all four stable UIDs, exclusive Qt
   serial ownership, and a successful post-recovery capture.
7. Request service stop and prove receiver stop, bounded worker join, serial
   close, and GPIO17 output LOW before process exit.
8. Reboot. Observe first logo frame/no OS chrome, confirm Wayland with no
   Xwayland, service health, four stable UIDs, exclusive serial ownership,
   product USB read-write, GPIO17 LOW, resource/thermal health, and one actual
   post-reboot touch capture.

## 8. Rollback drill

Rollback is required even after successful Qt tests:

1. Stop/disable the Qt unit. Confirm receiver join, serial close, and GPIO17 LOW.
2. Restore the saved Tk unit/config/session files by checksum.
3. Return the checkout non-destructively to recorded `PRE_PULL_SHA` with a clean
   `git switch --detach <PRE_PULL_SHA>` (or pull the approved rollback branch
   fast-forward-only). Do not use `git reset --hard`.
4. Reload user units, enable/start Tk, and prove it is the sole serial owner.
5. Reboot and observe the accepted logo-to-Tk handoff with no OS content.
6. Confirm four stable UIDs, GPIO17 output LOW, product USB read-write, and one
   actual touch capture plus committed four-view GIF.
7. Record restored Git SHA, unit/config checksums, service PID, capture ID,
   manifest storage fields, logs, and media validation.

If rollback fails, keep Qt disabled, preserve logs and media, and use the
documented non-display SSH/serial recovery path. Do not improvise a destructive
checkout or deploy uncommitted files.
