# V1 Qt Touchscreen UX Specification

Status: testable engineering specification for the independent Qt migration
track. Confirmed product decisions are cited by repository path; dimensions,
colors, timing thresholds, and Qt object names below are proposed acceptance
details until accepted by the product owner.

Normative words `MUST`, `MUST NOT`, `SHOULD`, and `MAY` describe validation
requirements for this track.

## 1. Product and Display Boundary

- The logical viewport MUST be exactly 800x480 in landscape orientation.
- Content MUST fill the viewport with no desktop chrome, title bar, cursor,
  scroll bars, or operating-system diagnostics.
- All product screens MUST use an opaque black or image-backed root; no
  unpainted Qt surface may flash during startup or transitions.
- Touch targets MUST be at least 48x48 logical pixels. The primary capture
  target MUST be at least 680x72 and centered horizontally.
- The UI MUST remain legible without depending on animation, color alone, or
  fine details smaller than two logical pixels.
- The screen MUST NOT show battery percentage, battery icons, charging state,
  remaining runtime, power-source state, or low-battery warnings. The external
  pack is the V1 charge indicator.
- The screen MUST NOT show or imply a live camera feed. The deterministic
  `assets/ui/preview-placeholder.png` fixture MAY be used for layout and
  headless tests. Whenever it is visible, the surface MUST overlay
  the exact text `STATIC PLACEHOLDER`; the UI MUST never use `LIVE` or imply that
  the fixture came from camera transport.
- The validation route selector MUST be test-only. A deterministic route is not
  automatically a shipped V1 feature or part of production navigation.
- No route may render a hotspot state or claim network availability.
- Unsupported camera settings MUST be disabled and MUST NOT call a node
  command, transport, or configuration API.

## 2. Visual Language

The seven files in `designs/ux-mockups/` are the route composition sources.
Every file is exactly 1619x971. The implementation MUST create native 800x480
Qt layouts and MUST NOT scale or use those mockup rasters as screen backgrounds.
Bounds below are deliberate 800x480 layout specifications, not scaled mockup
coordinates. Designs 4-7 are adapted validation compositions, not authority to
expand shipped product scope.

### 2.1 Palette

| Token | Value | Required use |
| --- | --- | --- |
| `surface` | `#000000` | Default background |
| `primaryText` | `#F4F6F8` | Main headings and instructions |
| `mutedText` | `#808890` | Waiting/inactive labels |
| `accentBlue` | `#58A8ED` | Capture affordance and active progress |
| `readyGreen` | `#5BD477` | Connected/saved success |
| `progressAmber` | `#FFB72B` | Current processing phase |
| `errorRed` | `#FF5E63` | Failed camera and blocking error |
| `divider` | `#4B4F54` | Header and panel separators |

Colors MAY be adjusted after panel measurement, but screenshots MUST maintain
at least 4.5:1 contrast for body text and 3:1 for large text and essential
icons. Status MUST also be conveyed by text or shape.

### 2.2 Type and motion

- Use the installed sans-serif family with a semibold face for headings and a
  regular/medium face for detail text. The UI MUST not depend on a font absent
  from a stock Raspberry Pi OS installation.
- Body/status text MUST be at least 18 px. Primary instructions MUST be at
  least 24 px. State headings SHOULD be 42-64 px where the layout permits.
- Letter spacing visible in the mockups MAY be reduced to preserve complete,
  unclipped messages at 800x480.
- The capture-progress animation SHOULD update at 30-60 Hz but MUST not control
  workflow timing. The review GIF MUST honor its encoded frame durations,
  clamped to at least 20 ms per frame.
- Essential state changes MUST remain understandable when all decorative
  animation is disabled.

## 3. Persistent Header

The READY and REVIEW families use a header occupying `x=0..799`, `y=0..78`.
CAPTURE_PROGRESS uses the full canvas and MAY omit this header.

- `productMark` (`x=18..92`, minimum 60x42): repository product mark, aspect
  preserved.
