# Mục 3 (phần Stitching) — Phân tích & đánh giá chung (Phần 2 + Phần 3)

> **Template — viết chung sau khi cả 2 phần có kết quả thật trên ảnh tự
> chụp.** Các gợi ý dưới đây dựa theo đúng các câu hỏi yêu cầu trong
> `docs/CV-project-2.pdf` mục 3 và `docs/HD-BTL-CV.pdf` mục 2.5.

## Ưu / nhược điểm SIFT vs ORB (điền sau khi có bảng số liệu thật)

Gợi ý khung so sánh (dựa trên đặc tính thuật toán + số liệu ở
`section_2_2_stitching_results.md`):

| Tiêu chí | SIFT | ORB |
|---|---|---|
| Tốc độ trích đặc trưng | Chậm hơn (DoG pyramid + descriptor 128-dim float) | Nhanh hơn nhiều (FAST + BRIEF nhị phân) |
| Độ chính xác căn chỉnh (reprojection error) | ? (điền số liệu thật) | ? |
| Số lượng keypoint/ảnh | Thường ít hơn ORB | Thường nhiều hơn |
| Bất biến scale/rotation | Tốt (thiết kế gốc cho mục đích này) | Có (nhờ pyramid + hướng), nhưng kém ổn định hơn SIFT ở scale lớn |
| Bản quyền/cấp phép | Hết hạn patent, dùng tự do trong OpenCV hiện tại | Luôn miễn phí, thiết kế để thay thế SIFT/SURF có patent |
| Phù hợp ứng dụng | Khi cần độ chính xác cao, không giới hạn thời gian thực | Khi cần tốc độ, tài nguyên hạn chế (mobile/embedded) |

## Câu hỏi cần trả lời (theo đề bài)

1. **Độ chính xác căn chỉnh:** so `reprojection_error_px` và `inlier_ratio`
   giữa 2 detector trên cùng bộ ảnh — detector nào cho sai số nhỏ hơn / tỉ lệ
   inlier cao hơn tức là tìm được correspondence đáng tin cậy hơn.
2. **Tính liên tục của ảnh:** quan sát trực quan panorama — có đường gấp
   khúc ở biên ghép không, có chi tiết bị nhân đôi/mờ không (dấu hiệu
   homography ước lượng sai hoặc blend chưa tốt).
3. **Chất lượng trực quan:** ánh sáng/màu sắc có nhất quán giữa các ảnh con
   không (pipeline hiện tại CHƯA làm exposure compensation — nếu ảnh tự chụp
   có độ phơi sáng khác nhau rõ rệt giữa các góc, đây sẽ là điểm yếu cần nêu).
4. **Trường hợp thành công / khó khăn:** nêu cụ thể bộ ảnh nào ghép tốt
   (texture phong phú, overlap đủ lớn ≥20-30%) và bộ ảnh nào gặp khó khăn
   (vùng chồng lấn ít chi tiết/lặp pattern — dễ match sai; overlap quá nhỏ —
   không đủ 4 match để ước lượng homography; chuyển động không phải thuần
   xoay quanh 1 tâm — vi phạm giả định homography).

## Hạn chế chung của pipeline hiện tại (để bàn thêm)

- Ghép tuần tự (pairwise) thay vì tối ưu đồng thời nhiều ảnh (global bundle
  adjustment) — sai số có thể tích lũy dần khi số ảnh tăng lên.
- Blend bằng feathering đơn giản, chưa xử lý chênh lệch phơi sáng
  (exposure compensation) hay multi-band blending như các pipeline panorama
  chuyên nghiệp (vd OpenCV Stitcher, Hugin).
- Giả định camera xoay quanh đúng 1 tâm quang học — ảnh chụp cầm tay có dịch
  chuyển vị trí nhỏ sẽ gây lỗi parallax, homography không còn mô tả chính xác
  quan hệ hình học giữa các ảnh.

## Hướng cải thiện (dẫn sang mục 2.6 Kết luận)

- Thêm exposure compensation trước khi blend.
- Thử multi-band blending (Laplacian pyramid) thay vì feathering đơn.
- Với >4 ảnh, cân nhắc bundle adjustment toàn cục thay vì ghép tuần tự.
