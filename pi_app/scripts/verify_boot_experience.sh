#!/bin/bash

set -euo pipefail

CMDLINE_FILE="/boot/firmware/cmdline.txt"
CONFIG_FILE="/boot/firmware/config.txt"
EXPECTED_LOGO="assets/Logo_800x480.png"

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

check "HDMI console is removed" bash -c "! grep -Eq '(^| )console=tty1( |$)' '${CMDLINE_FILE}'"
check "kernel command line contains no carriage returns" bash -c "tr -d '\r' < '${CMDLINE_FILE}' | cmp -s - '${CMDLINE_FILE}'"
check "Plymouth is disabled" grep -Eq '(^| )plymouth.enable=0( |$)' "${CMDLINE_FILE}"
check "unstable early fullscreen logo is disabled" bash -c "! grep -Eq '(^| )fullscreen_logo=1( |$)' '${CMDLINE_FILE}'"
check "boot cursor is disabled" grep -Eq '(^| )vt.global_cursor_default=0( |$)' "${CMDLINE_FILE}"
check "firmware rainbow splash is disabled" grep -Eq '^disable_splash=1$' "${CONFIG_FILE}"
check "distro Plymouth theme is restored" test "$(/usr/sbin/plymouth-set-default-theme 2>/dev/null || true)" = "pix"
check "TTY1 getty is masked" test "$(systemctl is-enabled getty@tty1.service 2>/dev/null || true)" = "masked"
check "labwc omits the desktop panel" bash -c "! grep -q 'wf-panel-pi' \"${HOME}/.config/labwc/autostart\""
check "labwc starts the logo background" grep -q "${EXPECTED_LOGO}" "${HOME}/.config/labwc/autostart"
check "camera app is active" systemctl --user is-active --quiet checkpoint4-ui.service

if [ "${failures}" -ne 0 ]; then
  echo "${failures} boot-experience check(s) failed." >&2
  exit 1
fi

echo "All boot-experience checks passed."
