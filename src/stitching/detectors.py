"""Feature detector and descriptor registry for image stitching."""

from dataclasses import dataclass
from typing import Any

import cv2


@dataclass
class DetectorConfig:
    name: str
    detector: Any
    norm_type: int
    ratio_threshold: float = 0.75


def create_detector(name: str) -> DetectorConfig:
    """Create a feature detector and its matching configuration."""
    name = name.lower()

    if name == "sift":
        if not hasattr(cv2, "SIFT_create"):
            raise RuntimeError("SIFT is unavailable in this OpenCV installation.")

        return DetectorConfig(
            name="sift",
            detector=cv2.SIFT_create(nfeatures=5000),
            norm_type=cv2.NORM_L2,
            ratio_threshold=0.75,
        )

    if name == "orb":
        return DetectorConfig(
            name="orb",
            detector=cv2.ORB_create(nfeatures=5000),
            norm_type=cv2.NORM_HAMMING,
            ratio_threshold=0.80,
        )

    if name == "surf":
        if not hasattr(cv2, "xfeatures2d"):
            raise RuntimeError(
                "SURF is unavailable. The current OpenCV build does not expose cv2.xfeatures2d."
            )

        try:
            detector = cv2.xfeatures2d.SURF_create(400)
        except cv2.error as exc:
            raise RuntimeError(
                "SURF is disabled in this OpenCV build. Use SIFT or ORB, or configure a compatible OpenCV build."
            ) from exc

        return DetectorConfig(
            name="surf",
            detector=detector,
            norm_type=cv2.NORM_L2,
            ratio_threshold=0.75,
        )

    raise ValueError(f"Unsupported detector: {name}. Choose sift, orb, or surf.")


def available_detectors() -> list[str]:
    """Return the detector names supported by this project."""
    return ["sift", "orb", "surf"]
