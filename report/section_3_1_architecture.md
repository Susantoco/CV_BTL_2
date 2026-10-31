# Mục 3.1 — Kiến trúc hệ thống tổng thể

> **Bản nháp (Chung).** Phần này không gắn với 1 thuật toán cụ thể nên không
> có "nguồn sẵn" như các mục khác — người viết đọc lại, đối chiếu với code
> trong `src/` và diễn đạt lại theo cách hiểu của mình trước khi đưa vào báo
> cáo (xem lưu ý học thuật trong `docs/HD-BTL-CV.pdf`).

## Nguyên tắc thiết kế

Đề bài gồm 2 bài toán độc lập về mặt toán học (giải PDE trên gradient ảnh vs.
ước lượng hình học chiếu từ đặc trưng), nên hệ thống được tách thành **2
module hoàn toàn tách biệt**, không chia sẻ code:

- `src/gradient_domain/` — Gradient Domain Editing (Phần 1)
- `src/stitching/` — Panoramic Image Stitching (Phần 2 + 3)

Trong mỗi module, lại áp dụng chung 1 nguyên tắc: **tách thuật toán lõi khỏi
CLI**. File `run_*.py` chỉ lo đọc tham số dòng lệnh, gọi hàm, và ghi kết quả
ra đĩa; toàn bộ logic thuật toán nằm ở các file còn lại và không phụ thuộc gì
vào `argparse`/I-O — nhờ vậy có thể gọi thẳng các hàm này từ notebook hoặc
test mà không cần qua CLI.

## Sơ đồ khối tổng thể

```
data/                         results/                      report/
 ├─ gradient_domain/           ├─ gradient_domain/           (nội dung viết tay,
 │   raw / mask / edgecase     │   so sánh naive vs Poisson    không tái sinh được)
 └─ stitching/                 └─ stitching/
     sample_synthetic/             panorama + metrics.csv
     member{1,2,3}_set/
        │                                 │
        ▼                                 ▼
┌───────────────────────┐       ┌───────────────────────────┐
│  src/gradient_domain/  │       │      src/stitching/       │
│  (Phần 1)              │       │   (Phần 2 core + Phần 3)  │
└───────────────────────┘       └───────────────────────────┘
```

`data/` là input cố định (ảnh gốc, không sinh ra từ code — trừ các bộ
synthetic). `results/` là output trung gian, **tái sinh được** bằng cách
chạy lại CLI (vì vậy bị gitignore) và là nguồn ảnh/số liệu chèn vào
`report/`.

## Kiến trúc module 1 — Gradient Domain Editing

```
run_pipeline.py (CLI)
   │  đọc background/source/mask + offset
   ▼
io_utils.py ── đọc ảnh, chuẩn hóa float [0,1] <-> uint8
   │
   ├──► naive_blend.py   (baseline: copy-paste trực tiếp)
   └──► poisson_blend.py (thuật toán lõi: dựng & giải hệ Af=b)
   │
   ▼
ảnh so sánh side-by-side (background/source/naive/poisson) → results/
```

`mask_tool.py` và `generate_synthetic.py` là 2 tiện ích độc lập, chạy **trước**
pipeline chính (vẽ mask / sinh ảnh test), không nằm trong luồng xử lý chính.

Điểm thiết kế đáng chú ý: `poisson_blend.py` factorize ma trận hệ số `A` **một
lần duy nhất** rồi tái sử dụng cho cả 3 kênh màu (`A` không phụ thuộc kênh) —
đây là lựa chọn kiến trúc ảnh hưởng trực tiếp tới hiệu năng, nên nhắc ở đây
thay vì chỉ ở phần lý thuyết.

## Kiến trúc module 2 — Panoramic Stitching

```
run_stitch.py (CLI, --detector sift|orb)
   │
   ▼
pipeline.py (6 bước, KHÔNG biết SIFT/ORB là gì)
   1. load_and_preprocess
   2. detect_and_describe ──────► detectors.py (registry SIFT/ORB/SURF)
   3. match_features                  │  nơi DUY NHẤT biết sự khác biệt
   4. estimate_homography             │  giữa các detector
   5. warp_and_align
   6. blend_overlap
   │
   ├──► metrics.py (thu thập số liệu mỗi bước: thời gian, inlier ratio, ...)
   ▼
panorama + 1 dòng metrics/cặp ảnh → results/stitching/metrics.csv
```

Đây là quyết định kiến trúc quan trọng nhất của module này: **pipeline
detector-agnostic**. `pipeline.py` chỉ gọi `detector.detect_and_compute(gray)`
và đọc `detector.norm_type`, không có `if sift / elif orb` nào trong đó. Nhờ
vậy:

- Phần 2 xây `pipeline.py` + chạy với SIFT.
- Phần 3 **không sửa `pipeline.py`**, chỉ đổi 1 tham số (`--detector orb`)
  hoặc thêm detector mới vào `detectors.py` — đảm bảo kết quả so sánh SIFT vs
  ORB ở mục 4.3 là so sánh công bằng (cùng 1 pipeline, chỉ khác bước trích đặc
  trưng).
- Nếu Phần 3 từng phải sửa `pipeline.py` để ORB chạy đúng, nghĩa là ranh giới
  module bị vi phạm — cần ghi lại trong phần hạn chế (mục 5.4/6.2) nếu có.

`generate_synthetic_scene.py` tương tự `generate_synthetic.py` bên module 1:
công cụ chuẩn bị dữ liệu test, đứng ngoài luồng xử lý chính.

## Vì sao không dùng 1 kiến trúc chung/trừu tượng hơn cho cả 2 module

Có thể nghĩ tới việc dựng 1 "Pipeline" base class chung rồi cho 2 module kế
thừa, nhưng 2 bài toán không chia sẻ bước xử lý nào ở mức có ý nghĩa (một bên
là giải hệ phương trình tuyến tính trên từng pixel, một bên là ước lượng mô
hình hình học từ tập điểm đặc trưng rời rạc) — thêm lớp trừu tượng chung chỉ
làm tăng độ phức tạp mà không tái sử dụng được code thật sự. Lựa chọn tách
biệt hoàn toàn cũng khớp với cách phân công nhân sự (mỗi module 1-2 người phụ
trách, tối thiểu hóa xung đột khi sửa code song song — xem `README.md` mục
"Shared git workflow").

## Quy ước chung áp dụng cho cả 2 module

| Quy ước | Module 1 | Module 2 |
|---|---|---|
| Input cố định | `data/gradient_domain/` | `data/stitching/` |
| Output tái sinh được | `results/gradient_domain/` | `results/stitching/` |
| Thuật toán lõi tách khỏi CLI | `poisson_blend.py` / `naive_blend.py` | `pipeline.py` |
| Điểm mở rộng duy nhất | cờ `--mixed-gradients` | `detectors.py` (thêm detector mới) |
| Số liệu định lượng | thời gian naive vs Poisson (in console) | `metrics.py` → `metrics.csv` (keypoint, inlier ratio, reprojection error, thời gian từng bước) |

*(TODO: vẽ lại 2 sơ đồ khối ở trên thành hình minh họa (draw.io/PowerPoint),
chèn vào `report/figures/`, dùng cho mục 3.1 trong bản PDF cuối cùng — phần
ASCII ở đây chỉ để tham khảo khi viết.)*
