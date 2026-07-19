# Ready/Capture/Library Navigation Reorganization - 2026-07-19

## Outcome

App 0.2.5 reorganizes the native 800x480 touchscreen flow:

- Ready retains USB state, all four camera badges, and READY/ATTENTION detail.
- Ready offers gear/Settings, Library, and Capture navigation but cannot enqueue
  a touchscreen photo.
- The former Preview Demo route and file are Capture.
- Capture is the only touchscreen route allowed to enqueue `CAPTURE`; Review
  and Settings navigate there.
- Media Demo and generic media-navigation labels are Library.
- The static camera fixture remains explicit: `STATIC PLACEHOLDER` and
  `CAMERA VIEW NOT CONNECTED`.

## Revision and Git Deployment

- Implementation: `afedfa8` (`Reorganize touchscreen capture navigation`)
- Canonical documentation: `c305cb1` (`Align UX documentation with capture flow`)
- Pi-discovered smoke-tool route fix: `d1ccc2e`
- Pi-rendered label fit corrections: `880a7b7`, `1d880c1`
- Final tested source: `1d880c159fee364b48040c429fa469907a7ef800`
- Deployment path: every change was committed and pushed to `origin/main`, then
  fast-forward pulled by `/home/username/bullet-time-cam` on `camerapi`.

## Automated and Native-Pi Evidence

- The final local suite passed 124 tests with the one environment-gated live
  evidence test skipped.
- The final Pi suite also passed 124 tests in 2.257 seconds with the same one
  expected skip.
- UX contract v4 passed all seven routes with zero errors.
- Ready, Capture, Settings, and Library each rendered through the Pi's native
  Wayland compositor at 800x480. Every bounded smoke reported one root object,
  `frame_swapped: true`, zero QML errors, and `status: PASS`.
- Visual review confirmed the gear glyph renders, all bottom navigation labels
  fit, Capture owns the only touchscreen shutter button, and the final static
  camera labels do not clip.
- The restarted product service ran app 0.2.5 at PID 5650 with `NRestarts=0`.
  Every boot/session verifier check passed; native Wayland remained active
  without Xwayland.
- The actual live service screen was captured after restart. With camera nodes
  not currently enumerated, it truthfully displayed four red camera badges and
  `ATTENTION` / `No camera nodes found` together with the new navigation.
- Product USB `/dev/sdb1` remained a read-write VFAT mount at
  `/media/username/USB DISK`.
- `pinctrl get 17` reported GPIO17 as output, pull-down, low, and `gpioinfo`
  showed the application's `lg` consumer.

## Artifacts

The five PNGs and exact hashes are recorded in
[`2026-07-19-navigation-routes/manifest.json`](2026-07-19-navigation-routes/manifest.json).
They include deterministic route-harness views plus the actual restarted
product-service display.

## Limitation

The four ESP32 camera nodes were not enumerated on USB during this deployment
pass. No new physical- or touchscreen-triggered four-camera capture was made.
The UI command boundary was exercised by the final Pi unit suite, native route
loading, and the restarted live service; previously qualified capture hardware
and media behavior are not represented as newly re-demonstrated here.
