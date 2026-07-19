# Ready and Library Navigation Icon Sizing - 2026-07-19

## Outcome

App 0.2.6 replaces the Library screen's `BACK TO CAMERA` label with a home
icon and makes both that icon and Ready's Settings gear fill most of their
touch targets. The home action continues to navigate directly to Ready.

## Revision and Deployment

- Initial implementation: `d436546` (`Enlarge Ready and Library navigation icons`)
- Pi-render-driven home-glyph correction: `4be243c` (`Increase Library home icon fill`)
- Final tested source: `4be243c80ca82af6cc1137cb6648a440b180ddae`
- Both commits were pushed to `origin/main` and fast-forward pulled by the clean
  `/home/username/bullet-time-cam` checkout on `camerapi`.

## Raspberry Pi Verification

- The complete deterministic Pi suite passed 124 tests in 2.253 seconds with
  only the expected environment-gated live-hardware evidence test skipped.
- Native Wayland Ready and Library route smokes each rendered at 800x480 with
  one root object, a frame swap, the required icon button, zero QML errors, and
  `status: PASS`.
- The final Library render `/tmp/4be243c-library.png` had SHA-256
  `d84f1d6aedbe80f04be70c9ff3c3ae61f75d4401e2403f4e227b30a4182a247c`.
  Visual inspection confirmed the home glyph occupies most of the 235x58
  button without clipping.
- A native QML interaction smoke invoked the deployed `homeButton.tapped`
  signal from Library and confirmed that Ready loaded by finding its
  `settingsButton`.
- The restarted live service ran as PID 6265 with `NRestarts=0`, exit status 0,
  and active/running state. Every boot/session verifier check passed, including
  native Wayland operation and absence of Xwayland.
- The live compositor capture `/tmp/4be243c-live.png` had SHA-256
  `f85c1438a17a554ce4718b29729570eda0c72ded6ec55bc245795dee754d02f9`.
  It showed the enlarged Settings gear on the actual product Ready screen.

## Limitation

The camera nodes were not enumerated during this UI-only deployment, so the
live Ready screen truthfully showed `ATTENTION` / `No camera nodes found`.
This pass validates the icon rendering, navigation, deployment, and service
health; it is not new four-camera capture evidence.
