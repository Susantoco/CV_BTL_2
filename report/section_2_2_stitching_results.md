# Mục 2.2 (tiếp) — Kết quả thực nghiệm & so sánh SIFT vs ORB

> **Template cho Phần 3.** Chạy đủ các lệnh bên dưới trên MỌI bộ ảnh (mẫu
> tổng hợp + bộ tự chụp của Phần 2 + bộ tự chụp của Phần 3) với CẢ 2 detector,
> rồi điền số liệu thật vào bảng thay cho phần ví dụ minh họa (lấy từ
> `data/stitching/sample_synthetic/`, chỉ mang tính minh họa pipeline chạy
> được, KHÔNG phải ảnh chụp thật nên không dùng để kết luận chất lượng
> phương pháp).

## Cách chạy để lấy số liệu

```bash
for SET in sample_synthetic member2_set member3_set; do
  for DET in sift orb; do
    python -m src.stitching.run_stitch \
        --images "data/stitching/$SET/*.jpg" \
        --detector $DET \
        --out "results/stitching/${DET}_${SET}.jpg" \
        --metrics-out results/stitching/metrics.csv \
        --image-set-name $SET
  done
done
```

(Đổi đuôi `*.jpg` cho đúng với bộ ảnh thật; `sample_synthetic` dùng `*.png`.)

Mỗi dòng lệnh append 1 dòng/cặp ảnh vào `results/stitching/metrics.csv` với
các cột: `image_set, detector, pair_index, num_keypoints_left/right,
num_good_matches, num_inliers, inlier_ratio, reprojection_error_px,
t_detect_s, t_match_s, t_homography_s, t_warp_s, t_blend_s, t_total_s`.

## Bảng so sánh (ví dụ minh họa — bộ `sample_synthetic`, 3 ảnh, 2 cặp ghép)

| Bộ ảnh | Detector | Cặp | #Keypoints (trái+phải) | #Good matches | #Inlier | Tỉ lệ inlier | Reproj. error (px) | Thời gian tổng (ms) |
|---|---|---|---|---|---|---|---|---|
| sample_synthetic | SIFT | 1 | 512 + 588 | 184 | 151 | 82.1% | 0.04 | 439 |
| sample_synthetic | SIFT | 2 | 1004 + 580 | 246 | 142 | 57.7% | 0.06 | 623 |
| sample_synthetic | ORB  | 1 | 2310 + 2666 | 457 | 397 | 86.9% | 0.45 | 2020 |
| sample_synthetic | ORB  | 2 | 3825 + 2345 | 510 | 386 | 75.7% | 0.74 | 358 |

*(Số liệu trên lấy từ 1 lần chạy thực tế trên máy phát triển — dùng để minh
họa định dạng bảng, KHÔNG phải kết luận cuối cùng. Lưu ý thời gian chạy phụ
thuộc máy, chạy benchmark thật trên cùng 1 máy cho tất cả detector/bộ ảnh để
so sánh công bằng.)*

### Nhận xét sơ bộ từ ví dụ trên (cần kiểm chứng lại với ảnh thật)

- ORB phát hiện nhiều keypoint hơn SIFT đáng kể trên cùng ảnh (do thuật toán
  FAST + BRIEF rẻ hơn, phát hiện nhiều điểm góc hơn), nhưng mỗi keypoint ORB
  "rẻ" hơn về mặt tính toán lẫn độ phân biệt.
- Reprojection error của SIFT nhỏ hơn ORB khoảng 10 lần (~0.05px vs ~0.6px)
  → SIFT cho độ chính xác căn chỉnh hình học cao hơn trên ảnh tổng hợp có
  texture rõ ràng.
- Thời gian chạy KHÔNG nhất quán giữ 2 cặp của cùng 1 detector (ORB cặp 1 lâu
  hơn hẳn cặp 2) — có thể do JIT warm-up của OpenCV hoặc số lượng keypoint
  dao động; cần chạy lại nhiều lần lấy trung bình khi viết báo cáo thật.

## Ảnh panorama minh họa

Chèn `results/stitching/sift_<set>.jpg` và `results/stitching/orb_<set>.jpg`
cạnh nhau cho từng bộ ảnh vào `report/figures/` để so sánh trực quan tính
liên tục (có bị gấp khúc / nhân đôi chi tiết ở vùng chồng lấn không) và chất
lượng blend (có còn thấy đường nối không).

## TODO còn thiếu trước khi nộp

- [ ] Chạy đủ bộ ảnh tự chụp của Phần 2 (`member2_set`) và Phần 3
      (`member3_set`) với cả 2 detector.
- [ ] Thay bảng số liệu minh họa trên bằng số liệu thật, tính trung bình nếu
      chạy nhiều lần.
- [ ] Chèn ảnh panorama thật vào `report/figures/`.
- [ ] Ghi chú rõ trường hợp nào pipeline thất bại (vd quá ít match, ảnh thiếu
      overlap) — xem `src/stitching/pipeline.py:estimate_homography` sẽ raise
      `ValueError` nếu có ít hơn 4 match, đó là dấu hiệu bộ ảnh không phù hợp
      hoặc detector không tìm đủ đặc trưng chung.
