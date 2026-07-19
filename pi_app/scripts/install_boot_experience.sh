#!/bin/bash

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TARGET_USER="${SUDO_USER:-}"
if [ -z "${TARGET_USER}" ] || [ "${TARGET_USER}" = "root" ]; then
  echo "Run this script with sudo from the desktop user that will run the camera application." >&2
  exit 1
fi
TARGET_HOME="$(getent passwd "${TARGET_USER}" | cut -d: -f6)"
if [ -z "${TARGET_HOME}" ]; then
  echo "Could not resolve the home directory for ${TARGET_USER}." >&2
  exit 1
fi
TARGET_UID="$(id -u "${TARGET_USER}")"
TARGET_GROUP="$(id -gn "${TARGET_USER}")"
EXPECTED_REPO_ROOT="${TARGET_HOME}/bullet-time-cam"
LOGO_PNG="${REPO_ROOT}/assets/Logo_800x480.png"
SERVICE_NAME="bullet-time-ui.service"
LEGACY_SERVICE_NAME="checkpoint4-ui.service"
SERVICE_SOURCE="${REPO_ROOT}/pi_app/systemd/${SERVICE_NAME}"
SESSION_SOURCE="${REPO_ROOT}/pi_app/session"
REQUIREMENTS_FILE="${REPO_ROOT}/pi_app/requirements.txt"
SYSTEM_REQUIREMENTS_FILE="${REPO_ROOT}/pi_app/system-requirements.txt"
VENV_DIR="${TARGET_HOME}/esp32cam-tools"
CMDLINE_FILE="/boot/firmware/cmdline.txt"
CONFIG_FILE="/boot/firmware/config.txt"
LIGHTDM_FILE="/etc/lightdm/lightdm.conf"
BACKUP_ROOT="/var/lib/bullet-time-boot-backups"
BACKUP_DIR="${BACKUP_ROOT}/$(date -u +%Y%m%dT%H%M%SZ)"
USER_LABWC_DIR="${TARGET_HOME}/.config/bullet-time-labwc"
USER_SYSTEMD_DIR="${TARGET_HOME}/.config/systemd/user"
USER_AUTOSTART="${USER_LABWC_DIR}/autostart"
USER_ENVIRONMENT="${USER_LABWC_DIR}/environment"
USER_SERVICE="${USER_SYSTEMD_DIR}/${SERVICE_NAME}"
LEGACY_USER_SERVICE="${USER_SYSTEMD_DIR}/${LEGACY_SERVICE_NAME}"
CLOUD_INIT_DISABLED_FILE="/etc/cloud/cloud-init.disabled"
CURSOR_THEME_DIR="/usr/share/icons/BulletTimeInvisible"

if [ "$(realpath "${REPO_ROOT}")" != "$(realpath -m "${EXPECTED_REPO_ROOT}")" ]; then
  echo "Clone this repository at ${EXPECTED_REPO_ROOT}; the service intentionally uses that stable path." >&2
  exit 1
fi

for required in "${LOGO_PNG}" "${SERVICE_SOURCE}" "${REQUIREMENTS_FILE}" "${SYSTEM_REQUIREMENTS_FILE}" \
  "${SESSION_SOURCE}/bullet-time-session" "${SESSION_SOURCE}/bullet-time.desktop" \
  "${CMDLINE_FILE}" "${CONFIG_FILE}"; do
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
if [ -e "${LIGHTDM_FILE}" ]; then
  cp -a "${LIGHTDM_FILE}" "${BACKUP_DIR}/lightdm.conf"
fi
if [ -e "${USER_AUTOSTART}" ]; then
  cp -a "${USER_AUTOSTART}" "${BACKUP_DIR}/labwc-autostart"
fi
if [ -e "${USER_ENVIRONMENT}" ]; then
  cp -a "${USER_ENVIRONMENT}" "${BACKUP_DIR}/labwc-environment"
fi
if [ -e "${USER_SERVICE}" ]; then
  cp -a "${USER_SERVICE}" "${BACKUP_DIR}/${SERVICE_NAME}"
fi
if [ -e "${LEGACY_USER_SERVICE}" ]; then
  cp -a "${LEGACY_USER_SERVICE}" "${BACKUP_DIR}/${LEGACY_SERVICE_NAME}"
fi
if [ -e /usr/share/plymouth/themes/default.plymouth ]; then
  readlink -f /usr/share/plymouth/themes/default.plymouth >"${BACKUP_DIR}/default-plymouth-theme.txt" || true
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install --no-upgrade -y \
  git kanshi labwc lightdm network-manager plymouth python3 python3-pil \
  python3-tk python3-venv raspi-config-core rpd-common rpd-plym-splash \
  swaybg udisks2 x11-apps
