"""
CLI dung chung cho Phan 2 (SIFT) va Phan 3 (ORB/SURF).

KHONG sua file nay de doi phuong phap trich xuat dac trung - chi truyen
--detector khac. Neu doi detector ma phai sua pipeline.py moi chay duoc,
nghia la pipeline chua thuc su detector-agnostic, bao lai de sua chung thay
vi fork rieng.

Vi du:
    python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector sift --out results/stitching/sift_synthetic.jpg
    python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector orb  --out results/stitching/orb_synthetic.jpg --metrics-out results/stitching/metrics.csv
"""
import argparse
import glob
import os

import cv2

from .metrics import append_metrics_csv
from .pipeline import stitch_images


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images", required=True,
                         help="Glob pattern (vd 'data/stitching/set1/*.jpg') hoac danh sach file "
                              "cach nhau boi dau phay, theo DUNG THU TU can ghep")
    parser.add_argument("--detector", required=True, choices=["sift", "orb", "surf"])
    parser.add_argument("--out", required=True)
    parser.add_argument("--max-dim", type=int, default=1600)
    parser.add_argument("--ransac-thresh", type=float, default=4.0)
    parser.add_argument("--ratio", type=float, default=0.75, help="Nguong Lowe's ratio test")
    parser.add_argument("--metrics-out", default=None,
                         help="Duong dan CSV de append so lieu so sanh (muc 2.2 bao cao)")
    parser.add_argument("--image-set-name", default=None,
                         help="Ten bo anh ghi vao CSV (mac dinh: ten thu muc chua anh dau tien)")
    args = parser.parse_args()

    if "," in args.images:
        image_paths = [p.strip() for p in args.images.split(",")]
    else:
        image_paths = sorted(glob.glob(args.images))
    if len(image_paths) < 2:
        raise ValueError(f"Can it nhat 2 anh, chi tim thay {len(image_paths)}: {image_paths}")

    print(f"Ghep {len(image_paths)} anh bang detector='{args.detector}':")
    for p in image_paths:
        print(f"  - {p}")

    panorama, all_metrics = stitch_images(
        image_paths, args.detector, max_dim=args.max_dim,
        ransac_thresh=args.ransac_thresh, ratio=args.ratio,
    )

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    cv2.imwrite(args.out, panorama)
    print(f"Da luu panorama: {args.out}")

    for m in all_metrics:
        print(f"  Cap {m['pair_index']}: {m['num_keypoints_left']}+{m['num_keypoints_right']} keypoints, "
              f"{m['num_good_matches']} good matches, {m['num_inliers']} inliers "
              f"({m['inlier_ratio'] * 100:.1f}%), reproj_err={m['reprojection_error_px']:.2f}px, "
              f"total={m['t_total_s'] * 1000:.1f}ms")

    if args.metrics_out:
        image_set_name = args.image_set_name or os.path.basename(os.path.dirname(image_paths[0])) or "unknown"
        append_metrics_csv(args.metrics_out, image_set_name, all_metrics)
        print(f"Da ghi so lieu vao: {args.metrics_out}")


if __name__ == "__main__":
    main()
