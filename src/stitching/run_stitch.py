"""CLI entry point supporting both README glob arguments and directory input."""

import argparse
from glob import glob, has_magic
from pathlib import Path

import cv2

from .metrics import append_run_metrics, print_metrics, save_metrics
from .pipeline import stitch_images

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def resolve_images(pattern: str) -> list[Path]:
    """Expand quoted globs on Windows, or enumerate an image directory."""
    directory = Path(pattern)
    if directory.is_dir():
        paths = list(directory.iterdir())
    elif has_magic(pattern):
        paths = [Path(name) for name in glob(pattern)]
    else:
        raise ValueError(f"Image directory or glob pattern does not exist: {pattern}")
    return sorted((p for p in paths if p.is_file() and
                   p.suffix.lower() in SUPPORTED_EXTENSIONS),
                  key=lambda p: p.name.lower())


def main():
    parser = argparse.ArgumentParser(description="Stitch overlapping images into a panorama.")
    parser.add_argument("--images", required=True,
                        help='Image directory or quoted glob, e.g. "data/stitching/*.png"')
    parser.add_argument("--detector", choices=["sift", "orb", "surf"], default="sift")
    parser.add_argument("--out", type=Path, default=None,
                        help="Exact output panorama image path.")
    parser.add_argument("--output-dir", type=Path, default=Path("results/stitching"),
                        help="Legacy output directory (used when --out is omitted).")
    parser.add_argument("--metrics-out", type=Path, default=None,
                        help="CSV path; append one summary row per successful run.")
    args = parser.parse_args()

    try:
        image_paths = resolve_images(args.images)
    except ValueError as exc:
        parser.error(str(exc))
    if len(image_paths) < 2:
        parser.error(f"At least two images are required; found {len(image_paths)} matching files.")

    panorama_path = args.out if args.out is not None else args.output_dir / f"panorama_{args.detector}.jpg"
    if panorama_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        parser.error("--out must be an image filename (.jpg, .png, etc.).")
    panorama_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path = (args.output_dir if args.out is None else panorama_path.parent) / f"metrics_{args.detector}.json"

    try:
        panorama, metrics, timing = stitch_images(image_paths, args.detector, return_timing=True)
        if not cv2.imwrite(str(panorama_path), panorama):
            raise RuntimeError(f"Could not save panorama image: {panorama_path}")
        save_metrics(metrics, metrics_path)
        if args.metrics_out is not None:
            append_run_metrics(metrics, args.metrics_out,
                               image_set=str(image_paths[0].parent), detector=args.detector,
                               image_count=len(image_paths),
                               stitching_time_ms=timing["stitching_time_ms"],
                               detection_time_ms=timing["detection_time_ms"])
    except (OSError, ValueError, RuntimeError, cv2.error) as exc:
        parser.exit(1, f"Stitching failed: {exc}\n")

    print_metrics(metrics)
    print(f"\nPanorama saved to: {panorama_path}")
    print(f"Pair metrics saved to: {metrics_path}")
    if args.metrics_out is not None:
        print(f"CSV summary appended to: {args.metrics_out}")


if __name__ == "__main__":
    main()