mapfile -t system_requirements <"${SYSTEM_REQUIREMENTS_FILE}"
apt-get install --no-upgrade -y "${system_requirements[@]}"

if [ ! -f "${LIGHTDM_FILE}" ]; then
  echo "LightDM configuration was not created at ${LIGHTDM_FILE}." >&2
  exit 1
fi

for supplemental_group in dialout input render video; do
  if getent group "${supplemental_group}" >/dev/null; then
    usermod -aG "${supplemental_group}" "${TARGET_USER}"
  fi
done
# The GPIO binding is supplied and maintained by Raspberry Pi OS. Ensure the
# app venv can see that system package even when upgrading an older venv.
if [ -x "${VENV_DIR}/bin/python" ]; then
  runuser -u "${TARGET_USER}" -- python3 -m venv --upgrade --system-site-packages "${VENV_DIR}"
else
  runuser -u "${TARGET_USER}" -- python3 -m venv --system-site-packages "${VENV_DIR}"
fi
runuser -u "${TARGET_USER}" -- "${VENV_DIR}/bin/pip" install -r "${REQUIREMENTS_FILE}"

# Raspberry Pi Imager provisioning is complete. Disable cloud-init so its
# per-boot stage helper cannot tee status messages directly to /dev/console.
install -m 0644 /dev/null "${CLOUD_INIT_DISABLED_FILE}"

# Remove the early-logo initramfs integration that hung this OS/kernel when
# tty1 was absent. Preserve the generated files in the timestamped backup.
install -d -m 0755 "${BACKUP_DIR}/retired-early-splash"
for splash_file in /etc/initramfs-tools/hooks/splash-screen-hook.sh /lib/firmware/logo.tga; do
  if [ -e "${splash_file}" ]; then
    mv "${splash_file}" "${BACKUP_DIR}/retired-early-splash/"
  fi
done
if dpkg-query -W -f='${Status}' rpi-splash-screen-support 2>/dev/null | grep -q 'install ok installed'; then
  apt-get purge -y rpi-splash-screen-support
fi

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT

# Install a fully transparent cursor theme before labwc starts. Qt also forces
# a blank application cursor, while the compositor exists first and otherwise
# exposes its default cursor over the logo background. Tk/X11 remain installed
# only as a rollback path for the accepted pre-Qt presentation.
install -d -m 0755 "${CURSOR_THEME_DIR}/cursors"
printf '%s' 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNgYGBgAAAABQABeqhXUAAAAABJRU5ErkJggg==' \
  | base64 -d >"${TEMP_DIR}/transparent-cursor.png"
