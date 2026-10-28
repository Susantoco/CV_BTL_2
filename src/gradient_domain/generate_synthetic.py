import os

import cv2
import numpy as np

OUT_DIR = os.path.join("data", "gradient_domain", "edgecase")
H, W = 400, 600
CENTER = np.array([W // 2, H // 2], dtype=np.float64)
RADIUS = 70.0


def _linear_gradient_bg(bgr_top, bgr_bottom, seed, noise_std=4):
    yy = np.mgrid[0:H, 0:W][0].astype(np.float64)
    t = (yy / H)[..., None]
    top = np.array(bgr_top, dtype=np.float64)
    bottom = np.array(bgr_bottom, dtype=np.float64)
    grad = top[None, None, :] * (1 - t) + bottom[None, None, :] * t
    noise = np.random.default_rng(seed).normal(0, noise_std, size=(H, W, 3))
    return np.clip(grad + noise, 0, 255)


def make_target_background():
    return _linear_gradient_bg((180, 150, 90), (220, 180, 110), seed=0).astype(np.uint8)


def make_source_and_masks(source_bg_float):
    yy, xx = np.mgrid[0:H, 0:W]
    dx = xx.astype(np.float64) - CENTER[0]
    dy = yy.astype(np.float64) - CENTER[1]
    dist = np.sqrt(dx ** 2 + dy ** 2)

    core_color = np.array([30.0, 170.0, 250.0])   # BGR: vang sang (tam mat troi)
    rim_color = np.array([25.0, 70.0, 225.0])      # BGR: do cam (rim mat troi)
    rim_t = np.clip(dist / RADIUS, 0, 1)[..., None]
    disk_color = core_color * (1 - rim_t) + rim_color * rim_t
    disk_color = disk_color + np.random.default_rng(7).normal(0, 10, size=(H, W, 1))
    disk_color = disk_color + 6 * np.sin(dist / RADIUS * 3 * np.pi)[..., None]  # van dong tam

    object_rgb = source_bg_float.copy()
    object_alpha = np.zeros((H, W), dtype=np.float64)
    disk_mask = dist <= RADIUS
    object_rgb[disk_mask] = disk_color[disk_mask]
    object_alpha[disk_mask] = 1.0

    rng = np.random.default_rng(11)
    for angle_deg in range(0, 360, 30):
        angle = np.deg2rad(angle_deg)
        direction = np.array([np.cos(angle), np.sin(angle)])
        p1 = CENTER + direction * RADIUS * 1.05
        p2 = CENTER + direction * RADIUS * (1.3 + 0.15 * rng.random())
        ray_canvas = np.zeros((H, W), dtype=np.uint8)
        cv2.line(ray_canvas, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), 255, 7, cv2.LINE_AA)
        ray_bool = ray_canvas > 127
        ray_t = np.clip((dist - RADIUS * 1.0) / (RADIUS * 0.45), 0, 1)[..., None]
        ray_color = core_color * (1 - ray_t) + rim_color * ray_t
        object_rgb[ray_bool] = ray_color[ray_bool]
        object_alpha[ray_bool] = 1.0

    source = np.clip(
        object_alpha[..., None] * object_rgb + (1 - object_alpha[..., None]) * source_bg_float, 0, 255
    ).astype(np.uint8)

    shape_canvas = (object_alpha > 0).astype(np.uint8) * 255
    tight_mask = cv2.dilate(shape_canvas, np.ones((5, 5), np.uint8), iterations=1)

    loose_mask = np.zeros((H, W), dtype=np.uint8)
    cv2.circle(loose_mask, (int(CENTER[0]), int(CENTER[1])), int(RADIUS * 1.45), 255, -1, cv2.LINE_AA)

    return source, tight_mask, loose_mask


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    bg = make_target_background()
    cv2.imwrite(os.path.join(OUT_DIR, "background.png"), bg)

    mild_bg = _linear_gradient_bg((140, 115, 70), (170, 140, 90), seed=3)
    source, tight_mask, loose_mask = make_source_and_masks(mild_bg)
    cv2.imwrite(os.path.join(OUT_DIR, "source.png"), source)
    cv2.imwrite(os.path.join(OUT_DIR, "mask.png"), tight_mask)
    cv2.imwrite(os.path.join(OUT_DIR, "mask_loose.png"), loose_mask)

    hard_dir = os.path.join(OUT_DIR, "challenging")
    os.makedirs(hard_dir, exist_ok=True)
    hard_bg = _linear_gradient_bg((40, 120, 200), (70, 160, 240), seed=13)
    hard_source, hard_mask, _ = make_source_and_masks(hard_bg)
    cv2.imwrite(os.path.join(hard_dir, "background.png"), bg)
    cv2.imwrite(os.path.join(hard_dir, "source.png"), hard_source)
    cv2.imwrite(os.path.join(hard_dir, "mask.png"), hard_mask)

    print(f"Da sinh anh tong hop vao: {OUT_DIR}")
    print(f"  - background/source/mask/mask_loose.png : bo anh demo chinh ({W}x{H}, offset 0 0)")
    print(f"  - challenging/                           : bo anh kho (minh hoa han che muc 2.5)")


if __name__ == "__main__":
    main()