- `cameraStrip` (`x=145..455`): four numbered indicators in stable logical
  order, each at least 48x48. Green ring means connected/successful; red outline
  plus number means failed; gray outline means unavailable/waiting.
- `storageBadge` (`x=610..790`, minimum 150x48): visible text `USB READY` before
  capture and `USB SAVED` after a committed result. A blocking storage fault
  replaces it with `USB ERROR` in red.
- There is no battery compartment, battery spacer, or reserved power-status
  region. Header layout MUST end at `storageBadge`; it MUST NOT preserve the
  mockup battery icon's divider or empty slot.
- A one-pixel divider at `y=78` separates the header from body content.

Names in backticks are stable semantic identifiers used by the contract and
test descriptions. Runtime QML MAY expose matching `objectName` values when a
test needs direct lookup; a name in this document alone is not proof that such
a lookup hook exists.

## 4. States and Screens

### 4.1 STARTING

Entry: Qt process creates its first surface.

- `startupLogo` MUST render `assets/Logo_800x480.png` with aspect-preserving
  containment on black before receiver discovery status is presented.
- It MUST cover the full 800x480 surface on the first rendered frame.
- There MUST be no pointer, intermediate blank/white frame, status text, or
  desktop content between the compositor logo and this frame.
- STARTING is non-interactive. Touch MUST NOT request capture.

Exit: the receiver publishes READY or ERROR.

### 4.2 READY_EMPTY

Entry: at least one registered camera session publishes READY, no latest review
is retained, and writable USB storage resolves successfully.

- Persistent header is visible.
- `readyGlyph` occupies approximately `x=80..285`, `y=130..335` and uses the
  blue aperture motif from `01-v1-ready.png` or a code-native equivalent.
- `stateHeading` reads `READY`.
- `stateDetail` reads `N OF 4 CAMERAS CONNECTED`, using the actual `N`.
- The bottom row contains a gear-icon Settings target, Library, and Capture.
- Ready MUST NOT enqueue `CAPTURE`; its Capture target navigates to `/capture`.
- The physical shutter remains independent of touchscreen route navigation.
- If `N < 4`, the screen MAY remain ready only if the runtime permits that
  workflow; it MUST show the true count and gray missing camera indicators.

### 4.3 READY_WITH_LATEST

Entry: READY arrives while a successfully loaded latest review is retained.

- The latest animation remains visible and playing; READY MUST NOT discard it.
- The persistent header and navigation targets remain available.
- A successful review carries no error banner. A retained partial review keeps
  its camera-specific banner until a new capture begins.

This state preserves the confirmed requirement that the latest result remains
displayed until the next capture.

### 4.4 CAPTURE_PROGRESS

Entry: the first accepted LOADING event after READY/REVIEW or an observed
physical capture start.

- The previous review MUST disappear before progress content is shown.
- `progressHeading` reads `CREATING BULLET-TIME` near `y=24`.
- `progressHero` is centered in approximately `x=300..500`, `y=65..255` and
  provides a non-blocking indeterminate ring.
- `cameraProgress1` through `cameraProgress4` occupy four equal columns in
  `x=120..680`, `y=260..385`. Each exposes a camera number and one of
  `WAITING`, `CAPTURING`, `TRANSFERRING`, `COMPLETE`, or `FAILED`.
- `phaseRail` near `y=410` exposes exactly three ordered phases:
  `CAPTURING`, `TRANSFERRING`, and `BUILDING ANIMATION`. Completed phases are
  blue, the active phase amber, and future phases gray.
- `steadyHint` reads `KEEP CAMERA STEADY` while any camera is capturing or
  transferring.
- The screen MUST remain in progress while work is actively advancing, even
  beyond the soft two-second target. It MUST NOT display a fabricated percent
  or countdown.
- Touch is disabled throughout CAPTURE_PROGRESS. Physical or touch attempts
  MUST NOT queue a second capture.
