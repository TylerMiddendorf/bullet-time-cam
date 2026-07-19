#!/bin/bash

set -euo pipefail

CMDLINE_FILE="/boot/firmware/cmdline.txt"
CONFIG_FILE="/boot/firmware/config.txt"
EXPECTED_LOGO="assets/Logo_800x480.png"
LABWC_AUTOSTART="${HOME}/.config/bullet-time-labwc/autostart"
LABWC_ENVIRONMENT="${HOME}/.config/bullet-time-labwc/environment"
APP_PYTHON="${HOME}/esp32cam-tools/bin/python"
EXPECTED_REPO_ROOT="${HOME}/bullet-time-cam"

failures=0

check() {
  local description="$1"
  shift
  if "$@"; then
    printf 'PASS: %s\n' "${description}"
  else
    printf 'FAIL: %s\n' "${description}" >&2
    failures=$((failures + 1))
  fi
}

check "required tty1 console is retained" grep -Eq '(^| )console=tty1( |$)' "${CMDLINE_FILE}"
check "repository uses the stable service path" test "$(pwd -P)" = "${EXPECTED_REPO_ROOT}"
check "camera runtime is installed" test -x "${APP_PYTHON}"
check "camera runtime imports succeed" "${APP_PYTHON}" -c 'import PIL, psutil, serial, tkinter'
check "PySide6 Qt Quick imports succeed" "${APP_PYTHON}" -c \
  'from PySide6 import QtCore, QtGui, QtQml, QtQuick'
check "Wayland Qt platform plugin is installed" bash -c \
  "dpkg-query -W -f='\${Status}' qt6-wayland 2>/dev/null | grep -q 'install ok installed'"
check "Qt Quick route tree loads" env QT_QPA_PLATFORM=wayland WAYLAND_DISPLAY=wayland-0 \
  "${APP_PYTHON}" -c 'from pi_app.bullettime.qt_ui import verify_qml; verify_qml()'
check "USB storage mount helper is installed" test -x /usr/bin/udisksctl
check "pinned lgpio package is installed" test "$(dpkg-query -W -f='${Version}' python3-lgpio 2>/dev/null || true)" = "0.2.2-1~rpt1+trixie"
check "camera runtime can import lgpio" "${APP_PYTHON}" -c 'import lgpio'
check "camera user has serial access" bash -c "id -nG | tr ' ' '\n' | grep -qx dialout"
check "camera user has GPIO access" bash -c "id -nG | tr ' ' '\n' | grep -qx gpio"
check "kernel command line contains no carriage returns" bash -c "tr -d '\r' < '${CMDLINE_FILE}' | cmp -s - '${CMDLINE_FILE}'"
check "Plymouth is disabled" grep -Eq '(^| )plymouth.enable=0( |$)' "${CMDLINE_FILE}"
check "cloud-init console output is disabled" grep -Eq '(^| )cloud-init=disabled( |$)' "${CMDLINE_FILE}"
check "cloud-init marker is installed" test -e /etc/cloud/cloud-init.disabled
check "Raspberry Pi Imager datasource is retired" bash -c "! grep -Eq '(^| )ds=nocloud' '${CMDLINE_FILE}'"
check "unstable early fullscreen logo is disabled" bash -c "! grep -Eq '(^| )fullscreen_logo=1( |$)' '${CMDLINE_FILE}'"
check "early splash hook is absent" test ! -e /etc/initramfs-tools/hooks/splash-screen-hook.sh
check "early splash package is absent" bash -c "! dpkg-query -W rpi-splash-screen-support >/dev/null 2>&1"
check "boot cursor is disabled" grep -Eq '(^| )vt.global_cursor_default=0( |$)' "${CMDLINE_FILE}"
check "regenerated initramfs is bypassed" grep -Eq '^auto_initramfs=0$' "${CONFIG_FILE}"
check "firmware rainbow splash is disabled" grep -Eq '^disable_splash=1$' "${CONFIG_FILE}"
check "distro Plymouth theme is restored" test "$(/usr/sbin/plymouth-set-default-theme 2>/dev/null || true)" = "pix"
check "TTY1 getty is masked" test "$(systemctl is-enabled getty@tty1.service 2>/dev/null || true)" = "masked"
check "LightDM autologin user is selected" grep -Eq "^autologin-user=$(id -un)$" /etc/lightdm/lightdm.conf
check "LightDM autologin has no delay" grep -Eq '^autologin-user-timeout=0$' /etc/lightdm/lightdm.conf
check "dedicated LightDM user session is selected" grep -Eq '^user-session=bullet-time$' /etc/lightdm/lightdm.conf
check "dedicated LightDM session is selected" grep -Eq '^autologin-session=bullet-time$' /etc/lightdm/lightdm.conf
check "labwc omits the desktop panel" bash -c "! grep -q 'wf-panel-pi' '${LABWC_AUTOSTART}'"
check "desktop chrome is not running" bash -c "! ps -eo comm= | grep -Eq '^(wf-panel-pi|pcmanfm|lxpanel)$'"
check "labwc starts the logo background" grep -q "${EXPECTED_LOGO}" "${LABWC_AUTOSTART}"
check "labwc selects the invisible cursor theme" grep -Eq '^XCURSOR_THEME=BulletTimeInvisible$' "${LABWC_ENVIRONMENT}"
check "invisible cursor theme is installed" test -s /usr/share/icons/BulletTimeInvisible/cursors/left_ptr
check "camera app is active" systemctl --user is-active --quiet bullet-time-ui.service
check "camera app forces native Wayland" grep -Eq '^Environment=QT_QPA_PLATFORM=wayland$' \
  "${HOME}/.config/systemd/user/bullet-time-ui.service"
check "legacy checkpoint service is absent" test ! -e "${HOME}/.config/systemd/user/checkpoint4-ui.service"

if [ "${failures}" -ne 0 ]; then
  echo "${failures} boot-experience check(s) failed." >&2
  exit 1
fi

echo "All boot-experience checks passed."
