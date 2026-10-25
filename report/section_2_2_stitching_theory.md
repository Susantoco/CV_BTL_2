# Mục 2.2 — Ghép ảnh toàn cảnh: pipeline & cơ sở lý thuyết

> **Bản nháp dựng sẵn cho Phần 2 (người phụ trách SIFT).** Vì pipeline dùng
> chung cho cả Phần 2/3 đã được xây dựng sẵn trong `src/stitching/` để đảm
> bảo tính nhất quán, phần lý thuyết dưới đây được soạn kèm theo luôn — người
> phụ trách Phần 2 đọc lại, chỉnh sửa theo cách hiểu của mình và bổ sung
> phần giải thích riêng về SIFT trước khi đưa vào báo cáo (xem lưu ý học
> thuật trong `docs/HD-BTL-CV.pdf`: không nên nộp nguyên văn nội dung AI
> soạn).

## Bài toán

**Input:** 3–4 ảnh chụp cùng một cảnh, từ cùng một vị trí quan sát nhưng góc
xoay camera khác nhau, có vùng nhìn chồng lấn giữa các ảnh liên tiếp.

**Output:** một ảnh toàn cảnh (panorama) duy nhất, góc nhìn rộng hơn, các
ảnh con được căn chỉnh và ghép liền mạch tại vùng chồng lấn.

**Giả định:** camera xoay quanh gần đúng một tâm quang học cố định (không có
dịch chuyển tịnh tiến lớn) — đây là điều kiện để một phép biến đổi
**homography** (biến đổi phối cảnh 2D) có thể mô tả chính xác quan hệ giữa
2 ảnh chụp từ cùng 1 điểm nhìn.

## Pipeline (6 bước, `src/stitching/pipeline.py`)

### 1. Load & tiền xử lý (`load_and_preprocess`)
Đọc ảnh màu, resize nếu cạnh lớn nhất vượt `max_dim` (mặc định 1600px, để
giới hạn thời gian trích đặc trưng/giải RANSAC), chuyển ảnh xám cho bước
trích đặc trưng (hầu hết detector hoạt động trên gradient độ sáng, không cần
thông tin màu).

### 2. Trích đặc trưng (`detect_and_describe`, qua `detectors.py`)
Với mỗi ảnh, phát hiện các điểm đặc trưng (keypoint) bất biến với phép xoay/
tỉ lệ, và tính **descriptor** (vector mô tả vùng lân cận mỗi keypoint) để có
thể so khớp giữa các ảnh. Pipeline không quan tâm detector cụ thể là gì —
chỉ cần nó trả về `(keypoints, descriptors)` theo đúng API của OpenCV
(`detectAndCompute`).

### 3. So khớp đặc trưng (`match_features`)
Dùng **Brute-Force Matcher** với **KNN (k=2)**: với mỗi descriptor ở ảnh 1,
tìm 2 descriptor gần nhất ở ảnh 2. Áp dụng **Lowe's ratio test**: chỉ giữ
match nếu khoảng cách gần nhất `m.distance < ratio * n.distance` (mặc định
`ratio=0.75`) — loại bỏ các match mơ hồ (2 ứng viên gần bằng nhau → không đáng
tin). `norm_type` (L2 cho descriptor dạng vector thực như SIFT/SURF, Hamming
cho descriptor nhị phân như ORB) được lấy từ chính detector đang dùng.

### 4. Ước lượng homography (`estimate_homography`)
Từ tập match tốt, giải phương trình `H` sao cho `dst ≈ H · src` (tọa độ
đồng nhất), bằng `cv2.findHomography(..., cv2.RANSAC, ransac_thresh)`.
**RANSAC** cần thiết vì tập match vẫn còn outlier (match sai do nhầm lẫn đặc
trưng tương tự ở vị trí khác) — RANSAC lặp lấy mẫu ngẫu nhiên 4 điểm, ước
lượng H, đếm số inlier (điểm khớp với sai số nhỏ hơn ngưỡng), chọn H có nhiều
inlier nhất.

### 5. Warp & căn chỉnh (`warp_and_align`)
Warp ảnh trái theo `H` vào hệ tọa độ ảnh phải bằng
`cv2.warpPerspective`. Vì ảnh sau warp có thể có tọa độ âm/mở rộng ra ngoài
khung ảnh gốc, pipeline tính trước bounding box của 4 góc ảnh sau warp hợp
với khung ảnh phải, rồi áp thêm một phép tịnh tiến để toàn bộ nội dung nằm
trong tọa độ dương — tránh bị cắt mất một phần panorama.

### 6. Blend vùng chồng lấn (`blend_overlap`)
Blend cơ bản bằng **feathering**: trọng số mỗi ảnh tại một điểm tỉ lệ với
khoảng cách từ điểm đó đến biên vùng ảnh đó phủ tới (`cv2.distanceTransform`)
— điểm càng gần "sâu" trong một ảnh, trọng số ảnh đó càng cao; tại chính giữa
vùng chồng lấn, 2 ảnh được trộn theo tỉ lệ gần 1:1. Cách này mượt hơn nhiều so
với lấy trung bình cộng đơn giản (vốn gây bóng mờ ở biên vùng chồng lấn) hay
cắt cứng giữa 2 ảnh (vốn vẫn có thể lộ seam nếu phơi sáng 2 ảnh khác nhau).

### Ghép N ảnh (`stitch_images`)
Với 3-4 ảnh, pipeline ghép tuần tự: ghép ảnh 1↔2 ra panorama tạm, rồi ghép
panorama đó với ảnh 3, v.v. Cách này đơn giản và đủ tốt khi thứ tự ảnh đã
biết trước (đúng với giả định đề bài: ảnh được chụp theo thứ tự góc xoay).

## Vì sao pipeline "detector-agnostic"

Toàn bộ 6 bước trên **không hề nhắc tới SIFT/ORB/SURF cụ thể** — chúng chỉ
gọi `detector.detect_and_compute(gray)` và dùng `detector.norm_type` để chọn
matcher phù hợp. File `detectors.py` là nơi duy nhất biết sự khác biệt giữa
các phương pháp (cách khởi tạo `cv2.SIFT_create()` / `cv2.ORB_create()` /
v.v. và norm type tương ứng). Nhờ vậy Phần 3 chỉ cần đổi 1 tham số
(`--detector orb`) để chạy lại toàn bộ pipeline mà không đụng tới logic ghép
ảnh.

## Vai trò SIFT trong pipeline này

*(TODO — người phụ trách Phần 2 bổ sung: tóm tắt nguyên lý SIFT — Scale-
Space Extrema qua Difference-of-Gaussian, gán hướng chủ đạo, descriptor 128
chiều theo histogram gradient cục bộ — và vì sao nó phù hợp làm detector
"chuẩn tham chiếu" để so sánh với ORB ở Phần 3: bất biến với scale/rotation
tốt, descriptor float chính xác cao nhưng tính toán chậm hơn.)*
