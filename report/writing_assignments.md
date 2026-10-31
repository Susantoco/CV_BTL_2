# Phân công viết báo cáo theo mục lục

> Khung mục lục dùng chung cho báo cáo cuối cùng (gộp cả 3 phần). Cột "Nguồn /
> ghi chú" trỏ tới file nháp đã có sẵn trong `report/` (nếu có) để copy/chỉnh
> sửa lại, hoặc ghi "Chưa có" nếu cần viết mới từ đầu.

| Mục | Nội dung | Người viết | Nguồn / ghi chú |
|---|---|---|---|
| **1** | Giới thiệu chung: mục tiêu đề bài (gradient domain + stitching), phân công nhóm, tổng quan 2 bài toán | Chung | Chưa có file — dựa vào `docs/CV-project-2.pdf` mục 1 + bảng phân công trong `README.md` |
| **2.1** | Tổng quan Gradient Domain Editing: bài toán, input/output, phạm vi/giả định | Part 1 | `section_2_1_gradient_theory.md` — phần "Mô tả bài toán" |
| **2.2** | Nguyên lý Poisson Image Editing: công thức biến phân, phương trình Poisson, rời rạc hóa, mixed gradients | Part 1 | Cùng file trên, phần "Nguyên lý..." + "Rời rạc hóa" + "Mixed gradients" |
| **2.3** | Tổng quan Image Stitching: bài toán panorama, 3-4 ảnh cùng vị trí khác góc xoay, giả định homography | Part 2 | `section_2_2_stitching_theory.md` — phần "Bài toán" |
| **2.4** | Phát hiện & mô tả đặc trưng: lý thuyết SIFT + ORB | Part 2 (SIFT) + Part 3 (ORB) | Phần "Trích đặc trưng" đã có khung chung; TODO "Vai trò SIFT" chưa điền; ORB chưa có — Part 3 viết thêm song song |
| **2.5** | So khớp đặc trưng: BFMatcher KNN + Lowe's ratio test | Part 2 | Phần "So khớp đặc trưng" đã viết đủ |
| **2.6** | Homography và RANSAC | Part 2 | Phần "Ước lượng homography" đã viết đủ |
| **2.7** | Căn chỉnh ảnh và blending: warpPerspective, feathering | Part 2 | Phần "Warp & căn chỉnh" + "Blend vùng chồng lấn" đã viết đủ |
| **3.1** | Kiến trúc hệ thống tổng thể: 2 module độc lập, sơ đồ khối | Chung | Chưa có — cần viết mới (vd sơ đồ `src/gradient_domain/` vs `src/stitching/`) |
| **3.2** | Phần I — Gradient Domain Editing: pipeline high-level + code cốt lõi | Part 1 | Chưa có file riêng — cần viết, trích code từ `poisson_blend.py` |
| **3.3** | Phần II — Panoramic Image Stitching: pipeline high-level + code cốt lõi, phần đổi sang ORB | Part 2 (khung pipeline) + Part 3 (đoạn ORB) | `section_2_2_stitching_theory.md` phần "Pipeline (6 bước)" + "Vì sao detector-agnostic" (bỏ bớt phần lý thuyết thuần đã đưa lên 2.4-2.7) |
| **3.4** | Thiết kế thực nghiệm và cấu hình: bộ ảnh dùng, tham số (ratio, ransac_thresh, max_dim, offset...) | Part 1 (config gradient) + Part 2/3 (config stitching) | Rải rác trong README "Usage" — gom thành 1 bảng |
| **4.1** | Kết quả Gradient Domain Editing: ảnh before/after 3 bộ test | Part 1 | `section_3_gradient_analysis.md` — phần so sánh naive vs Poisson |
| **4.2** | Kết quả Image Stitching: ảnh panorama SIFT và ORB | Part 2 (SIFT) + Part 3 (ORB) | `section_2_2_stitching_results.md` — "Ảnh panorama minh họa" (còn TODO chèn ảnh thật) |
| **4.3** | So sánh phương pháp trích xuất đặc trưng: bảng số liệu SIFT vs ORB | Part 3 | `section_2_2_stitching_results.md` — bảng chính, cần thay số liệu thật từ `metrics.csv` |
| **4.4** | Tổng hợp kết quả định lượng + định tính (cả 2 bài toán) | Chung (Part 3 chủ trì bảng, Part 1 góp nhận xét) | Chưa có — tổng hợp từ 4.1-4.3 |
| **5.1** | Ưu/nhược điểm từng phương pháp: Poisson vs naive-paste; SIFT vs ORB | Part 1 (đoạn Poisson) + Part 2/3 (đoạn SIFT/ORB) | `section_3_gradient_analysis.md` "Tổng kết điểm mạnh/yếu" + `section_3_stitching_analysis.md` "Ưu/nhược SIFT vs ORB" |
| **5.2** | Trường hợp thành công/thất bại cụ thể | Chung | `section_3_stitching_analysis.md` mục "Câu hỏi cần trả lời" ý 4 + phần mask tight/loose bên gradient |
| **5.3** | Ảnh hưởng dữ liệu & tham số: mask size, ratio threshold, overlap % | Chung | `section_3_gradient_analysis.md` (mask) + `section_3_stitching_analysis.md` (overlap, RANSAC) |
| **5.4** | Nguyên nhân sai lệch & hướng cải thiện | Chung | `section_3_gradient_analysis.md` (chênh tông màu) + `section_3_stitching_analysis.md` "Hạn chế chung" |
| **6.1** | Kết luận: tóm tắt những gì đã đạt được | Chung (viết cuối cùng) | Tổng hợp toàn bài |
| **6.2** | Hạn chế | Chung | Gộp từ 5.4 + "Hạn chế chung của pipeline" |
| **6.3** | Hướng phát triển | Chung | `section_3_stitching_analysis.md` mục "Hướng cải thiện" + phần tương ứng gradient |
