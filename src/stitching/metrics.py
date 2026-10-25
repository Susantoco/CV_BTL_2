"""
Thu thap/ghi so lieu so sanh giua cac phuong phap trich xuat dac trung
(so keypoint, so match, ty le inlier, reprojection error, thoi gian tung
buoc), dung cho bang so sanh o muc 2.2 bao cao (Phan 3 phu trach tong hop).
"""
import csv
import os

FIELDNAMES = [
    "image_set", "detector", "pair_index",
    "num_keypoints_left", "num_keypoints_right",
    "num_good_matches", "num_inliers", "inlier_ratio",
    "reprojection_error_px",
    "t_detect_s", "t_match_s", "t_homography_s", "t_warp_s", "t_blend_s", "t_total_s",
]


def append_metrics_csv(csv_path, image_set_name, metrics_list):
    """Append moi metrics (1 dict / cap anh) thanh 1 dong vao CSV. Tao file +
    header neu chua ton tai, cho phep goi nhieu lan voi cac detector/bo anh
    khac nhau roi gop lai thanh 1 bang duy nhat."""
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for m in metrics_list:
            row = {"image_set": image_set_name, **m}
            writer.writerow({k: row.get(k, "") for k in FIELDNAMES})
