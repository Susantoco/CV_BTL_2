# CV BTL2 — Gradient Domain Editing & Panoramic Image Stitching

Repo dùng chung cho cả 3 phần của bài tập lớn (xem `docs/CV-project-2.pdf` và
`docs/HD-BTL-CV.pdf` cho đề bài gốc và hướng dẫn báo cáo chung của môn học).

## Phân công & chủ sở hữu từng phần

| Phần | Nội dung | Thư mục code chính | Người phụ trách |
|---|---|---|---|
| 1 | Gradient Domain Editing (Poisson blending) | `src/gradient_domain/` | (bạn) |
| 2 | Core pipeline stitching + SIFT | `src/stitching/` | Thành viên B |
| 3 | Pipeline của Phần 2 + ORB/SURF + so sánh | `src/stitching/` (chỉ đổi `--detector`) | Thành viên C |

**Quan trọng với Phần 2 & 3:** cả hai dùng chung một pipeline
(`src/stitching/pipeline.py`). Phần 2 build pipeline này và chạy với SIFT;
Phần 3 **không viết lại pipeline**, chỉ truyền `--detector orb` (hoặc thêm
detector mới vào `detectors.py`) rồi chạy lại. Nếu Phần 3 thấy cần sửa
`pipeline.py` để ORB chạy đúng, nghĩa là pipeline chưa thực sự
detector-agnostic — báo lại cho Phần 2 để sửa chung, đừng fork riêng.

> **Lưu ý về SURF:** build OpenCV hiện tại (`opencv-python` chuẩn, không phải
> `opencv-contrib-python` bản `nonfree`) không có `cv2.xfeatures2d`, nên SURF
> **không chạy được** trừ khi tự build OpenCV với cờ `OPENCV_ENABLE_NONFREE`.
> `detectors.py` vẫn khai báo `SURFDetector` nhưng sẽ raise lỗi rõ ràng nếu
> gọi tới. Yêu cầu đề bài chỉ cần **ít nhất 2 phương pháp** — SIFT + ORB đã
> đủ. Nếu nhóm vẫn muốn có SURF, cần cài `opencv-contrib-python` phiên bản
> cũ (<4.3, trước khi SURF bị patent-lock ra khỏi free build) hoặc build từ
> source.

## Cấu trúc thư mục

```
BTL2/
├── docs/                          # Đề bài gốc + hướng dẫn chung (không sửa)
├── data/
│   ├── gradient_domain/
│   │   ├── sample/                # Ảnh tổng hợp (synthetic) để test thuật toán Poisson — đã có sẵn
│   │   └── real/                  # <-- Bỏ ảnh nền + ảnh nguồn thật của bạn vào đây
│   └── stitching/
│       ├── sample_synthetic/      # Bộ ảnh tổng hợp để validate pipeline trước khi có ảnh thật
│       ├── member2_set/           # <-- Bộ ảnh tự chụp của người làm Phần 2
│       └── member3_set/           # <-- Bộ ảnh tự chụp của người làm Phần 3
├── src/
│   ├── gradient_domain/           # PHẦN 1 — Poisson blending
│   │   ├── io_utils.py            # Đọc/ghi ảnh, chuẩn hóa float [0,1] <-> uint8
│   │   ├── mask_tool.py           # Công cụ vẽ mask tương tác bằng chuột (polygon)
│   │   ├── naive_blend.py         # Ghép trực tiếp (copy-paste) — baseline để so sánh
│   │   ├── poisson_blend.py       # Thuật toán Poisson/gradient-domain blending (cốt lõi)
│   │   ├── generate_synthetic.py  # Sinh ảnh nền/nguồn/mask tổng hợp để test khi chưa có ảnh thật
│   │   └── run_pipeline.py        # CLI: chạy naive + poisson, xuất ảnh so sánh side-by-side
│   └── stitching/                 # PHẦN 2 + 3 — dùng chung
│       ├── detectors.py           # Registry các detector (SIFT/ORB/SURF) — nơi DUY NHẤT cần sửa để thêm/đổi phương pháp
│       ├── pipeline.py            # Pipeline detector-agnostic: preprocess -> match -> homography -> warp -> blend
│       ├── metrics.py             # Thu thập số liệu so sánh (số keypoint, tỉ lệ inlier, reproj. error, thời gian)
│       ├── generate_synthetic_scene.py  # Sinh bộ ảnh tổng hợp nhiều góc nhìn để validate pipeline
│       └── run_stitch.py          # CLI: python -m src.stitching.run_stitch --images ... --detector sift|orb
├── results/                        # Output ảnh/báo cáo trung gian (bị gitignore, tự chạy lại để tái tạo)
│   ├── gradient_domain/
│   └── stitching/
├── report/                         # Nội dung soạn sẵn cho từng mục báo cáo chung (2.1 → 3)
│   ├── section_2_1_gradient_theory.md     # Phần 1 viết
│   ├── section_2_2_stitching_theory.md    # Phần 2 viết (lý thuyết pipeline)
│   ├── section_2_2_stitching_results.md   # Phần 3 viết (bảng so sánh thực nghiệm)
│   ├── section_3_gradient_analysis.md     # Phần 1 viết
│   ├── section_3_stitching_analysis.md    # Phần 2+3 viết chung
│   └── figures/                           # Ảnh minh họa chèn vào báo cáo LaTeX/PDF cuối
├── notebooks/                      # (tùy chọn) notebook Colab để demo/export PDF
├── requirements.txt
└── .gitignore
```

