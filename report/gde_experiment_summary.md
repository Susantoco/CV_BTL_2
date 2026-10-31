# Tổng hợp thực nghiệm — Gradient Domain Editing (GDE)

> Tài liệu tổng hợp để gửi viết phần "Kết quả thực nghiệm" trong báo cáo.
> Toàn bộ số liệu/ảnh trong file này lấy từ kết quả có sẵn trong
> `results/gradient_domain/` cộng với 2 lần chạy bổ sung
> (`results/gradient_domain/mixed_test/`) để lấy số liệu Mixed Gradients
> và thời gian chạy — không có số liệu nào bị suy diễn/bịa đặt. Chỗ nào
> không có dữ liệu được ghi rõ "Không có dữ liệu".

## 1. Tổng quan thực nghiệm

4 test case chính:

| # | Test case | Loại dữ liệu | Kích thước ảnh nền | Mask (số px) | Offset (oy, ox) |
|---|---|---|---|---|---|
| 1 | `edgecase` — tight mask | Synthetic | 400×600 | Tight, 21.323 px | (0, 0) |
| 2 | `edgecase` — loose mask | Synthetic (cùng cặp ảnh với #1) | 400×600 | Loose, 32.441 px | (0, 0) |
| 3 | `edgecase/challenging` | Synthetic | 400×600 | 21.323 px | (0, 0) |
| 4 | **Ảnh thực tế: cá vào nước** (offset 300) | Ảnh thật (`fish.jpg` ghép vào `water.jpg`) | 640×436 | 12.139 px | **(300, 100)** |

**Ghi chú về test case 4:** repo có 3 lần chạy khác với cùng cặp ảnh
nhưng offset nông hơn — `test1` = (200,100), `test2` = (150,100),
`test3` = (100,100) — và một lần chạy ở offset (300,100) lưu dưới tên
`real_compare`. Theo yêu cầu, **test case 4 trong tài liệu này dùng
offset (300,100)** (thay cho `test1`) vì đây là vị trí thể hiện rõ rệt
nhất hiện tượng cần phân tích (đổi màu do lệch tông nguồn/nền); các
offset (100,150,200) cho hiện tượng tương tự nhưng ít nổi bật hơn, không
phân tích chi tiết riêng trong tài liệu này.

**Cấu hình Mixed Gradients:** đã chạy **bổ sung** 2 lần tại đúng offset
(300,100) của test case 4 — một lần mặc định (chỉ dùng gradient nguồn),
một lần với `--mixed-gradients` — để có dữ liệu so sánh trực tiếp (xem
mục 3). Đây là thí nghiệm Mixed Gradients duy nhất tồn tại trong dự án.

## 2. Phân tích từng test case

### Test case 1: `edgecase` (tight mask) — "mặt trời" texture
- **Background:** nền trời gradient xanh nhạt, 400×600, sinh tổng hợp.
- **Source:** nền trời xanh hơi xám (lệch tông nhẹ so với background) +
  một "mặt trời" tổng hợp có gradient hướng tâm (vàng→cam), nhiễu, và
  các tia sáng toả ra.
- **Mask:** tight — ôm sát hình mặt trời + tia nắng (dilate 5×5), 21.323 px.
- **Naive Copy-Paste:** có một viền vuông/seam mờ quanh vùng mask do
  nền source và nền background lệch tông nhẹ.
- **Poisson Blending:** seam biến mất hoàn toàn; màu mặt trời gần như
  giữ nguyên vì 2 nền chỉ lệch tông nhẹ.
- **So sánh:** Poisson rõ ràng tốt hơn — không seam, không đổi màu đáng kể.
- **Cải thiện quan sát được:** loại bỏ hoàn toàn đường biên cứng.
- **Artifact/hạn chế:** không quan sát thấy artifact đáng kể ở độ phân
  giải ảnh hiện có.

### Test case 2: `edgecase` (loose mask) — cùng ảnh, mask rộng hơn
- **Background/Source:** giống hệt test case 1.
- **Mask:** loose — hình tròn lớn (bán kính ×1.45 so với vật thể),
  32.441 px, bao trọn nhiều vùng nền phẳng quanh mặt trời.
- **Naive Copy-Paste:** seam rõ rệt hơn nhiều so với tight — một vòng
  tròn lớn (nền ảnh source) hiện rõ trên nền background.
- **Poisson Blending:** vòng tròn seam biến mất hoàn toàn; bằng mắt
  thường ở độ phân giải ảnh hiện có, kết quả loose trông gần tương
  đương kết quả tight — không phát hiện rõ "halo" như mô tả lý thuyết
  ban đầu, cần ảnh độ phân giải cao hơn để xác nhận.
- **So sánh tight vs loose:** cả hai đều loại bỏ seam bằng Poisson,
  nhưng naive với loose mask tạo seam lớn và phản cảm hơn hẳn naive
  với tight mask — minh chứng mask càng ôm sát, naive-paste càng ít lỗi.

### Test case 3: `edgecase/challenging` — lệch tông màu mạnh (synthetic)
- **Background:** nền trời xanh (tương tự test 1, 2).
- **Source:** nền cam/vàng (gần như bù màu với nền xanh) + cùng mặt
  trời texture.
- **Mask:** tight, 21.323 px (giống mask tight test 1).
- **Naive Copy-Paste:** seam cực kỳ rõ — hình chữ nhật nền cam của
  source nổi bật hoàn toàn trên nền xanh.
- **Poisson Blending:** seam biến mất hoàn toàn **nhưng** mặt trời đổi
  màu triệt để — từ cam/vàng/đỏ sang xanh dương/tím/xanh lục — trong
  khi hình dạng, vành, tia nắng, vân tròn bên trong vẫn giữ nguyên
  cấu trúc.
- **So sánh:** Naive giữ đúng màu nhưng seam lộ liễu; Poisson xoá seam
  hoàn hảo nhưng hy sinh màu sắc thật của vật thể.
- **Ý nghĩa:** minh chứng định tính rõ nhất (bản synthetic) cho hạn chế
  "Poisson chỉ ràng buộc gradient, không ràng buộc giá trị tuyệt đối
  (DC component)".

### Test case 4: Ảnh thực tế — cá vào nước, offset (300, 100)
- **Background:** ảnh thật — cảnh dưới nước (mây trên mặt nước, vùng
  nước xanh bên dưới), 640×436.
- **Source:** ảnh thật một con cá bạc (vảy, vây, đuôi hồng/nâu) chụp
  trên nền trắng — chênh lệch tông màu cực lớn so với nền nước xanh.
- **Mask:** 12.139 px, bám theo hình con cá.
- **Naive Copy-Paste:** cá giữ đúng màu gốc (bạc/trắng/hồng) nhưng có
  viền trắng mờ rõ rệt bao quanh, đặc biệt ở vây lưng và đuôi (mask
  không khớp hoàn hảo với vùng vây mảnh, lộ rìa nền trắng của ảnh gốc)
  — seam rất dễ nhận ra bằng mắt.
- **Poisson Blending (non-mixed):** viền trắng biến mất hoàn toàn, cá
  hoà vào nước rất mượt — nhưng màu cá đổi hẳn từ bạc/trắng sang xanh
  đen/xanh dương đậm (gần giống màu nước xung quanh). Cấu trúc vảy,
  hình dạng vây vẫn nhận ra được, chỉ tông màu bị "nhuộm" theo nước.
- **So sánh trực tiếp:** Naive giữ đúng màu cá nhưng seam/viền trắng
  lộ rõ; Poisson xoá seam hoàn toàn nhưng đổi hẳn tông màu cá — cùng
  kiểu trade-off như test case 3, nhưng đây là **ảnh thật, không dàn
  dựng** — bằng chứng mạnh nhất trong toàn bộ thực nghiệm cho hạn chế
  "nguồn và nền lệch tông màu lớn".
- **Artifact khác:** viền trắng còn sót ở naive cho thấy mask chưa
  khớp hoàn hảo với các chi tiết mảnh (vây, đuôi) — hạn chế về chất
  lượng mask khi áp dụng cho ảnh thật có biên phức tạp.

## 3. Mixed Gradients

Đã chạy thực nghiệm bổ sung tại đúng offset (300,100) của test case 4
(cá/nước) — nơi lệch tông màu rõ nhất — để so sánh Poisson mặc định
(chỉ dùng gradient nguồn) với Poisson dùng `--mixed-gradients`.

**Hiện tượng đổi màu cá (bạc → xanh đen):** xảy ra **giống hệt nhau**
ở cả 2 phiên bản — mixed-gradients **không khắc phục** được vấn đề
lệch tông màu. Đúng với lý thuyết: mixed gradients chỉ chọn gradient
lớn hơn theo từng cạnh (nguồn vs nền), không ràng buộc giá trị tuyệt
đối/DC component của nghiệm — nên không giải quyết được hiện tượng
"đổi màu theo điều kiện biên" đã thấy ở test case 3 và 4.

**Khác biệt quan sát được:** tập trung ở vùng **vây lưng** của cá —
nơi vây mỏng/gần như trong suốt trong ảnh nguồn nên gradient nguồn tại
đó yếu. Với mixed-gradients, thuật toán "hút" texture bong bóng nước
từ nền vào vùng này (vì gradient nền > gradient nguồn tại đó), tạo ra
các đốm sáng lạ chồng lên vây — không có ở bản non-mixed. Khoảng
8.969/12.139 pixel trong mask có giá trị khác nhau giữa 2 phiên bản
(900 pixel lệch rõ rệt, chênh lệch >20/255 theo thang tổng 3 kênh màu).

**Đánh giá:** trong trường hợp cụ thể này, mixed-gradients tạo ra
**artifact gây hại** (đốm bong bóng chồng lên vây) chứ không cải thiện
chất lượng — khác với use-case lý tưởng của mixed gradients (ghép vật
trong suốt/có lỗ một cách có chủ đích, nơi việc để lộ texture nền là
mong muốn). Ở đây hiệu ứng "lộ texture nền" xảy ra ngoài ý muốn tại
vùng vây mỏng, làm giảm chất lượng thị giác so với non-mixed.

**Kết luận:** Mixed Gradients không nên dùng mặc định cho mọi trường
hợp — chỉ phù hợp khi vùng ghép có chủ đích cần giữ lại/lộ texture nền
(vật trong suốt, có lỗ thủng); với vật thể có texture yếu cục bộ (như
vây cá) nhưng không có chủ đích lộ nền, mixed-gradients có thể gây
artifact ngoài ý muốn.

## 4. Số liệu định lượng

**Đo trên test case 4 (ảnh thật, cá/nước), offset (300,100), ảnh
640×436, mask 12.139 pixel = 12.139 biến số cho mỗi kênh màu (R,G,B),
trung bình 5 lần chạy liên tiếp:**

| Phương pháp | Min (ms) | Trung bình (ms) |
|---|---|---|
| Naive copy-paste | 6.8 | 8.5 |
| Poisson blend (non-mixed) | 91.2 | 107.9 |
| Poisson blend (mixed-gradients) | 110.8 | 112.9 |

**Nhận xét:** Poisson chậm hơn naive khoảng **12–13 lần** ở test case
này (do phải dựng + factorize ma trận thưa `A` rồi giải hệ 3 lần, một
lần mỗi kênh màu). Mixed-gradients và non-mixed có thời gian chạy
**tương đương nhau** trong giới hạn sai số đo đạc (chênh lệch ~5ms
trên nền ~100ms) — hợp lý vì cả hai dùng chung bước factorize `A` tốn
kém nhất, chỉ khác nhau ở cách tính vế phải `b`.

| Hạng mục | Giá trị |
|---|---|
| Kích thước ảnh nền — `edgecase`/`challenging` | 400×600 px |
| Kích thước ảnh nền — test case 4 (cá/nước) | 640×436 px |
| Số pixel mask — tight (edgecase) | 21.323 px |
| Số pixel mask — loose (edgecase) | 32.441 px |
| Số pixel mask — challenging | 21.323 px |
| Số pixel mask — cá (test case 4) | 12.139 px |
| Số biến hệ phương trình | = số pixel mask tương ứng (giải riêng mỗi kênh R/G/B) |
| Metric chất lượng ảnh (PSNR/SSIM...) | **Chưa thực hiện** — không có script tính các chỉ số này cho GDE |

## 5. Đánh giá tổng thể

- **Poisson hoạt động tốt nhất:** test case 1 (`edgecase` tight mask)
  — nền nguồn/đích lệch tông rất nhẹ, mask ôm sát → Poisson vừa xoá
  seam vừa gần như giữ nguyên màu sắc gốc.
- **Poisson gặp hạn chế rõ nhất:** test case 3 (`challenging`, synthetic)
  và đặc biệt test case 4 (ảnh thật, cá/nước) — chênh lệch tông nền quá
  lớn khiến đối tượng đổi màu hoàn toàn dù hình dạng/texture được giữ
  nguyên. Mixed-gradients **không giải quyết được** vấn đề này (mục 3).
- **Ảnh hưởng của mask:** mask loose tạo seam naive lớn và rõ hơn mask
  tight; ở ảnh thật, mask không khớp hoàn hảo với chi tiết mảnh (vây
  cá) để lại viền trắng sót ở kết quả naive.
- **Ảnh hưởng của chênh lệch màu sắc:** là yếu tố quyết định chất
  lượng kết quả Poisson mạnh nhất trong toàn bộ thực nghiệm.
- **Trade-off chất lượng vs thời gian:** Poisson chậm hơn naive ~12–13
  lần (đo thực tế tại test case 4) để đổi lấy việc loại bỏ hoàn toàn
  seam cứng — nhưng đổi màu đối tượng là cái giá phải trả khi 2 ảnh
  lệch tông mạnh, và mixed-gradients không khắc phục được đánh đổi này
  mà chỉ thêm ~0–5ms chi phí tương đương, đồng thời có thể gây thêm
  artifact cục bộ ở vùng texture yếu nếu dùng không đúng chỗ.

## 6. Danh sách hình ảnh đầu ra

### Test case 1 & 2 — `results/gradient_domain/edgecase/`
- 4-panel: `compare_tight.png`, `compare_loose.png`
- Naive riêng: `compare_tight_naive.png`, `compare_loose_naive.png`
- Poisson riêng: `compare_tight_poisson.png`, `compare_loose_poisson.png`
- Input: `data/gradient_domain/edgecase/background.png`, `source.png`,
  `mask.png` (tight), `mask_loose.png` (loose)

### Test case 3 — `results/gradient_domain/edgecase/challenging/`
- 4-panel: `compare_challenging.png`
- Naive riêng: `compare_challenging_naive.png`
- Poisson riêng: `compare_challenging_poisson.png`
- Input: `data/gradient_domain/edgecase/challenging/background.png`,
  `source.png`, `mask.png`

### Test case 4 — ảnh thật, offset (300,100)
- 4-panel (non-mixed): `results/gradient_domain/real_compare.png`
  (tương đương `results/gradient_domain/mixed_test/compare_nonmixed.png`)
- Naive riêng: `real_compare_naive.png`
- Poisson riêng (non-mixed): `real_compare_poisson.png`
- Input: `data/gradient_domain/raw/fish.jpg` (source),
  `data/gradient_domain/raw/water.jpg` (background),
  `data/gradient_domain/mask/fish.png` (mask)

### Mixed Gradients (bổ sung) — `results/gradient_domain/mixed_test/`
- `compare_nonmixed.png` / `compare_nonmixed_naive.png` /
  `compare_nonmixed_poisson.png` — Poisson mặc định tại offset (300,100)
- `compare_mixed.png` / `compare_mixed_naive.png` /
  `compare_mixed_poisson.png` — Poisson với `--mixed-gradients`
- `diff_heatmap.png` — bản đồ nhiệt chênh lệch pixel giữa 2 phiên bản
- `crop_compare.png` — crop vùng cá, so sánh non-mixed | mixed | heatmap
- `dorsal_zoom2.png` — phóng to vùng vây lưng, thấy rõ artifact bong
  bóng của mixed-gradients

### Không dùng trong phân tích chi tiết (offset nông hơn, cùng loại ảnh)
- `results/gradient_domain/test1/` — offset (200,100)
- `results/gradient_domain/test2/` — offset (150,100)
- `results/gradient_domain/test3/` — offset (100,100)
