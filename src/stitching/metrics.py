"""Metrics for evaluating image stitching."""

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass
class PairMetrics:
    image_a: str
    image_b: str
    detector: str
    keypoints_a: int
    keypoints_b: int
    tentative_matches: int
    inliers: int
    inlier_ratio: float
    reprojection_error_px: float
    detection_time_ms: float
    matching_time_ms: float
    homography_time_ms: float
    success: bool
    error: str = ""


def save_metrics(metrics: list[PairMetrics], output_path: Path) -> None:
    """Save pairwise metrics as a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            [asdict(item) for item in metrics],
            file,
            indent=2,
            ensure_ascii=False,
        )


def print_metrics(metrics: list[PairMetrics]) -> None:
    """Print a compact summary for every image pair."""
    for item in metrics:
        print(f"\n{item.image_a} -> {item.image_b}")
        print(f"  Detector:       {item.detector}")
        print(f"  Keypoints:      {item.keypoints_a} / {item.keypoints_b}")
        print(f"  Matches:        {item.tentative_matches}")
        print(f"  Inliers:        {item.inliers}")
        print(f"  Inlier ratio:   {item.inlier_ratio:.3f}")
        print(f"  Reprojection:   {item.reprojection_error_px:.3f} px")
        print(
            "  Time:           "
            f"{item.detection_time_ms + item.matching_time_ms + item.homography_time_ms:.2f} ms"
        )
        print(f"  Success:        {item.success}")

        if item.error:
            print(f"  Error:          {item.error}")


def append_run_metrics(metrics: list[PairMetrics], output_path: Path,
                       image_set: str, detector: str, image_count: int,
                       stitching_time_ms: float, detection_time_ms: float) -> None:
    """Append one summary row per run; preserve previous detector runs."""
    import csv
    import math

    output_path.parent.mkdir(parents=True, exist_ok=True)
    columns = [
        "image_set", "detector", "image_count", "pair_count",
        "keypoint_count", "match_count", "inlier_count", "inlier_ratio",
        "reprojection_error_px", "detection_time_ms", "matching_time_ms",
        "homography_time_ms", "stitching_time_ms", "total_time_ms", "success",
    ]
    keypoints = [metrics[0].keypoints_a] + [m.keypoints_b for m in metrics] if metrics else []
    matches = sum(m.tentative_matches for m in metrics)
    inliers = sum(m.inliers for m in metrics)
    valid_errors = [(m.reprojection_error_px, m.inliers) for m in metrics
                    if math.isfinite(m.reprojection_error_px) and m.inliers > 0]
    weighted_error = (sum(e * n for e, n in valid_errors) / sum(n for _, n in valid_errors)
                      if valid_errors else float("nan"))
    row = {
        "image_set": image_set, "detector": detector, "image_count": image_count,
        "pair_count": len(metrics), "keypoint_count": sum(keypoints),
        "match_count": matches, "inlier_count": inliers,
        "inlier_ratio": inliers / matches if matches else 0.0,
        "reprojection_error_px": weighted_error,
        "detection_time_ms": detection_time_ms,
        "matching_time_ms": sum(m.matching_time_ms for m in metrics),
        "homography_time_ms": sum(m.homography_time_ms for m in metrics),
        "stitching_time_ms": stitching_time_ms,
        "total_time_ms": 0.0,
        "success": all(m.success for m in metrics),
    }
    row["total_time_ms"] = (row["detection_time_ms"] + row["matching_time_ms"]
                            + row["homography_time_ms"] + stitching_time_ms)
    exists = output_path.exists() and output_path.stat().st_size > 0
    if exists:
        with output_path.open("r", encoding="utf-8-sig", newline="") as file:
            header = next(csv.reader(file), [])
        if header != columns:
            raise ValueError(f"CSV header mismatch at {output_path}; use a new CSV path.")
    with output_path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if not exists:
            writer.writeheader()
        writer.writerow(row)
