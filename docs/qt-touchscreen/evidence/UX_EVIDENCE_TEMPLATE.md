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

## Scope Audit

- [ ] No live camera stream or live-preview pipeline was exercised or claimed.
- [ ] The only preview-like asset is `assets/ui/preview-placeholder.png`.
- [ ] Whenever the preview fixture is visible, it says `DEMO PLACEHOLDER` and
      never `LIVE`.
- [ ] No battery level, icon, charge, power-source, or battery-status UI appears.
- [ ] No empty battery compartment, divider, spacer, or reserved header region
      remains.
- [ ] No settings, library, deletion, Wi-Fi control, or 12-camera UI appears.
- [ ] `docs/MILESTONE_4_PLAN.md` is unchanged from the track baseline.

## Rollback Drill

| Field | Value |
| --- | --- |
| Rollback trigger used | `<health-gate/manual/failure>` |
| Pre-rollback Qt service state | `<value>` |
| Restored service/unit/config paths | `<paths>` |
| Restored Git commit | `<sha>` |
| Post-rollback Tk service state | `<active/inactive>` |
| Post-rollback boot observation | `<evidence>` |
| Post-rollback capture ID | `<capture ID>` |
| Media/filesystem validation | `<result>` |

## Deviations and Open Failures

- `<requirement/scenario>` - `<observed result>` - `<owner/follow-up>`

## Conclusion

State exactly what this run demonstrates and what it does not. Do not mark the
Qt migration accepted unless every required scenario and the Pi deployment/
rollback gates pass with named evidence.
