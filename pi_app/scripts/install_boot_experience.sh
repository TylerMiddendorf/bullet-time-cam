#!/bin/bash

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TARGET_USER="${SUDO_USER:-username}"
TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
TARGET_UID="$(id -u "${TARGET_USER}")"
TARGET_GROUP="$(id -gn "${TARGET_USER}")"
LOGO_PNG="${REPO_ROOT}/assets/Logo_800x480.png"
SERVICE_SOURCE="${REPO_ROOT}/pi_app/systemd/checkpoint4-ui.service"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
CONFIG_FILE="/boot/firmware/config.txt"
BACKUP_ROOT="/var/lib/bullet-time-boot-backups"
BACKUP_DIR="${BACKUP_ROOT}/$(date -u +%Y%m%dT%H%M%SZ)"
USER_LABWC_DIR="${TARGET_HOME}/.config/labwc"
USER_SYSTEMD_DIR="${TARGET_HOME}/.config/systemd/user"
USER_AUTOSTART="${USER_LABWC_DIR}/autostart"
USER_SERVICE="${USER_SYSTEMD_DIR}/checkpoint4-ui.service"

for required in "${LOGO_PNG}" "${SERVICE_SOURCE}" "${CMDLINE_FILE}" "${CONFIG_FILE}"; do
  if [ ! -f "${required}" ]; then
    echo "Required file not found: ${required}" >&2
    exit 1
  fi
done

if ! tr -d '\0' </proc/device-tree/model 2>/dev/null | grep -q "Raspberry Pi"; then
  echo "This installer must run on a Raspberry Pi." >&2
  exit 1
fi

install -d -m 0755 "${BACKUP_DIR}"
cp -a "${CMDLINE_FILE}" "${BACKUP_DIR}/cmdline.txt"
cp -a "${CONFIG_FILE}" "${BACKUP_DIR}/config.txt"
if [ -e "${USER_AUTOSTART}" ]; then
  cp -a "${USER_AUTOSTART}" "${BACKUP_DIR}/labwc-autostart"
fi
if [ -e "${USER_SERVICE}" ]; then
  cp -a "${USER_SERVICE}" "${BACKUP_DIR}/checkpoint4-ui.service"
fi
if [ -e /usr/share/plymouth/themes/default.plymouth ]; then
  readlink -f /usr/share/plymouth/themes/default.plymouth >"${BACKUP_DIR}/default-plymouth-theme.txt" || true
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y imagemagick rpi-splash-screen-support swaybg

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT
LOGO_TGA="${TEMP_DIR}/logo.tga"

if command -v magick >/dev/null 2>&1; then
  magick "${LOGO_PNG}" -colors 224 -depth 8 -type TrueColor -alpha off \
    -compress none -define tga:bits-per-sample=8 "${LOGO_TGA}"
else
  convert "${LOGO_PNG}" -colors 224 -depth 8 -type TrueColor -alpha off \
    -compress none -define tga:bits-per-sample=8 "${LOGO_TGA}"
fi

# Raspberry Pi's supported helper embeds the early fullscreen logo in initramfs.
configure-splash "${LOGO_TGA}" --no-cmdline

# Keep the distro's proven theme selected even though Plymouth is disabled for
# this product path. The custom script theme used in the first attempt crashed
# Plymouth 24.004.60 on Raspberry Pi OS Trixie before root startup.
/usr/sbin/plymouth-set-default-theme pix

# Raspberry Pi OS commonly ships cmdline.txt without a trailing newline. Bash
# still populates the array in that case, but read returns nonzero at EOF.
IFS=' ' read -r -a current_tokens <"${CMDLINE_FILE}" || true
new_tokens=()
for token in "${current_tokens[@]}"; do
  case "${token}" in
    console=tty1|quiet|splash|plymouth.ignore-serial-consoles|plymouth.enable=*|rd.plymouth=*|vt.global_cursor_default=*|fullscreen_logo=*|fullscreen_logo_name=*|loglevel=*|systemd.show_status=*|rd.systemd.show_status=*|udev.log_level=*|consoleblank=*)
      ;;
    *)
      new_tokens+=("${token}")
      ;;
  esac
done
new_tokens+=(
  "quiet"
  "plymouth.enable=0"
  "rd.plymouth=0"
  "vt.global_cursor_default=0"
  "fullscreen_logo=1"
  "fullscreen_logo_name=logo.tga"
  "loglevel=3"
  "systemd.show_status=false"
  "rd.systemd.show_status=false"
  "udev.log_level=3"
  "consoleblank=0"
)
printf '%s\n' "${new_tokens[*]}" >"${TEMP_DIR}/cmdline.txt"
install -m 0644 "${TEMP_DIR}/cmdline.txt" "${CMDLINE_FILE}"

awk '!/^disable_splash=/' "${CONFIG_FILE}" >"${TEMP_DIR}/config.txt"
printf '\n[all]\n# Bullet-Time product boot presentation\ndisable_splash=1\n' >>"${TEMP_DIR}/config.txt"
install -m 0644 "${TEMP_DIR}/config.txt" "${CONFIG_FILE}"

install -d -m 0755 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${USER_LABWC_DIR}" "${USER_SYSTEMD_DIR}"
{
  printf '/usr/bin/swaybg -c 000000 -i %q -m fill &\n' "${LOGO_PNG}"
  printf '/usr/bin/kanshi &\n'
  printf '/usr/bin/systemctl --user restart checkpoint4-ui.service &\n'
} >"${TEMP_DIR}/labwc-autostart"
install -m 0644 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${TEMP_DIR}/labwc-autostart" "${USER_AUTOSTART}"
install -m 0644 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${SERVICE_SOURCE}" "${USER_SERVICE}"

# The HDMI virtual console must never clear the logo with a login prompt.
# Serial console and SSH remain available as recovery paths.
systemctl mask getty@tty1.service autovt@tty1.service
systemctl daemon-reload

if [ -S "/run/user/${TARGET_UID}/bus" ]; then
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user disable checkpoint4-ui.service || true
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user daemon-reload
fi

update-initramfs -u -k all

echo "Installed the Bullet-Time logo boot experience."
echo "Backup: ${BACKUP_DIR}"
echo "Reboot to activate and verify the complete handoff."
