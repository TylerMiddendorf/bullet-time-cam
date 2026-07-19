# Capture-Time Library Previews - 2026-07-19

## Outcome

App 0.2.9 generates `library_preview.jpg` while building every complete or
usable partial capture set. The 240x135-bounded JPEG is published atomically
with the originals, animation, and manifest. Its manifest record includes byte
count, CRC32, width, and height.

The media catalog reads this small file directly for every new capture instead
of opening and decoding its animated GIF. Existing schema-2 capture sets remain
compatible: only the initially visible six legacy entries use the prior
first-frame GIF fallback.

## Revision and Automated Checks

- Implementation commit: `ea9e4c5` (`Generate library previews during capture`)
- Application version: `0.2.9`
- The commit was pushed to `origin/main` and fast-forward pulled by the clean
  `/home/username/bullet-time-cam` checkout on `camerapi`.
- Windows and Raspberry Pi each passed 128 deterministic tests; the single
  environment-gated live-ledger test skipped as expected.
- Repository formatting, linting, hygiene, and push hooks passed.
- Coverage verifies preview creation and manifest validation, all-entry preview
  availability beyond the first page, zero GIF decoding when previews exist,
  and bounded legacy fallback behavior.

## Raspberry Pi Hardware Verification

- The product volume was `/dev/sda1`, mounted read/write at
  `/media/username/USB DISK`; all four stable ESP32 serial paths were present.
- One normal GPIO17 hardware trigger created complete capture
  `20260719T224502Z_b091c2b9` with Cameras 1-4 successful and app version 0.2.9.
- Capture-set time was 2,407.602 ms. The set contains four CRC-valid originals,
  the ordered six-frame GIF, the manifest, and `library_preview.jpg`.
- The preview is a 1,602-byte, 180x135 JPEG with manifest CRC32 `4e50cd29`.
- The evidence validator accepted the complete capture and all four camera
  identities. The production catalog returned the new capture as its latest
  entry, exposed its preview as `image/jpeg`, and scanned the four-entry product
  library in 0.081 seconds.
- The live Qt service was restarted and reported active/running, zero restarts,
  and exit status 0. All 39 boot/session checks passed.

## Scope and Compatibility

No existing capture set was rewritten. Deleting a set continues to remove its
entire validated directory, so the preview is deleted with its originals, GIF,
and manifest. The firmware was not changed or reflashed; this is a Raspberry Pi
capture-pipeline and library optimization.
