# Qt Touchscreen UX Evidence - <date and run label>

Status: `PASS | PARTIAL | FAIL`

## Identity

| Field | Value |
| --- | --- |
| Date/time with timezone | `<YYYY-MM-DDTHH:MM:SS±HH:MM>` |
| Operator | `<name>` |
| Host | `<CI / workstation / Raspberry Pi>` |
| Git commit and dirty state | `<sha; clean/dirty plus paths>` |
| Baseline commit | `1ef1ba6` |
| Raspberry Pi OS/kernel | `<value or N/A>` |
| Python / PySide6 / Qt | `<versions>` |
| Qt platform / renderer | `<offscreen|minimal|wayland; software|hardware>` |
| Display | `<800x480 mode and connector or virtual>` |
| Fixture or physical media | `<FIXTURE name or capture ID>` |
| Expected deploy SHA | `<workstation commit>` |
| Remote branch SHA | `<git ls-remote result>` |
| Pi pre-pull / post-pull SHA | `<sha> / <sha>` |
| Service environment | `<include QT_QPA_PLATFORM>` |
| QML root objects / warnings | `<count> / <count>` |
| First frameSwapped | `<monotonic timestamp or delta>` |

## Commands

```text
<exact setup and validation commands>
```

## Automated Scenario Results

| Scenario | Result | Duration | Screenshot / log | SHA-256 | Notes |
| --- | --- | ---: | --- | --- | --- |
| UX-001 | `<PASS/FAIL>` | `<ms>` | `<path>` | `<hash>` | `<notes>` |
| UX-002 | | | | | |
| UX-003 | | | | | |
| UX-004 | | | | | |
| UX-005 | | | | | |
| UX-006 | | | | | |
| UX-007 | | | | | |
| UX-008 | | | | | |
| UX-009 | | | | | |
| UX-010 | | | | | |
| UX-011 | | | | | |
| UX-012 | | | | | |
| UX-013 | | | | | |
| UX-014 | | | | | |
| UX-015 | | | | | |
| UX-016 | | | | | |
| UX-017 | | | | | |
| UX-018 | | | | | |
| UX-019 | | | | | |
| UX-020 | | | | | |
| UX-021 | | | | | |
| UX-022 | | | | | |

## Seven-Route Screenshot Matrix

| Design / route | Source raster | Native screenshot | SHA-256 | Required route-specific evidence |
| --- | --- | --- | --- | --- |
| 01 ready | `1619x971` | `01-ready-800x480.png` | | Four IDs, USB READY, one capture target |
| 02 progress | `1619x971` | `02-progress-800x480.png` | | No stale review; no touch command |
| 03 partial review | `1619x971` | `03-partial-review-800x480.png` | | Logical failed camera and real/fixture GIF |
| 04 static preview placeholder | `1619x971` | `04-static-preview-placeholder-800x480.png` | | `DEMO PLACEHOLDER`; `PREVIEW NOT CONNECTED`; no backend |
| 05 four-camera control center | `1619x971` | `05-four-camera-control-center-800x480.png` | | Four IDs; disabled settings; zero node commands |
| 06 removable-media library | `1619x971` | `06-removable-media-library-800x480.png` | | USB-only, read-only catalog |
| 07 GIF viewer | `1619x971` | `07-gif-viewer-800x480.png` | | Named real GIF; `AnimatedImage`; no Qt Multimedia |

## Pi Deployment and Boot Handoff

| Check | Result | Concrete evidence |
| --- | --- | --- |
| Preflight and backup completed | `<PASS/FAIL>` | `<backup path and checksums>` |
| Qt runtime imports from service venv | | |
| QML/assets resolve without fallback | | |
| Service remains active after restart | | |
| First frame is product logo | | `<photo/video name>` |
| No OS text, desktop, pointer, or blank flash | | `<photo/video name>` |
| Touch queues exactly one capture | | `<journal/capture ID>` |
| Physical shutter still works | | `<capture ID>` |
| Four stable camera IDs enumerate | | `<command/log>` |
| USB capture is committed off boot card | | `<manifest storage fields>` |
| Shutdown completes within service timeout | | `<journal timing>` |
| `QT_QPA_PLATFORM=wayland` in service | | `<systemctl show/cat>` |
| No Xwayland after switch | | `<pgrep result>` |
| Bounded QML smoke has no warnings and root count > 0 | | `<smoke JSON>` |
| First `frameSwapped` metric recorded | | `<metric/log>` |
| Receiver stop/join, serial close, GPIO17 LOW cleanup | | `<journal/GPIO evidence>` |
| Review media detached before drive removal | | `<test/log>` |

