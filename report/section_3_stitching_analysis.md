# Mục 3 (phần Stitching) — Phân tích & đánh giá chung (Phần 2 + Phần 3)

Phần này trình bày đánh giá tổng hợp về hiệu năng thực tế, ưu nhược điểm của hai phương pháp trích xuất đặc trưng **SIFT** và **ORB** trên cùng một pipeline ghép ảnh toàn cảnh dựa trên đặc trưng (Feature-based Image Stitching).

---

## Ưu / nhược điểm SIFT vs ORB

Dựa trên thuật toán gốc và kết quả thực nghiệm thu được:

| Tiêu chí | SIFT (Scale-Invariant Feature Transform) | ORB (Oriented FAST and Rotated BRIEF) |
|---|---|---|
| **Thuật toán phát hiện** | DoG (Difference of Gaussians) trên không gian tỷ lệ (Scale-space) | FAST góc cạnh kết hợp Pyramid để tính hướng (Orientation) |
| **Bộ mô tả (Descriptor)** | 128 giá trị số thực (Float, $L_2$ Norm) | 256-bit nhị phân (Binary, Hamming Distance) |
| **Độ chính xác căn chỉnh** | **Rất cao** (Reprojection error $\approx 0.04 - 0.45\text{ px}$) | **Trung bình** (Reprojection error $\approx 0.45 - 1.00\text{ px}$) |
| **Tỉ lệ Inlier / Khả năng lọc nhiễu** | Duy trì tỉ lệ điểm ghép đúng cao và ổn định trên ảnh chất lượng cao | Tốt trên cảnh lý tưởng, nhưng dễ bị sai (false matches) ở cảnh phức tạp |
| **Tính bền vững (Robustness)** | **Rất cao.** Vượt qua bộ ảnh khó `member2_set` ngay cả khi góc xoay lớn | **Kém.** Thất bại hoàn toàn trên `member2_set`, tạo Homography lỗi gây tràn RAM |
| **Tốc độ tính toán** | Chậm hơn ở khâu tạo bộ mô tả Float 128 chiều | Nhanh hơn nhờ thuật toán FAST và so khớp khoảng cách Hamming bằng phép XOR |
| **Bản quyền & Sử dụng** | Đã hết hạn patent, sẵn sàng trong thư viện OpenCV chuẩn | Miễn phí mã nguồn mở, tối ưu cho ứng dụng thời gian thực |

---

## Trả lời các câu hỏi đánh giá theo yêu cầu bài tập

### 1. Độ chính xác căn chỉnh (Alignment Accuracy)
- **SIFT vượt trội hơn hẳn ORB về độ chính xác.** Trên bộ ảnh `member3_set`, SIFT đạt sai số tái phản chiếu trung bình dưới $0.4\text{ px}$, trong khi ORB là $0.88\text{ px}$. 
- Lý do là bộ mô tả 128 chiều của SIFT ghi nhận chi tiết độ dốc hướng (gradient histograms) vùng lân cận cực kỳ chi tiết, giúp xác định tọa độ sub-pixel chính xác hơn so với bộ mô tả nhị phân của ORB.

### 2. Tính liên tục của ảnh & Chất lượng trực quan
- Các bức ảnh ghép thành công bởi SIFT (`member3_set` và `member2_set`) thể hiện tính liên tục tuyệt vời ở các đường biên kiến trúc, cột nhà và khung cảnh. Thuật toán pha trộn Feathering (Distance Transform) giúp loại bỏ triệt để vệt nối biên (seams).
- Tuy nhiên, do pipeline chưa tích hợp **bù phơi sáng (Exposure Compensation)**, nếu các ảnh con có độ sáng không đều (như trong `member2_set`), ảnh toàn cảnh sẽ xuất hiện vùng chuyển màu sáng-tối cục bộ.

### 3. Phân tích các trường hợp thành công và khó khăn
- **Trường hợp thành công (`sample_synthetic`, `member3_set`):**
  - Cảnh vật có họa tiết (texture) phong phú, điểm góc rõ ràng.
  - Vùng chồng lấn giữa các ảnh đạt khoảng $30\% - 50\%$.
  - Ảnh được chụp xoay quanh cùng một tâm quang học (Optical Center), thỏa mãn điều kiện biến đổi Homography.
- **Trường hợp gặp khó khăn / Thất bại (`member2_set` với ORB):**
  - Ảnh tự chụp cầm tay có độ rung nhiễu, góc nghiêng lớn và sự chênh lệch ánh sáng.
  - ORB không lọc được các điểm khớp sai (outliers) ở vùng nhiễu, làm sai lệch mô hình RANSAC. Điều này dẫn đến việc tính toán ma trận Homography bị biến dạng cực đoan, phóng to ảnh lên hàng chục nghìn pixel và gây ngưng trệ chương trình do tràn bộ nhớ (cần hơn 53 GB RAM).

---

## Hạn chế chung của pipeline hiện tại

1. **Ghép tuần tự (Pairwise Sequential Stitching):** Pipeline ghép nối tiếp từng cặp ảnh một. Tích lũy sai số (drift error) tăng dần theo từng lượt ghép, dẫn đến ảnh ở các bước sau dễ bị méo hơn.
2. **Thiếu cơ chế kiểm tra Homography hợp lệ (Homography Sanity Check):** Pipeline chưa có bước kiểm tra xem ma trận $H$ thu được có làm biến dạng diện tích quá mức hay không trước khi thực hiện `cv2.warpPerspective`.
3. **Pha trộn cơ bản:** Phương pháp Feathering hoạt động tốt trên ảnh phẳng nhưng sẽ tạo ra hiệu ứng "bóng ma" (ghosting) nếu cảnh vật có đối tượng chuyển động.

---

## Hướng cải thiện

1. Tích hợp cơ chế kiểm tra điều kiện ma trận Homography (ví dụ: kiểm tra định thức ma trận $\det(H)$ hoặc góc bóp méo) để cảnh báo/loại bỏ ngay khi detector trích xuất sai.
2. Nâng cấp thuật toán blend lên **Multi-band Blending (Laplacian Pyramid)** để xử lý triệt để hiện tượng bóng ma và chênh lệch ánh sáng.
3. Áp dụng **Bundle Adjustment toàn cục** thay vì ghép từng cặp tuần tự khi làm việc với tập ảnh panorama lớn ($> 5$ ảnh).