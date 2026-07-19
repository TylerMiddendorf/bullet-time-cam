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
  echo "Run with sudo from the desktop user that runs the camera application." >&2
  exit 1
fi
TARGET_UID="$(id -u "${TARGET_USER}")"

mapfile -t controllers < <(
  find /sys/bus/pci/drivers/xhci_hcd -maxdepth 1 -type l -printf '%f\n' | sort
)
if [ "${#controllers[@]}" -ne 1 ]; then
  echo "Expected exactly one xHCI PCI controller; found ${#controllers[@]}." >&2
  exit 1
fi

RECOVERY_SCRIPT="${REPO_ROOT}/pi_app/scripts/recover_camera_usb.sh"
SERVICE_SOURCE="${REPO_ROOT}/pi_app/systemd/bullet-time-usb-recovery.service"
for required in "${RECOVERY_SCRIPT}" "${SERVICE_SOURCE}"; do
  if [ ! -f "${required}" ]; then
    echo "Required file not found: ${required}" >&2
    exit 1
  fi
done

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TEMP_DIR}"' EXIT
SUDOERS_FILE="${TEMP_DIR}/bullet-time-usb-recovery"
printf '%s ALL=(root) NOPASSWD: /usr/bin/systemctl start --no-block bullet-time-usb-recovery.service\n' \
  "${TARGET_USER}" >"${SUDOERS_FILE}"
visudo -cf "${SUDOERS_FILE}"

install -d -m 0755 /usr/local/libexec
install -m 0755 "${RECOVERY_SCRIPT}" /usr/local/libexec/bullet-time-recover-usb
install -m 0644 "${SERVICE_SOURCE}" /etc/systemd/system/bullet-time-usb-recovery.service
printf 'BULLET_TIME_USER=%s\nBULLET_TIME_UID=%s\nBULLET_TIME_XHCI=%s\n' \
  "${TARGET_USER}" "${TARGET_UID}" "${controllers[0]}" \
  >/etc/default/bullet-time-usb-recovery
install -m 0440 "${SUDOERS_FILE}" /etc/sudoers.d/bullet-time-usb-recovery
systemctl daemon-reload

echo "Installed guarded camera USB recovery for ${TARGET_USER} on ${controllers[0]}."
