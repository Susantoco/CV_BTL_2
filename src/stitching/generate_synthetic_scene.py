"""
Sinh bo anh tong hop nhieu goc nhin tu 1 "canh" lon, dung de validate pipeline
stitching (detect -> match -> homography -> warp -> blend) chay dung truoc
khi co anh chup that. Chay 1 lan:

    python -m src.stitching.generate_synthetic_scene

Luu y QUAN TRONG: day chi la cac crop chong lan tu cung 1 anh (tuong duong
dich chuyen ngang thuan tuy, KHONG mo phong goc xoay camera that nhu de bai
yeu cau "cung vi tri quan sat, cac goc xoay khac nhau"). Muc dich DUY NHAT la
kiem tra code chay dung ve mat ky thuat (sinh homography, warp, blend khong
loi) khi chua co anh thuc nghiem that - KHONG thay the cho bo anh tu chup
(--images data/stitching/member2_set, member3_set).
"""
import os

import cv2
import numpy as np

OUT_DIR = os.path.join("data", "stitching", "sample_synthetic")
SCENE_H, SCENE_W = 900, 2200
VIEW_W = 900
OVERLAP_RATIO = 0.35


def make_scene():
    rng = np.random.default_rng(42)
    scene = np.full((SCENE_H, SCENE_W, 3), 230, dtype=np.uint8)

    # Nen checker nhat de co nhieu goc/canh cho detector bam vao.
    step = 40
    for y in range(0, SCENE_H, step):
        for x in range(0, SCENE_W, step):
            if (x // step + y // step) % 2 == 0:
                scene[y:y + step, x:x + step] = (215, 215, 215)

    # Rai cac hinh ngau nhien (circle/rectangle/line) voi mau/kich thuoc khac
    # nhau de tao nhieu dac trung cuc bo doc nhat, de SIFT/ORB bam vao.
    for _ in range(220):
        shape = rng.integers(0, 3)
        color = tuple(int(c) for c in rng.integers(0, 255, size=3))
        cx, cy = int(rng.integers(20, SCENE_W - 20)), int(rng.integers(20, SCENE_H - 20))
        if shape == 0:
            cv2.circle(scene, (cx, cy), int(rng.integers(5, 18)), color, -1, cv2.LINE_AA)
        elif shape == 1:
            s = int(rng.integers(8, 24))
            cv2.rectangle(scene, (cx - s, cy - s), (cx + s, cy + s), color, -1)
        else:
            angle = rng.uniform(0, 2 * np.pi)
            length = int(rng.integers(15, 40))
            p2 = (int(cx + length * np.cos(angle)), int(cy + length * np.sin(angle)))
            cv2.line(scene, (cx, cy), p2, color, 2, cv2.LINE_AA)

    noise = rng.normal(0, 6, size=scene.shape)
    return np.clip(scene.astype(np.float64) + noise, 0, 255).astype(np.uint8)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    scene = make_scene()
    stride = int(VIEW_W * (1 - OVERLAP_RATIO))
    x_starts = list(range(0, SCENE_W - VIEW_W + 1, stride))
    for i, x0 in enumerate(x_starts):
        view = scene[:, x0:x0 + VIEW_W]
        path = os.path.join(OUT_DIR, f"view_{i}.png")
        cv2.imwrite(path, view)
        print(f"Da luu: {path}")
    print(f"Tong cong {len(x_starts)} goc nhin, overlap ~{OVERLAP_RATIO * 100:.0f}%")
    print("Chay thu: python -m src.stitching.run_stitch "
          f'--images "{OUT_DIR}/*.png" --detector sift --out results/stitching/sift_synthetic.jpg')


if __name__ == "__main__":
    main()