printf '24 0 0 %s\n' "${TEMP_DIR}/transparent-cursor.png" >"${TEMP_DIR}/cursor.conf"
/usr/bin/xcursorgen "${TEMP_DIR}/cursor.conf" "${CURSOR_THEME_DIR}/cursors/left_ptr"
for system_cursor in /usr/share/icons/PiXtrix/cursors/*; do
  cursor_name="$(basename "${system_cursor}")"
  if [ "${cursor_name}" != "left_ptr" ]; then
    ln -sfn left_ptr "${CURSOR_THEME_DIR}/cursors/${cursor_name}"
  fi
done
printf '[Icon Theme]\nName=Bullet-Time Invisible Cursor\n' >"${CURSOR_THEME_DIR}/index.theme"

# Keep the distro's proven theme selected even though Plymouth is disabled for
# this product path. Hardware trials showed that both custom Plymouth and the
# Trixie early-fullscreen-logo path can prevent this Pi from reaching root.
/usr/sbin/plymouth-set-default-theme pix

# Collapse any CRLF left by boot-card recovery on Windows, while still
# tolerating Raspberry Pi OS images that omit the final newline entirely.
cmdline_text="$(tr '\r\n' ' ' <"${CMDLINE_FILE}")"
IFS=' ' read -r -a current_tokens <<<"${cmdline_text}"
new_tokens=()
for token in "${current_tokens[@]}"; do
  case "${token}" in
    console=tty1|quiet|splash|plymouth.ignore-serial-consoles|plymouth.enable=*|rd.plymouth=*|vt.global_cursor_default=*|fullscreen_logo=*|fullscreen_logo_name=*|loglevel=*|systemd.show_status=*|rd.systemd.show_status=*|udev.log_level=*|consoleblank=*|ds=nocloud*|cloud-init=*)
      ;;
    *)
      new_tokens+=("${token}")
      ;;
  esac
done
new_tokens+=(
  "console=tty1"
  "quiet"
  "plymouth.enable=0"
  "rd.plymouth=0"
  "vt.global_cursor_default=0"
  "loglevel=0"
  "systemd.show_status=false"
  "rd.systemd.show_status=false"
  "udev.log_level=0"
  "consoleblank=0"
  "cloud-init=disabled"
)
printf '%s\n' "${new_tokens[*]}" >"${TEMP_DIR}/cmdline.txt"
install -m 0644 "${TEMP_DIR}/cmdline.txt" "${CMDLINE_FILE}"

awk '!/^disable_splash=/ && !/^auto_initramfs=/' "${CONFIG_FILE}" >"${TEMP_DIR}/config.txt"
printf '\n[all]\n# Bullet-Time product boot presentation\nauto_initramfs=0\ndisable_splash=1\n' >>"${TEMP_DIR}/config.txt"
install -m 0644 "${TEMP_DIR}/config.txt" "${CONFIG_FILE}"

install -d -m 0755 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${USER_LABWC_DIR}" "${USER_SYSTEMD_DIR}"
{
  printf '/usr/bin/swaybg -c 000000 -i %q -m fill &\n' "${LOGO_PNG}"
  printf '/usr/bin/kanshi &\n'
  printf '/usr/bin/systemctl --user restart %s &\n' "${SERVICE_NAME}"
} >"${TEMP_DIR}/labwc-autostart"
install -m 0644 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${TEMP_DIR}/labwc-autostart" "${USER_AUTOSTART}"
printf 'XCURSOR_THEME=BulletTimeInvisible\nXCURSOR_SIZE=24\n' >"${TEMP_DIR}/labwc-environment"
install -m 0644 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${TEMP_DIR}/labwc-environment" "${USER_ENVIRONMENT}"
install -m 0644 -o "${TARGET_USER}" -g "${TARGET_GROUP}" "${SERVICE_SOURCE}" "${USER_SERVICE}"
install -m 0755 "${SESSION_SOURCE}/bullet-time-session" "/usr/local/bin/bullet-time-session"
install -m 0644 "${SESSION_SOURCE}/bullet-time.desktop" "/usr/share/wayland-sessions/bullet-time.desktop"

awk -v target_user="${TARGET_USER}" '
  function emit_camera_seat() {
    print "user-session=bullet-time"
    print "autologin-user=" target_user
    print "autologin-user-timeout=0"
    print "autologin-session=bullet-time"
    inserted = 1
  }
  /^\[/ {
    if (in_seat && !inserted) {
      emit_camera_seat()
    }
    in_seat = ($0 == "[Seat:*]")
    if (in_seat) {
      seat_found = 1
    }
    print
    next
  }
  in_seat && /^(user-session|autologin-user|autologin-user-timeout|autologin-session)=/ {
    next
  }
  { print }
  END {
    if (in_seat && !inserted) {
      emit_camera_seat()
    }
    if (!seat_found) {
      print ""
      print "[Seat:*]"
      emit_camera_seat()
    }
  }
' "${LIGHTDM_FILE}" >"${TEMP_DIR}/lightdm.conf"
install -m 0644 "${TEMP_DIR}/lightdm.conf" "${LIGHTDM_FILE}"

# The HDMI virtual console must never clear the logo with a login prompt.
# Serial console and SSH remain available as recovery paths.
systemctl mask getty@tty1.service autovt@tty1.service
systemctl daemon-reload

if [ -S "/run/user/${TARGET_UID}/bus" ]; then
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user stop "${LEGACY_SERVICE_NAME}" || true
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user disable "${LEGACY_SERVICE_NAME}" || true
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user disable "${SERVICE_NAME}" || true
fi
rm -f "${LEGACY_USER_SERVICE}"
if [ -S "/run/user/${TARGET_UID}/bus" ]; then
  runuser -u "${TARGET_USER}" -- env "XDG_RUNTIME_DIR=/run/user/${TARGET_UID}" \
    systemctl --user daemon-reload
fi

# Do not regenerate initramfs on this product image. Hardware trials showed
# that a freshly generated image prevents this Pi from reaching userspace;
# config.txt explicitly boots the kernel directly instead.

echo "Installed the Bullet-Time logo boot experience."
echo "Backup: ${BACKUP_DIR}"
echo "Reboot to activate and verify the complete handoff."
