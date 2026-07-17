# Local Sample Photos

This directory is intentionally present in the repository, but its image files
are always ignored. Do not force-add captures, generated samples, or other media
from this directory.

To create a deterministic local dataset for the offline four-camera workflow:

```bash
python -m pi_app.tools.prepare_sample_photos
```

The command creates complete capture sets `photo_0001` through `photo_0006`
under `cam1/` through `cam4/`. It also creates `photo_0007` for Cameras 1-3
while deliberately omitting Camera 4, matching the partial-set scenario in the
Milestone 1 plan. Existing files are preserved unless `--force` is supplied.

Real camera captures can use the same directory layout. They remain local and
must never be committed.
