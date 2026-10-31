"""Generate a reproducible synthetic scene with overlapping views."""

import argparse
from pathlib import Path

import cv2
import numpy as np


def generate_scene(seed: int = 42):
    rng = np.random.default_rng(seed)

    width, height = 1500, 520
    scene = np.full((height, width, 3), 235, dtype=np.uint8)

    # Background grid provides additional spatial structure.
    for x in range(0, width, 40):
        cv2.line(scene, (x, 0), (x, height), (215, 215, 215), 1)

    for y in range(0, height, 40):
        cv2.line(scene, (0, y), (width, y), (215, 215, 215), 1)

    # Random shapes and labels create repeatable visual features.
    for i in range(180):
        x = int(rng.integers(20, width - 20))
        y = int(rng.integers(20, height - 20))
        color = tuple(int(v) for v in rng.integers(20, 220, size=3))
        radius = int(rng.integers(4, 17))

        if i % 3 == 0:
            cv2.circle(scene, (x, y), radius, color, -1)
        elif i % 3 == 1:
            cv2.rectangle(
                scene,
                (x - radius, y - radius),
                (x + radius, y + radius),
                color,
                -1,
            )
        else:
            cv2.line(
                scene,
                (x - radius, y - radius),
                (x + radius, y + radius),
                color,
                3,
            )

    for x in range(50, width - 150, 180):
        cv2.putText(
            scene,
            f"FEATURE {x}",
            (x, 250),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        )

    return scene


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/stitching/sample_synthetic"),
    )
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    scene = generate_scene(args.seed)

    view_width = 700
    starts = [0, 400, 800]

    for index, start in enumerate(starts, start=1):
        view = scene[:, start:start + view_width]
        output = args.output_dir / f"{index:02d}.png"

        if not cv2.imwrite(str(output), view):
            raise RuntimeError(f"Failed to write {output}")

        print(f"Saved {output}")

    print("Synthetic image generation complete.")


if __name__ == "__main__":
    main()