- Runtime messages that lack structured per-camera progress MUST map
  conservatively: unknown cameras remain `WAITING`, a named started camera
  becomes `CAPTURING`, a named failure becomes `FAILED`, and the global phase
  stays at the latest evidenced phase. The UI MUST NOT invent completion.

Exit: REVIEW_COMPLETE, REVIEW_PARTIAL, or ERROR_BLOCKING.

### 4.5 REVIEW_COMPLETE

Entry: REVIEW event includes a loadable committed GIF.

- The GIF fills the area below the 78 px header using aspect-preserving crop or
  containment; faces/subjects MUST not be distorted.
- The header camera indicators are all green and `storageBadge` reads
  `USB SAVED`.
- A translucent bottom panel contains navigation to Capture, Viewer, and
  Library.
- The GIF loops until the next capture begins. Decoded frames MUST be detached
  from removable media so unplugging the drive after load does not stop Qt event
  processing.
- The Capture target navigates to `/capture`; Review MUST NOT queue a shot.

### 4.6 REVIEW_PARTIAL

Entry: REVIEW_WITH_ERROR includes a loadable committed GIF made from at least
two successful views.

- Review media behavior matches REVIEW_COMPLETE.
- Successful camera indicators are green; every failed logical camera is red.
- `partialHeading` reads `SAVED WITH N VIEWS`, using the manifest/result count.
- `partialDetail` names every failed logical camera, for example
  `CAMERA 4 DID NOT RESPOND`. If the raw diagnostic differs, user-facing text
  stays bounded while the journal/manifest retains full detail.
- The bottom Capture action navigates to `/capture`.
- Failure identity MUST come from logical camera IDs, never transient serial
  port names.

### 4.7 ERROR_BLOCKING

Entry: ERROR without a usable retained review, a storage failure during capture,
no camera nodes, or review-media load failure.

- The screen uses a black background, red `errorHeading`, white actionable
  detail, and a retry/capture action only when the runtime can safely accept it.
- Storage messages MUST use the existing compact meanings: unavailable, full,
  read-only, mount failure, or removed/I/O failure. Each names USB storage and
  gives a next action in no more than three lines of at most 48 characters.
- Camera connection errors MUST include stable logical camera number when
  known. Raw `/dev/tty*` paths MUST not be the primary user-facing identity.
- If the prior review was loaded and no new capture has begun, a non-capture
  error MAY overlay that review. Once capture begins, an error MUST NOT restore
  stale review imagery behind a current failure.
- A review-media load failure reads `REVIEW UNAVAILABLE`, explains that the USB
  drive was removed, and permits recovery without terminating the event loop.

### 4.8 CAPTURE

Route: `/capture`; visual source:
`designs/ux-mockups/04-fast-follow-live-preview.png`.

- The route MUST use only `assets/ui/preview-placeholder.png` as its image-like
  content and MUST render `STATIC PLACEHOLDER` over that asset.
- It MUST also render `CAMERA VIEW NOT CONNECTED`. It MUST NOT render `LIVE`, create
  a camera-stream object, open camera transport, or import Qt Multimedia.
- It shows exactly four camera identities and USB readiness without battery,
  Wi-Fi, hotspot, timer, or user-setting claims.
- It is the only touchscreen route allowed to emit the existing product
  `CAPTURE` command. It also navigates to Settings or Ready and emits no node
  setting commands.

### 4.9 FOUR_CAMERA_CONTROL_CENTER test route

Route: `/control-center`; visual source:
`designs/ux-mockups/05-ideal-future-control-center.png`.

- The header MUST report the connected count out of four and render exactly
  Cameras 1-4. It MUST NOT retain the source concept's 12-camera, battery, or
  hotspot regions.
- Exposure, white balance, smooth motion, and interpolation rows MUST be
  visibly marked `V2 · DISABLED` beneath a `SETTINGS` heading.
- Disabled setting objects MUST have no signal binding capable of sending a
  node command. The route's `node_commands` contract remains an empty list.
