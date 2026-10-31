"""CLI entry point for image stitching."""

import argparse
from pathlib import Path

import cv2

from .metrics import print_metrics, save_metrics
from .pipeline import stitch_images


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def main():
    parser = argparse.ArgumentParser(
        description="Stitch overlapping images into a panorama."
    )
    parser.add_argument(
        "--images",
        required=True,
        type=Path,
        help="Directory containing images in left-to-right order.",
    )
    parser.add_argument(
        "--detector",
        choices=["sift", "orb", "surf"],
        default="sift",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/stitching"),
    )

    args = parser.parse_args()

    if not args.images.is_dir():
        parser.error(f"Image directory does not exist: {args.images}")

    image_paths = sorted(
        path
        for path in args.images.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
    )

    if len(image_paths) < 2:
        parser.error("The input directory must contain at least two images.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    try:
        panorama, metrics = stitch_images(image_paths, args.detector)
    except (ValueError, RuntimeError, cv2.error) as exc:
        parser.exit(1, f"Stitching failed: {exc}\n")

    panorama_path = args.output_dir / f"panorama_{args.detector}.jpg"
    metrics_path = args.output_dir / f"metrics_{args.detector}.json"

    if not cv2.imwrite(str(panorama_path), panorama):
        parser.exit(1, "Could not save panorama image.\n")

    save_metrics(metrics, metrics_path)
    print_metrics(metrics)

    print(f"\nPanorama saved to: {panorama_path}")
    print(f"Metrics saved to:  {metrics_path}")


if __name__ == "__main__":
    main()