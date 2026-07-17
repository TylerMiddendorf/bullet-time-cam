# Raspberry Pi Display and Final USB Inventory - July 17, 2026

Status: read-only SSH inventory complete; product owner confirms the observed hub/cabling is the final V1 installation.

Inspection time reported by the Pi: `2026-07-17T18:41:47-04:00` on host `camerapi`.

## Display

- Active connector: `HDMI-A-2`
- Mode: 800x480 at 65.681 Hz, preferred/current
- Compositor-reported physical area: 150x100 mm
- EDID identity exposed by the compositor: make `Addi-Data GmbH`, model `0x0004`, serial `0x00000001`
- Video interface: HDMI
- Touch/power-side USB controller: `8888:6666`, device name `免驱触摸易驱板`, serial `Joy 1.0000`
- Touch USB speed: 12 Mb/s
- USB descriptor maximum: 100 mA at USB 5 V, equivalent to 0.5 W declared maximum

The 150x100 mm value is the display-reported physical area, not a caliper measurement of the outer bezel or depth. The 100 mA value is the generic USB interface's `bMaxPower`, not measured current for the whole display/backlight. Linux cannot supply the missing mechanical dimensions or real load over SSH; those require physical instruments if later enclosure or battery calculations need them.

## Installed Final USB Chain

`lsusb -t` and sysfs reported:

1. Raspberry Pi USB 2 root hub at 480 Mb/s.
2. VIA Labs `2109:3431` four-port hub at 480 Mb/s.
3. Terminus Technology `1a40:0101` four-port downstream hub at 480 Mb/s.
4. Four Espressif `303a:1001` USB JTAG/serial devices on the four downstream ports, each at 12 Mb/s:
   - `E0:72:A1:F9:9C:F8`
   - `E0:72:A1:F9:9C:C0`
   - `E0:72:A1:F9:A1:90`
   - `E0:72:A1:F9:B3:E4`
5. Touch controller `8888:6666` at 12 Mb/s.
6. Phison `13fe:6700` removable `USB DISK 3.0` at 480 Mb/s.

The four ESP32 USB descriptors each declare 500 mA maximum; the removable drive declares 300 mA; both hubs declare 100 mA; and the touch controller declares 100 mA. These descriptor ceilings are not simultaneous measured consumption and must not be summed as a battery-sizing result. The installed chain's four-camera data function is supported separately by the recorded 40/40 repeated transfer run; aggregate electrical power still requires suitable instrumentation.
