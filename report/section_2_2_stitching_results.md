# Mục 2.2 (tiếp) — Kết quả thực nghiệm & so sánh SIFT vs ORB

File báo cáo này tổng hợp số liệu thực nghiệm trực tiếp từ quá trình chạy pipeline ghép ảnh toàn cảnh (`src/stitching/run_stitch.py`) trên 3 bộ dữ liệu: ảnh tổng hợp (`sample_synthetic`), bộ ảnh tự chụp của Phần 2 (`member2_set`) và bộ ảnh tự chụp của Phần 3 (`member3_set`).

## Bảng so sánh kết quả thực nghiệm

Dưới đây là bảng số liệu thu thập được từ file `results/stitching/metrics.csv`:

| Bộ ảnh | Detector | Cặp | Keypoints (L + R) | Good matches | Inliers | Tỉ lệ Inlier | Reproj. error (px) | Thời gian tổng (ms) |
|---|---|---|---|---|---|---|---|---|
| **sample_synthetic** | SIFT | 1 | 512 + 588 | 184 | 151 | 82.07% | 0.0448 | 439.2 |
| **sample_synthetic** | SIFT | 2 | 1004 + 580 | 246 | 142 | 57.72% | 0.0576 | 622.7 |
| **sample_synthetic** | ORB | 1 | 2310 + 2666 | 457 | 397 | 86.87% | 0.4473 | 2019.9 |
| **sample_synthetic** | ORB | 2 | 3825 + 2345 | 510 | 386 | 75.69% | 0.7411 | 358.0 |
| **member3_set** | SIFT | 1 | 2265 + 2247 | 876 | 867 | 98.97% | 0.4223 | 183.0 |
| **member3_set** | SIFT | 2 | 3562 + 2087 | 827 | 823 | 99.52% | 0.4454 | 195.2 |
| **member3_set** | SIFT | 3 | 4820 + 1899 | 897 | 883 | 98.44% | 0.3510 | 324.2 |
| **member3_set** | SIFT | 4 | 5277 + 1905 | 797 | 786 | 98.62% | 0.3655 | 1600.5 |
| **member3_set** | ORB | 1 | 3620 + 3517 | 848 | 841 | 99.17% | 0.9996 | 3473.9 |
| **member3_set** | ORB | 2 | 4000 + 3435 | 380 | 373 | 98.16% | 0.9359 | 135.4 |
| **member3_set** | ORB | 3 | 4000 + 3430 | 397 | 380 | 95.72% | 0.7708 | 244.2 |
| **member3_set** | ORB | 4 | 4000 + 3378 | 494 | 478 | 96.76% | 0.8646 | 1138.4 |
| **member2_set** | SIFT | 1 | 1286 + 1413 | 169 | 55 | 32.54% | 0.5349 | 301.0 |
| **member2_set** | SIFT | 2 | 2969 + 1564 | 248 | 72 | 29.03% | 1.6107 | 617.1 |
| **member2_set** | SIFT | 3 | 4619 + 1547 | 287 | 134 | 46.69% | 1.2174 | 2524.4 |
| **member2_set** | SIFT | 4 | 3961 + 1563 | 236 | 157 | 66.53% | 1.3503 | 4469.9 |
| **member2_set** | ORB | 1..4 | N/A | N/A | N/A | N/A | Thất bại (Out of Memory) | N/A |

### Phân tích chi tiết số liệu thực nghiệm

1. **Số lượng Keypoints & Good Matches:**
   - **ORB** trích xuất số lượng điểm đặc trưng lớn hơn đáng kể so với **SIFT** trên hầu hết các bộ ảnh (ví dụ ở `member3_set`, ORB đạt giới hạn tối đa `nfeatures=4000` keypoint ở các ảnh sau).
   - Tuy nhiên, số lượng điểm khớp chất lượng (`Good matches` sau Lowe's ratio test) của ORB lại tương đương hoặc ít hơn SIFT (đặc biệt ở các cặp 2, 3, 4 của `member3_set`, SIFT đạt ~800-900 good matches trong khi ORB chỉ đạt ~380-490 good matches).

2. **Độ chính xác căn chỉnh (Reprojection Error):**
   - **SIFT vượt trội hoàn toàn về độ chính xác hình học:** Trên bộ ảnh tổng hợp `sample_synthetic`, sai số biến đổi của SIFT rất nhỏ ($~0.04 - 0.05\text{ px}$), nhỏ hơn ORB ($~0.45 - 0.74\text{ px}$) khoảng 10 lần.
   - Trên bộ ảnh thật `member3_set`, SIFT duy trì sai số ở mức rất thấp ($0.35 - 0.45\text{ px}$), trong khi ORB có sai số dao động cao từ $0.77 - 1.00\text{ px}$.
   - Trên bộ ảnh khó `member2_set` (có góc nghiêng và chênh lệch phơi sáng), tỉ lệ inlier của SIFT bị tụt giảm nghiêm trọng (xuống còn $29% - 66\%$), đẩy sai số tái phản chiếu lên $0.53 - 1.61\text{ px}$.

3. **Hiện tượng thất bại hoàn toàn của ORB trên bộ ảnh `member2_set`:**
   - Khi chạy ORB trên `member2_set`, chương trình lập tức gặp lỗi quá tải bộ nhớ (`cv2.OutOfMemoryError` / `ArrayMemoryError`), do OpenCV yêu cầu cấp phát tới hơn 53 GB RAM khi thực hiện bước `cv2.warpPerspective`.
   - **Nguyên nhân:** Bộ ảnh `member2_set` chứa nhiều vùng nhiễu/nền mờ. Bộ mô tả nhị phân BRIEF của ORB không đủ độ phân biệt trong trường hợp này, dẫn đến các điểm so khớp bị sai lệch nghiêm trọng (outliers cực đoan). Khi RANSAC ước lượng ma trận Homography ($H$) dựa trên tập điểm nhiễu này, ma trận bị suy biến khiến kích thước khung tranh (`canvas_size`) phình to tới hàng chục nghìn pixel ($17174 \times 29926$), làm tràn RAM hệ thống.

---

## Ảnh panorama minh họa

*(Thành viên chèn ảnh chụp màn hình kết quả từ thư mục `results/stitching/` vào đây)*

- **Bộ `sample_synthetic`:** Cả SIFT và ORB đều ghép thành công. Ảnh mượt mà, không lệch khung.
- **Bộ `member3_set`:** Cả SIFT và ORB ghép thành công.
- **Bộ `member2_set`:** 
  - SIFT ghép thành công toàn bộ 5 ảnh (dù thời gian tổng tăng lên 4.47s ở bước cuối do canvas lớn).
  - ORB thất bại tại cặp ảnh thứ nhất do ma trận Homography tính sai.

---