## Pre-Switch Pi Baseline

Recheck rather than copying these values into a pass. The verified starting
facts at clean commit `1e6a6e7` were service PID `5111`, GPIO17 output LOW, all
four stable UIDs present, UI-only serial ownership, product USB read-write,
1.4 GiB free RAM, 6.5 GiB free root, 37 C, and `get_throttled=0`.

| Fact | Rechecked value | Result | Evidence |
| --- | --- | --- | --- |
| Git clean / SHA | | | |
| Service state / PID | | | |
| GPIO17 output LOW | | | |
| Four stable UIDs | | | |
| UI-only serial owner | | | |
| Product USB read-write | | | |
| Free RAM / root | | | |
| Temperature / throttling | | | |
| Terminus `error -71` since baseline | | | `<kernel/service lines or none observed>` |

## Fault and Recovery Evidence

For each exercised fault, record the injection, visible text, filesystem result,
service result, recovery action, and first successful post-recovery capture.

| Fault | Injection | Visible result | Filesystem/service result | Recovery evidence |
| --- | --- | --- | --- | --- |
| Missing USB | | | | |
| Full USB | | | | |
| Read-only USB | | | | |
| Unmountable USB | | | | |
| Removal after review load | | | | |
| Camera unavailable | | | | |
| Terminus hub `error -71` disconnect/recovery | | | | |

## Actual Touchscreen / Rig Tests

| Test | Result | Capture / artifact | Concrete evidence |
| --- | --- | --- | --- |
| Touch outside target emits no capture | | | |
| One real touch emits one GPIO17 capture | | | |
| Physical shutter remains independent | | | |
| Controlled partial capture | | | |
| Removal after review decode | | | |
| Read-only USB library | | | |
| Clean stop/join/serial/GPIO cleanup | | | |
| Reboot logo/Wayland/no-Xwayland | | | |
| Post-reboot touch capture | | | |

## Scope Audit

- [ ] No live camera stream or live-preview pipeline was exercised or claimed.
- [ ] The only preview-like asset is `assets/ui/preview-placeholder.png`.
- [ ] Whenever the preview fixture is visible, it says `DEMO PLACEHOLDER` and
      never `LIVE`.
- [ ] No battery level, icon, charge, power-source, or battery-status UI appears.
- [ ] No empty battery compartment, divider, spacer, or reserved header region
      remains.
- [ ] No enabled settings, media mutation, Wi-Fi control, hotspot claim, or
      12-camera UI appears; library/control-center content is confined to its
      bounded validation route.
- [ ] The control-center test route has exactly four cameras; unsupported
      settings are disabled and emit no node commands.
- [ ] The library test route reads only removable USB and offers no mutation.
- [ ] The viewer test route uses a real GIF through `AnimatedImage` without Qt
      Multimedia.
- [ ] `docs/MILESTONE_4_PLAN.md` is unchanged from the track baseline.

## Rollback Drill

| Field | Value |
| --- | --- |
| Rollback trigger used | `<health-gate/manual/failure>` |
| Pre-rollback Qt service state | `<value>` |
| Restored service/unit/config paths | `<paths>` |
| Restored Git commit | `<sha>` |
| Expected / remote / Pi deployed SHA | `<sha> / <sha> / <sha>` |
| Post-rollback Tk service state | `<active/inactive>` |
| Post-rollback boot observation | `<evidence>` |
| Post-rollback capture ID | `<capture ID>` |
| Media/filesystem validation | `<result>` |
| Receiver stop/join and GPIO cleanup | `<result and timing>` |

## Deviations and Open Failures

- `<requirement/scenario>` - `<observed result>` - `<owner/follow-up>`

## Conclusion

State exactly what this run demonstrates and what it does not. Do not mark the
Qt migration accepted unless every required scenario and the Pi deployment/
rollback gates pass with named evidence.
