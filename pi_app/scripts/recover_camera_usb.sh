#!/bin/bash

set -euo pipefail

CONFIG_FILE="/etc/default/bullet-time-usb-recovery"
if [ "$(id -u)" -ne 0 ]; then
  echo "Camera USB recovery must run as root." >&2
  exit 1
fi
if [ ! -r "${CONFIG_FILE}" ]; then
  echo "Recovery configuration is missing: ${CONFIG_FILE}" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "${CONFIG_FILE}"
: "${BULLET_TIME_USER:?missing recovery user}"
: "${BULLET_TIME_UID:?missing recovery uid}"
: "${BULLET_TIME_XHCI:?missing xHCI controller}"

USER_RUNTIME="/run/user/${BULLET_TIME_UID}"
DRIVER_ROOT="/sys/bus/pci/drivers/xhci_hcd"
CONTROLLER_PATH="/sys/bus/pci/devices/${BULLET_TIME_XHCI}"

user_systemctl() {
  runuser -u "${BULLET_TIME_USER}" -- env "XDG_RUNTIME_DIR=${USER_RUNTIME}" \
    systemctl --user "$@"
}

restart_ui() {
  user_systemctl start bullet-time-ui.service || true
}

if [ ! -S "${USER_RUNTIME}/bus" ]; then
  echo "The ${BULLET_TIME_USER} user service manager is unavailable." >&2
  exit 1
fi
if [ ! -L "${CONTROLLER_PATH}/driver" ] || \
  [ "$(basename "$(readlink -f "${CONTROLLER_PATH}/driver")")" != "xhci_hcd" ]; then
  echo "Configured controller ${BULLET_TIME_XHCI} is not bound to xhci_hcd." >&2
  exit 1
fi

trap restart_ui EXIT
user_systemctl stop bullet-time-ui.service
sync

while read -r device device_type; do
  if [ "${device_type}" != "part" ] || ! lsblk -s -ndo TRAN "${device}" | grep -qx usb; then
    continue
  fi
  if findmnt -rn -S "${device}" >/dev/null; then
    runuser -u "${BULLET_TIME_USER}" -- env "XDG_RUNTIME_DIR=${USER_RUNTIME}" \
      udisksctl unmount -b "${device}"
  fi
done < <(lsblk -nrpo PATH,TYPE)

printf '%s' "${BULLET_TIME_XHCI}" >"${DRIVER_ROOT}/unbind"
sleep 2
printf '%s' "${BULLET_TIME_XHCI}" >"${DRIVER_ROOT}/bind"
udevadm settle --timeout=15

camera_count=0
for _attempt in $(seq 1 20); do
  camera_count="$(lsusb -d 303a:1001 2>/dev/null | wc -l)"
  if [ "${camera_count}" -eq 4 ]; then
    break
  fi
  sleep 1
done

if [ "${camera_count}" -ne 4 ]; then
  echo "USB reset completed, but only ${camera_count}/4 ESP32 camera nodes enumerated." >&2
  exit 1
fi

restart_ui
trap - EXIT
echo "Camera USB recovery completed with 4/4 ESP32 nodes enumerated."
