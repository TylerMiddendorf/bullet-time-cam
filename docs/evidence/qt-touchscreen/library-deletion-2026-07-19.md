# Library and Viewer Deletion - Raspberry Pi Evidence

Date: July 19, 2026

Final deployed commit: `3f99e76` (`Prevent viewer footer text overlap`)

Feature commit: `95961ff` (`Add confirmed library media deletion`)

## Scope and safety boundary

- Delete is available from both the removable-media library and detached GIF
  viewer.
- The user must confirm a modal that names the selected capture set, states
  that its original JPEGs, animation GIF, and manifest will be deleted, and
  states that the action cannot be undone.
- The filesystem operation revalidates the schema-2 published set immediately
  before deletion, rejects symlinked or non-directory targets, and requires the
  target's resolved parent to equal the active removable-USB capture root.
- The complete capture-set directory is removed so JPEG originals and the GIF
  cannot become orphans. Rename, editing, sharing, and boot-card operations are
  not exposed.

## Automated results

- Windows development host: 118 tests discovered; 117 passed and the one
  environment-gated live-evidence test skipped as expected.
- Repository pre-commit hooks passed, including JSON checks, merge/private-key
  checks, whitespace/line-ending checks, Ruff lint, and Ruff formatting.
- The pre-push gate repeated the full deterministic Python suite successfully
  for both commits.
- Raspberry Pi at final commit `3f99e76`: 118 tests ran in 2.242 seconds; 117
  passed and the same live-evidence test skipped.
- The production QML tree loaded offscreen on the Pi with PySide6 after the
  final pull and emitted no QML error.

The focused tests cover confirmation, cancellation, successful refresh,
drive-removal failure presentation, exact-set removal, adjacent-set retention,
changed-manifest rejection, and rejection of entries outside the active root.

## Native 800x480 route evidence

The final Pi-rendered routes both passed first-frame, root-object, object lookup,
viewport, and zero-QML-error checks:

| Render | SHA-256 |
| --- | --- |
| Corrected viewer with Delete action | `eb3f6b4206b40a076189ce251289567c702ed4195a779f10e793e3a403fe0037` |
| Irreversible delete confirmation | `38043707dd4caf34d82af7896d137d68e1d7e496f3bff6214f8057ec53d87432` |

Visual inspection found a footer-label collision in the initial feature render.
Commit `3f99e76` added bounded text fitting; the corrected viewer render shows
separate playback, view-count, Delete, and Back controls without overlap. The
confirmation render keeps the capture ID, consequence text, Cancel, and Delete
Permanently controls inside the 800x480 viewport.

## Real removable-USB deletion check

The product drive was mounted read/write from `/dev/sdb1` at
`/media/username/USB DISK`. A disposable published set named
`codex_delete_test_95961ff` was created directly below `BulletTime/` with:

- `camera_1.jpg` through `camera_4.jpg`
- `bullet_time.gif`
- `manifest.json`

The catalog grew from 219 to 220 valid entries. Its GIF decoded into two
detached viewer frames before deletion. The production deletion function then
removed the set and the catalog returned to 219 entries. The target no longer
existed, and the complete name set of all 222 pre-existing capture directories
was unchanged. No user capture was selected or deleted. A final check confirmed
the disposable directory remained absent.

## Deployed runtime

- Pi checkout: clean `3f99e76`
- `bullet-time-ui.service`: active after restart; PID 4065 at the recorded check
- Runtime command: `python -m pi_app.bullettime.main --config pi_app/config.json`
- GPIO17: output LOW after deployment
- Boot/session verifier: all 37 checks passed
- Product USB capture-directory count after cleanup: 222

The Pi does not retain a persistent user journal, so the absence of journal
warnings is not used as evidence. Native route smokes, production-QML loading,
service state, controller tests, and the real removable-storage operation are
the concrete verification layers.
