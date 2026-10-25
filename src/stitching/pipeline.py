"""
Pipeline ghep anh toan canh (feature-based image stitching), dung chung cho
Phan 2 (SIFT) va Phan 3 (ORB/SURF). File nay KHONG duoc chua logic rieng cho
tung loai detector - muon doi phuong phap trich xuat dac trung, truyen
`detector_name` khac khi goi stitch_images()/stitch_pair(), hoac sua
detectors.py neu can them detector moi.

Cac buoc (dung theo de bai muc 2.2):
    1. load_and_preprocess   - doc anh, resize neu qua lon, chuyen xam
    2. detect_and_describe   - trich dac trung (qua detectors.py)
    3. match_features        - so khop KNN + Lowe's ratio test
    4. estimate_homography   - RANSAC
    5. warp_and_align        - warp anh theo homography, dat len canvas chung
    6. blend_overlap         - blend vung chong lan bang feathering (distance
                                transform) o muc co ban theo yeu cau de bai
"""
import time

import cv2
import numpy as np

from .detectors import get_detector


def load_and_preprocess(path, max_dim=1600):
    """Doc anh mau, resize neu canh lon nhat vuot qua max_dim, tra ve them
    ban xam de trich dac trung."""
    color = cv2.imread(path, cv2.IMREAD_COLOR)
    if color is None:
        raise FileNotFoundError(f"Khong doc duoc anh: {path}")
    h, w = color.shape[:2]
    scale = min(1.0, max_dim / max(h, w))
    if scale < 1.0:
        color = cv2.resize(color, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(color, cv2.COLOR_BGR2GRAY)
    return color, gray


def detect_and_describe(gray, detector):
    return detector.detect_and_compute(gray)


def match_features(desc1, desc2, norm_type, ratio=0.75):
    """So khop KNN (k=2) + Lowe's ratio test. Hoat dong voi ca descriptor
    float (SIFT/SURF, norm_type=NORM_L2) lan binary (ORB, NORM_HAMMING) vi
    BFMatcher tu dieu chinh theo norm_type truyen vao."""
    if desc1 is None or desc2 is None or len(desc1) < 2 or len(desc2) < 2:
        return []
    matcher = cv2.BFMatcher(norm_type)
    knn = matcher.knnMatch(desc1, desc2, k=2)
    good = []
    for pair in knn:
        if len(pair) != 2:
            continue
        m, n = pair
        if m.distance < ratio * n.distance:
            good.append(m)
    return good


def estimate_homography(kp1, kp2, good_matches, ransac_thresh=4.0):
    if len(good_matches) < 4:
        raise ValueError(f"Khong du diem khop de uoc luong homography ({len(good_matches)} < 4)")
    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
    H, inlier_mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransac_thresh)
    if H is None:
        raise ValueError("cv2.findHomography that bai (khong tim duoc mo hinh phu hop)")
    return H, inlier_mask, src_pts, dst_pts


def _reprojection_error(H, src_pts, dst_pts, inlier_mask):
    """Sai so trung binh (px) giua diem khop sau khi warp bang H va diem dich
    thuc te, chi tinh tren cac inlier - dung lam do do 'chinh xac can chinh'."""
    inliers = inlier_mask.ravel().astype(bool)
    if not inliers.any():
        return float("nan")
    projected = cv2.perspectiveTransform(src_pts[inliers], H)
    diff = projected.reshape(-1, 2) - dst_pts[inliers].reshape(-1, 2)
    return float(np.sqrt((diff ** 2).sum(axis=1)).mean())


def warp_and_align(img_left, img_right, H):
    """
    Warp `img_left` bang H sao cho khop he toa do cua `img_right`, dat ca hai
    len mot canvas chung du lon (co dich chuyen de khong bi cat am toa do).

    Tra ve: canvas_left, canvas_right (cung kich thuoc, cung he toa do), phan
    khong co anh la mau den (0) - dung cho blend_overlap() o buoc sau.
    """
    h1, w1 = img_left.shape[:2]
    h2, w2 = img_right.shape[:2]

    corners_left = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]]).reshape(-1, 1, 2)
    corners_left_warped = cv2.perspectiveTransform(corners_left, H)
    corners_right = np.float32([[0, 0], [w2, 0], [w2, h2], [0, h2]]).reshape(-1, 1, 2)
    all_corners = np.concatenate([corners_left_warped, corners_right], axis=0)

    x_min, y_min = np.floor(all_corners.min(axis=0).ravel()).astype(int)
    x_max, y_max = np.ceil(all_corners.max(axis=0).ravel()).astype(int)
    translation = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]], dtype=np.float64)

    canvas_size = (x_max - x_min, y_max - y_min)
    canvas_left = cv2.warpPerspective(img_left, translation @ H, canvas_size)
    canvas_right = np.zeros((canvas_size[1], canvas_size[0], 3), dtype=img_right.dtype)
    canvas_right[-y_min:-y_min + h2, -x_min:-x_min + w2] = img_right
    return canvas_left, canvas_right