## Cài đặt môi trường

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
pip install -r requirements.txt
```

Đã kiểm tra trên môi trường chung: `opencv-python 4.13`, SIFT và ORB chạy
được out-of-the-box (không cần `opencv-contrib-python`).

## Cách chạy — Phần 1 (Gradient Domain Editing)

```bash
# 1. (một lần) sinh ảnh tổng hợp để test thuật toán trước khi có ảnh thật
python -m src.gradient_domain.generate_synthetic

# 2. (khi có ảnh thật) vẽ mask tương tác trên ảnh nguồn
python -m src.gradient_domain.mask_tool --source data/gradient_domain/real/source.jpg --out data/gradient_domain/real/mask.png

# 3. chạy blend + so sánh naive vs Poisson
python -m src.gradient_domain.run_pipeline \
    --background data/gradient_domain/real/background.jpg \
    --source data/gradient_domain/real/source.jpg \
    --mask data/gradient_domain/real/mask.png \
    --offset 50 80 \
    --out results/gradient_domain/compare.png
```

`generate_synthetic.py` sinh ra 3 bộ ảnh test đã kiểm chứng, dùng được ngay
cho báo cáo trong lúc chưa có ảnh thật:

| Bộ ảnh | Mục đích |
|---|---|
| `sample/{background,source,mask}.png` | Demo chính: nền source/target cùng tông xanh nhưng khác độ sáng → naive paste lộ seam rõ, Poisson blend xóa seam và vẫn giữ đúng màu vật thể |
| `sample/mask_loose.png` (dùng thay cho `mask.png`) | Mask rộng hơn nhiều so với vật thể → minh họa ảnh hưởng của kích thước mask (mục 2.5): mask càng rộng, Poisson càng "kéo" nhiều nền phẳng vào vùng giải, dễ để lại viền/halo |
| `sample/challenging/{background,source,mask}.png` | Nền source lệch hẳn tông màu (cam/vàng) so với target (xanh) gần như bù màu → vật thể bị đổi hẳn tông màu sau Poisson blend. Ví dụ minh họa **hạn chế** của phương pháp khi 2 ảnh có ánh sáng/tông màu quá khác biệt |

Lưu ý lý thuyết quan trọng đã rút ra khi làm test: Poisson blending chỉ giữ
được *gradient* của source, không giữ được màu tuyệt đối — nên (a) vùng vật
thể phải có texture/gradient nội bộ thật sự (tô màu đặc tuyệt đối sẽ bị "bốc
hơi" thành nội suy biên), và (b) nếu màu nền quanh vật thể ở ảnh nguồn khác
quá xa màu nền đích, điều kiện biên sẽ kéo lệch cả vùng theo tông màu đích.

## Cách chạy — Phần 2 / Phần 3 (Stitching)

```bash
# (một lần) sinh bộ ảnh tổng hợp để validate pipeline
python -m src.stitching.generate_synthetic_scene

# Phần 2 — SIFT
python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector sift --out results/stitching/sift_synthetic.jpg

# Phần 3 — chỉ đổi --detector, pipeline giữ nguyên
python -m src.stitching.run_stitch --images "data/stitching/sample_synthetic/*.png" --detector orb --out results/stitching/orb_synthetic.jpg

# Chạy trên bộ ảnh tự chụp của từng người tương tự, chỉ đổi --images
python -m src.stitching.run_stitch --images "data/stitching/member2_set/*.jpg" --detector sift --out results/stitching/sift_member2.jpg
python -m src.stitching.run_stitch --images "data/stitching/member2_set/*.jpg" --detector orb  --out results/stitching/orb_member2.jpg
```

Thêm `--metrics-out results/stitching/metrics.csv` để ghi số liệu (số
keypoint, số match, tỉ lệ inlier, reprojection error, thời gian từng bước)
phục vụ bảng so sánh ở mục 2.2 của báo cáo — mỗi lần chạy sẽ append thêm một
dòng vào CSV đó, nên chạy đủ cả 2 detector trên đủ các bộ ảnh rồi mở file ra
tổng hợp bảng.

## Quy trình làm việc chung (git)

1. Người tổng hợp (bạn) `git init` + push repo khung này lên remote trước.
2. Mỗi thành viên clone về, tạo nhánh riêng: `part1-gradient`,
   `part2-sift`, `part3-orb-compare`.
3. Chỉ sửa trong thư mục/file thuộc phần mình (xem bảng phân công ở trên) để
   tránh conflict — đặc biệt Phần 2 & 3 cùng đụng `src/stitching/`, nên trao
   đổi trước khi sửa `pipeline.py`/`detectors.py`.
4. Review chéo code nhau qua Pull Request trước khi merge vào `main`.
5. Mục "Nhận xét/Thảo luận" và "Kết luận" trong báo cáo viết chung sau khi cả
   3 phần có kết quả — để trong `report/section_4_discussion.md` và
   `report/section_5_conclusion.md` (tạo khi tới lúc viết).

## Trạng thái hiện tại

- [x] Khung repo + pipeline stitching detector-agnostic (SIFT + ORB chạy được)
- [x] Phần 1: Poisson blending hiện thực đầy đủ, đã test với ảnh tổng hợp
- [ ] Ảnh thật (background/source cho Phần 1; 3-4 ảnh mỗi góc cho Phần 2/3) — **mỗi người tự bổ sung vào `data/`**
- [ ] Bảng so sánh thực nghiệm cuối cùng (Phần 3) — cần chạy trên ảnh thật
- [ ] Báo cáo LaTeX tổng hợp cuối cùng