- Its Capture target navigates to `/capture`; the control center MUST NOT emit
  `CAPTURE`. Its other active targets navigate to Ready or Library; settings
  remain inert.

### 4.10 REMOVABLE_MEDIA_LIBRARY test route

Route: `/library`; visual source:
`designs/ux-mockups/06-library-navigation.png`.

- Entries MUST come only from committed capture directories on the selected
  removable USB filesystem. The route MUST fail closed when that filesystem is
  unavailable and MUST NOT enumerate or display boot-card media.
- The library supports scrolling, selection, open viewer, confirmed deletion,
  and back to camera/control. Delete MUST target only a revalidated published
  capture-set directory directly below the active removable-USB root and MUST
  remove its JPEG originals, GIF, and manifest together. It MUST require an
  explicit irreversible-action confirmation. Rename, share, repair, and other
  write actions remain prohibited.
- Thumbnails and metadata load asynchronously or from deterministic fixtures;
  enumeration and decode MUST NOT block the GUI thread for 33 ms.
- Removal during enumeration or after thumbnail load MUST produce a bounded USB
  error while the event loop survives. Already-decoded thumbnail data MUST not
  retain an open removable-media file handle.

### 4.11 REAL_GIF_VIEWER test route

Route: `/viewer`; visual source:
`designs/ux-mockups/07-gif-viewer.png`.

- A worker MUST decode the selected real `image/gif` with Pillow into detached
  PNG data-URL frames before navigation to the viewer. QML presents those
  frames with `Image`; it MUST NOT import or depend on Qt Multimedia.
- Playback automatically loops using the GIF frame durations. The viewer
  supports back to the library and the same confirmed whole-set delete action;
  it emits no node command and no other storage mutation command.
- Unplugging the drive after decode MUST not stop playback, event polling, or
  navigation.
- Fixture evidence names the exact GIF and its SHA-256. Product evidence names
  the capture ID and committed manifest.

## 5. Event-to-State Contract

| Runtime input | Required transition |
| --- | --- |
| first Qt frame | STARTING |
| READY, no retained review | READY_EMPTY |
| READY, retained review | READY_WITH_LATEST |
| LOADING from READY/REVIEW | CAPTURE_PROGRESS; clear visible prior review |
| subsequent LOADING | update progress in place; never queue capture |
| REVIEW with valid image | REVIEW_COMPLETE |
| REVIEW_WITH_ERROR with valid image | REVIEW_PARTIAL |
| ERROR while capture active | ERROR_BLOCKING with no stale image |
| ERROR while idle partial review retained | retain REVIEW_PARTIAL and its original camera error |
| invalid/removed review image | ERROR_BLOCKING; continue polling |
| route `/capture` | static fixture; sole touchscreen capture command/backend |
| test route `/control-center` | four cameras; settings disabled; no node command |
| test route `/library` | removable-media enumeration and confirmed whole-set deletion |
| test route `/viewer` | real GIF decoded to detached PNG frames |

Events are processed on the Qt GUI thread through a queued signal or equivalent
thread-safe boundary. Receiver work, filesystem resolution, image decoding, and
manifest writes MUST NOT block the GUI thread long enough to miss two
consecutive 60 Hz frames (33 ms) in deterministic tests. Best-effort display
timing persistence MUST never crash or freeze the view if USB media disappears.

## 6. Acceptance Scenarios

The Qt migration is not accepted until all scenario IDs below have automated
headless evidence and the Pi-only subset has physical-device evidence.

