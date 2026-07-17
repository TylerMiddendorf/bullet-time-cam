"""Generate deterministic, ignored JPEGs for the offline four-camera workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw


def prepare_sample_photos(root: Path, *, force: bool = False) -> list[Path]:
    """Create six complete sets and one Camera-4-missing set below ``root``."""
    created_or_existing: list[Path] = []
    for capture_number in range(1, 8):
        camera_ids = range(1, 4) if capture_number == 7 else range(1, 5)
        for camera_id in camera_ids:
            camera_dir = root / f"cam{camera_id}"
            camera_dir.mkdir(parents=True, exist_ok=True)
            path = camera_dir / f"photo_{capture_number:04d}.jpg"
            created_or_existing.append(path)
            if path.exists() and not force:
                continue
            color = (
                35 + camera_id * 38,
                30 + capture_number * 22,
                150 + (camera_id * capture_number * 9) % 90,
            )
            image = Image.new("RGB", (800, 600), color)
            draw = ImageDraw.Draw(image)
            draw.rectangle((40, 40, 760, 560), outline="white", width=8)
            draw.text(
                (70, 80),
                f"Bullet-Time local sample\nCamera {camera_id}\nCapture {capture_number}",
                fill="white",
                spacing=12,
            )
            image.save(path, format="JPEG", quality=90, optimize=True)
    return created_or_existing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "photos",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    paths = prepare_sample_photos(args.output, force=args.force)
    print(f"Prepared {len(paths)} ignored sample images below {args.output.resolve()}")


if __name__ == "__main__":
    main()
