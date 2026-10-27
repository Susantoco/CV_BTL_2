"""Detector-agnostic image stitching pipeline."""

from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from .detectors import create_detector
from .metrics import PairMetrics


def read_images(image_paths: list[Path]) -> list[np.ndarray]:
    images = []

    for path in image_paths:
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)

        if image is None:
            raise ValueError(f"Cannot read image: {path}")

        images.append(image)

    return images


def detect_features(images, config):
    keypoints = []
    descriptors = []
    elapsed_ms = []

    for image in images:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        start = perf_counter()
        points, desc = config.detector.detectAndCompute(gray, None)
        elapsed_ms.append((perf_counter() - start) * 1000)

        keypoints.append(points or [])
        descriptors.append(desc)

    return keypoints, descriptors, elapsed_ms


def match_pair(desc_a, desc_b, config):
    """Match image B against image A; return (A index, B index)."""
    if desc_a is None or desc_b is None:
        return [], 0.0

    if len(desc_a) < 2 or len(desc_b) < 2:
        return [], 0.0

    matcher = cv2.BFMatcher(config.norm_type, crossCheck=False)

    start = perf_counter()
    neighbors = matcher.knnMatch(desc_b, desc_a, k=2)

    good = [
        pair[0]
        for pair in neighbors
        if len(pair) == 2
        and pair[0].distance < config.ratio_threshold * pair[1].distance
    ]

    elapsed_ms = (perf_counter() - start) * 1000
    return good, elapsed_ms


def estimate_homography(points_a, points_b, matches):
    """Estimate H mapping image B coordinates into image A."""
    if len(matches) < 4:
        return None, None, float("inf"), 0.0

    src = np.float32(
        [points_b[m.queryIdx].pt for m in matches]
    ).reshape(-1, 1, 2)

    dst = np.float32(
        [points_a[m.trainIdx].pt for m in matches]
    ).reshape(-1, 1, 2)

    start = perf_counter()
    H, mask = cv2.findHomography(
        src,
        dst,
        cv2.RANSAC,
        4.0,
        maxIters=2000,
        confidence=0.995,
    )
    elapsed_ms = (perf_counter() - start) * 1000

    if H is None or mask is None:
        return None, None, float("inf"), elapsed_ms

    inlier_mask = mask.ravel().astype(bool)

    if not np.any(inlier_mask):
        return None, None, float("inf"), elapsed_ms

    projected = cv2.perspectiveTransform(src, H).reshape(-1, 2)
    targets = dst.reshape(-1, 2)
    errors = np.linalg.norm(projected - targets, axis=1)

    reprojection_error = float(errors[inlier_mask].mean())

    return H, inlier_mask, reprojection_error, elapsed_ms


def calculate_pair_metrics(
    image_names,
    config,
    keypoints,
    descriptors,
    detection_times,
):
    metrics = []
    transforms = [np.eye(3, dtype=np.float64)]

    for i in range(len(keypoints) - 1):
        name_a = image_names[i]
        name_b = image_names[i + 1]

        matches, matching_ms = match_pair(
            descriptors[i],
            descriptors[i + 1],
            config,
        )

        H, inlier_mask, reprojection_error, homography_ms = (
            estimate_homography(
                keypoints[i],
                keypoints[i + 1],
                matches,
            )
        )

        inliers = (
            int(inlier_mask.sum())
            if inlier_mask is not None
            else 0
        )
        ratio = inliers / len(matches) if matches else 0.0

        success = (
            H is not None
            and inliers >= 4
            and np.isfinite(reprojection_error)
        )

        if success:
            transforms.append(transforms[-1] @ H)
        else:
            transforms.append(transforms[-1].copy())

        metrics.append(
            PairMetrics(
                image_a=name_a,
                image_b=name_b,
                detector=config.name,
                keypoints_a=len(keypoints[i]),
                keypoints_b=len(keypoints[i + 1]),
                tentative_matches=len(matches),
                inliers=inliers,
                inlier_ratio=ratio,
                reprojection_error_px=reprojection_error,
                detection_time_ms=(
                    detection_times[i] + detection_times[i + 1]
                ),
                matching_time_ms=matching_ms,
                homography_time_ms=homography_ms,
                success=success,
                error="" if success else "Homography estimation failed",
            )
        )

    return transforms, metrics


def warp_and_blend(images, transforms):
    """Warp images into a shared canvas and average overlapping pixels."""
    corners = []

    for image, H in zip(images, transforms):
        h, w = image.shape[:2]
        image_corners = np.float32(
            [[0, 0], [w, 0], [w, h], [0, h]]
        ).reshape(-1, 1, 2)

        warped_corners = cv2.perspectiveTransform(image_corners, H)
        corners.append(warped_corners.reshape(-1, 2))

    all_corners = np.concatenate(corners, axis=0)
    min_xy = np.floor(all_corners.min(axis=0)).astype(int)
    max_xy = np.ceil(all_corners.max(axis=0)).astype(int)

    width, height = (max_xy - min_xy).tolist()

    if width <= 0 or height <= 0 or width * height > 100_000_000:
        raise ValueError("Invalid or excessively large panorama canvas.")

    translation = np.array(
        [
            [1.0, 0.0, -min_xy[0]],
            [0.0, 1.0, -min_xy[1]],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float64,
    )

    accum = np.zeros((height, width, 3), dtype=np.float32)
    weights = np.zeros((height, width), dtype=np.float32)

    for image, H in zip(images, transforms):
        matrix = translation @ H

        warped = cv2.warpPerspective(image, matrix, (width, height))

        source_mask = np.ones(image.shape[:2], dtype=np.uint8) * 255
        warped_mask = cv2.warpPerspective(
            source_mask,
            matrix,
            (width, height),
            flags=cv2.INTER_NEAREST,
        )

        valid = warped_mask > 0
        accum[valid] += warped[valid].astype(np.float32)
        weights[valid] += 1.0

    valid = weights > 0
    panorama = np.zeros_like(accum, dtype=np.uint8)
    panorama[valid] = np.clip(accum[valid] / weights[valid, None], 0, 255).astype(np.uint8)

    return panorama


def stitch_images(image_paths: list[Path], detector_name: str):
    if len(image_paths) < 2:
        raise ValueError("At least two images are required.")

    images = read_images(image_paths)
    config = create_detector(detector_name)

    keypoints, descriptors, detection_times = detect_features(images, config)

    transforms, metrics = calculate_pair_metrics(
        [path.name for path in image_paths],
        config,
        keypoints,
        descriptors,
        detection_times,
    )

    if not all(item.success for item in metrics):
        failed = [
            f"{item.image_a} -> {item.image_b}"
            for item in metrics
            if not item.success
        ]
        raise RuntimeError("Unable to register all consecutive image pairs: " + ", ".join(failed))

    panorama = warp_and_blend(images, transforms)
    return panorama, metrics