def blend_overlap(canvas_left, canvas_right):
    """Blend vung chong lan o muc co ban bang feathering: trong so theo
    khoang-cach-toi-bien cua tung anh (distance transform), muot hon han so
    voi cat cung/lay trung binh don gian giua 2 anh."""
    mask_left = (canvas_left.sum(axis=2) > 0).astype(np.uint8)
    mask_right = (canvas_right.sum(axis=2) > 0).astype(np.uint8)

    w_left = cv2.distanceTransform(mask_left, cv2.DIST_L2, 5).astype(np.float64)
    w_right = cv2.distanceTransform(mask_right, cv2.DIST_L2, 5).astype(np.float64)

    total = w_left + w_right
    total[total == 0] = 1.0
    alpha_left = (w_left / total)[..., None]
    alpha_right = (w_right / total)[..., None]

    blended = (canvas_left.astype(np.float64) * alpha_left
               + canvas_right.astype(np.float64) * alpha_right)
    only_left = (mask_left > 0) & (mask_right == 0)
    only_right = (mask_right > 0) & (mask_left == 0)
    blended[only_left] = canvas_left[only_left]
    blended[only_right] = canvas_right[only_right]
    return np.clip(blended, 0, 255).astype(np.uint8)


def stitch_pair(img_left, img_right, detector_name, ransac_thresh=4.0, ratio=0.75, detector_kwargs=None):
    """Ghep 2 anh mau (mang numpy BGR, da tien xu ly) thanh 1 panorama.
    Tra ve (panorama, metrics_dict)."""
    detector = get_detector(detector_name, **(detector_kwargs or {}))
    metrics = {"detector": detector_name}

    t0 = time.perf_counter()
    gray_left = cv2.cvtColor(img_left, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(img_right, cv2.COLOR_BGR2GRAY)
    kp1, desc1 = detect_and_describe(gray_left, detector)
    kp2, desc2 = detect_and_describe(gray_right, detector)
    metrics["t_detect_s"] = time.perf_counter() - t0
    metrics["num_keypoints_left"] = len(kp1)
    metrics["num_keypoints_right"] = len(kp2)

    t0 = time.perf_counter()
    good_matches = match_features(desc1, desc2, detector.norm_type, ratio=ratio)
    metrics["t_match_s"] = time.perf_counter() - t0
    metrics["num_good_matches"] = len(good_matches)

    t0 = time.perf_counter()
    H, inlier_mask, src_pts, dst_pts = estimate_homography(kp1, kp2, good_matches, ransac_thresh)
    metrics["t_homography_s"] = time.perf_counter() - t0
    num_inliers = int(inlier_mask.sum())
    metrics["num_inliers"] = num_inliers
    metrics["inlier_ratio"] = num_inliers / len(good_matches) if good_matches else 0.0
    metrics["reprojection_error_px"] = _reprojection_error(H, src_pts, dst_pts, inlier_mask)

    t0 = time.perf_counter()
    canvas_left, canvas_right = warp_and_align(img_left, img_right, H)
    metrics["t_warp_s"] = time.perf_counter() - t0

    t0 = time.perf_counter()
    panorama = blend_overlap(canvas_left, canvas_right)
    metrics["t_blend_s"] = time.perf_counter() - t0

    metrics["t_total_s"] = sum(
        metrics[k] for k in ("t_detect_s", "t_match_s", "t_homography_s", "t_warp_s", "t_blend_s")
    )
    return panorama, metrics


def _crop_black_border(panorama):
    gray = cv2.cvtColor(panorama, cv2.COLOR_BGR2GRAY)
    coords = cv2.findNonZero((gray > 0).astype(np.uint8))
    if coords is None:
        return panorama
    x, y, w, h = cv2.boundingRect(coords)
    return panorama[y:y + h, x:x + w]


def stitch_images(image_paths, detector_name, max_dim=1600, ransac_thresh=4.0, ratio=0.75,
                   detector_kwargs=None, crop_border=True):
    """
    Ghep tuan tu danh sach anh (theo dung thu tu trong `image_paths`, gia
    dinh cac anh ke nhau co vung chong lan) thanh 1 panorama duy nhat.

    Tra ve: (panorama, list_metrics) - list_metrics co 1 phan tu cho moi cap
    anh lien tiep da ghep, dung de tong hop bang so sanh o Phan 3.
    """
    if len(image_paths) < 2:
        raise ValueError("Can it nhat 2 anh de ghep panorama")

    loaded = [load_and_preprocess(p, max_dim=max_dim)[0] for p in image_paths]
    panorama = loaded[0]
    all_metrics = []
    for i in range(1, len(loaded)):
        panorama, metrics = stitch_pair(
            panorama, loaded[i], detector_name,
            ransac_thresh=ransac_thresh, ratio=ratio, detector_kwargs=detector_kwargs,
        )
        metrics["pair_index"] = i
        all_metrics.append(metrics)
        if crop_border:
            panorama = _crop_black_border(panorama)
    return panorama, all_metrics