| ID | Scenario | Required assertion |
| --- | --- | --- |
| UX-001 | First frame | 800x480 opaque startup logo; no cursor/OS content |
| UX-002 | Four-camera ready | Four green IDs, USB READY, single enabled capture target |
| UX-003 | Touch debounce | Ten rapid/multi-touch inputs queue one CAPTURE |
| UX-004 | Active capture | Prior review absent; touch disabled; phase does not regress |
| UX-005 | Long capture | Progress remains active past two seconds without false failure |
| UX-006 | Complete review | GIF animates, USB SAVED, all four green, next-capture target |
| UX-007 | Camera 4 partial | Three-view GIF plus explicit logical Camera 4 failure |
| UX-008 | Multiple failures | Every failed logical ID is visible; no transient port identity |
| UX-009 | Missing USB before touch | No trigger command; actionable USB unavailable screen |
| UX-010 | Full/read-only/mount/I-O USB | Correct compact message; no clipped text |
| UX-011 | Review drive removed | Event loop survives; REVIEW UNAVAILABLE; later READY/ERROR renders |
| UX-012 | READY after review | Latest review remains visible and animated |
| UX-013 | Error after new capture | Stale review is not restored |
| UX-014 | Geometry | Every screenshot is exactly 800x480; required bounds fit viewport |
| UX-015 | Scope guard | No battery/power region or live/video/stream label; the camera fixture says STATIC PLACEHOLDER |
| UX-016 | Shutdown | Receiver stop and Qt exit complete within service timeout |
| UX-017 | Capture route | Fixture says `STATIC PLACEHOLDER` and `CAMERA VIEW NOT CONNECTED`; sole touchscreen capture command |
| UX-018 | Four-camera control center | Exactly four IDs; no battery/hotspot region; settings disabled; no node commands |
| UX-019 | Removable-media library | Only committed USB captures; confirmed whole-set deletion; missing/removal fault survives |
| UX-020 | Real GIF viewer | Real GIF decodes to detached looping PNG frames; no Qt Multimedia import |
| UX-021 | Route screenshot matrix | Seven canonical screenshots are each exactly 800x480 with recorded SHA-256 |
| UX-022 | Wayland production gate | `QT_QPA_PLATFORM=wayland`; no Xwayland; bounded smoke has no warnings and a root object |

## 7. Evidence Rules

- A screenshot alone proves only rendering, not interaction or physical
  behavior.
- Headless results record Qt/PySide versions, render backend, display variables,
  scenario seed, assertions, screenshot SHA-256, and failure output.
- Raspberry Pi results additionally record commit, package versions, OS/kernel,
  display mode, service status, boot handoff observation, touch action count,
  GPIO trigger evidence, and rollback result.
- Any screenshot generated with fixture media is labeled `FIXTURE` in its
  evidence metadata. Product screenshots use a named capture ID and committed
  manifest.
- Unresolved clipping, missing assets/fonts, software-rendering differences,
  or Pi-only failures remain explicit; they are not converted into passes by a
  desktop headless result.

## 8. Runtime and cleanup contract

The target runtime is Debian 13 Trixie arm64 with its Qt/PySide 6.8 package
family. The exact explicit minimum is recorded in
`pi_app/system-requirements-qt.txt`: `python3-pyside6.qtquick`,
`qml6-module-qtquick-controls`, `qml6-module-qtquick-layouts`,
`qml6-module-qtqml-workerscript`, and `qt6-wayland`. Apt resolves their lower
level dependencies. Install `qml6-module-qtquick-effects` only if a QML file
actually imports `QtQuick.Effects`.

- Production MUST set `QT_QPA_PLATFORM=wayland`; relying on the default or on
  Xwayland is a failed migration gate.
- Headless tests use `offscreen`, software RHI, the basic render loop, and the
  Basic Controls style for deterministic comparisons.
- A bounded QML smoke MUST fail on any QML warning, a load timeout, or
  `rootObjects().length == 0`.
- The first Qt frame MUST be the opaque product logo. The first `frameSwapped`
  timestamp and logo-visible assertion are recorded independently.
- Shutdown MUST stop the receiver, join its worker within the service timeout,
  close serial ownership, and restore or confirm GPIO17 output LOW before Qt
  exits.
- The known Tk/X11 packages remain installed as recovery capability until an
  explicit rollback drill is performed and accepted. Their presence alone is
  not rollback evidence.
