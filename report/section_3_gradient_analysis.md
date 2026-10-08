# Mục 3 (phần Gradient Domain Editing) — Phân tích & đánh giá

> TODO khi có ảnh thật: chạy lại `run_pipeline.py` trên ảnh ở
> `data/gradient_domain/real/`, thay số liệu/ảnh minh họa bên dưới bằng kết
> quả thật. Phần kết luận lý thuyết (dựa trên bộ ảnh tổng hợp) vẫn giữ
> nguyên giá trị vì phản ánh đúng bản chất toán học của phương pháp.

## So sánh naive copy-paste vs Poisson blending

Thực nghiệm trên bộ ảnh tổng hợp `data/gradient_domain/sample/` (mặt trời
texture đặt lên nền trời, nền `source` tối/lệch tông hơn `background`):

| Tiêu chí | Naive copy-paste | Poisson blending |
|---|---|---|
| Seam tại biên mask | Rõ rệt — hình chữ nhật/tròn bao quanh vật thể lộ hẳn do chênh lệch độ sáng nền | Biến mất — chuyển tiếp mượt, mắt thường khó nhận ra ranh giới |
| Giữ texture nội bộ vật thể | Giữ nguyên 100% (chỉ copy pixel) | Giữ được hình dạng/gradient nội bộ, nhưng tông màu tổng thể có thể dịch nhẹ theo ánh sáng nền đích |
| Thời gian chạy | ~3 ms (ảnh 400×600, mask ~15k px) | ~100 ms (phải giải hệ sparse linear system) |
| Độ phức tạp cài đặt | Rất đơn giản | Cần dựng & giải hệ phương trình tuyến tính thưa |

→ Poisson blending đánh đổi chi phí tính toán lớn hơn nhiều (và cần giải
LU factorization) để đổi lấy kết quả **liền mạch về ánh sáng/biên**, đúng mục
tiêu đề bài yêu cầu ("kết quả tự nhiên về mặt ánh sáng và biên").

## Ảnh hưởng của kích thước/độ ôm sát của mask

So sánh `mask.png` (ôm sát hình dạng vật thể, chỉ dilate ~2px) với
`mask_loose.png` (vòng tròn rộng hơn nhiều so với vật thể) trên **cùng** cặp
background/source:

- Với mask ôm sát: điều kiện biên chỉ tác động lên viền mỏng quanh vật thể →
  phần lớn vật thể giữ nguyên gradient nội bộ, chỉ vùng rìa được điều chỉnh
  nhẹ để khớp nền.
- Với mask rộng: vùng nền phẳng (gần như không gradient) nằm giữa vật thể và
  biên mask bị kéo theo nội suy điều hòa về phía giá trị nền đích, để lại một
  **vòng halo mờ** quanh vật thể — ảnh vẫn mượt hơn naive-paste nhưng không
  "sạch" bằng mask ôm sát.

**Kết luận:** chất lượng Poisson blending phụ thuộc trực tiếp vào chất lượng
mask — mask càng sát biên thật của đối tượng, kết quả càng tự nhiên. Đây là
điểm cần lưu ý khi vẽ mask bằng `mask_tool.py` trên ảnh thật.

## Trường hợp khó: chênh lệch tông màu nền lớn

Bộ ảnh `data/gradient_domain/sample/challenging/` dựng tình huống nền
`source` (cam/vàng) khác gần như bù màu với `background` (xanh). Kết quả
Poisson blend trong trường hợp này làm đối tượng đổi hẳn tông màu (từ cam/đỏ
sang tím/lục), dù hình dạng/gradient nội bộ (vành, tia nắng, vân tròn) vẫn
được giữ nguyên hoàn toàn — có thể kiểm chứng trực quan qua
`results/gradient_domain/compare_challenging.png`.

**Nguyên nhân:** vì phương trình Poisson chỉ ràng buộc gradient, "mức màu
tuyệt đối" (DC component) của nghiệm hoàn toàn do điều kiện biên quyết định.
Nếu giá trị biên (nền đích) cách xa giá trị gốc của vật thể tại đúng điểm
tiếp giáp, toàn bộ vùng sẽ dịch chuyển theo một lượng gần như hằng số bằng
đúng độ chênh lệch đó.

**Hạn chế rút ra:** Poisson/gradient-domain blending phù hợp nhất khi ảnh
nguồn và ảnh nền có **điều kiện ánh sáng/tông màu tương đồng** (cùng thời
điểm chụp, cùng môi trường); khi 2 ảnh có ánh sáng quá khác biệt, kỹ thuật
"mixed gradients" hoặc tiền xử lý cân bằng màu (color transfer) trước khi
blend sẽ cần thiết để tránh hiện tượng đổi màu không mong muốn.

## Ảnh hưởng của việc thiếu texture trong vùng mask

Thử nghiệm ban đầu (không giữ lại trong repo) dùng vật thể tô màu đặc tuyệt
đối (`cv2.circle(..., -1)` không gradient) cho thấy: vùng màu đặc bị thay thế
hoàn toàn bằng nội suy điều hòa giữa các giá trị biên, mất sạch màu gốc — vì
gradient = 0 khắp nơi trong vùng đó nên phương trình Poisson suy biến thành
phương trình Laplace thuần túy. Đây là lý do `generate_synthetic.py` cố tình
thêm gradient hướng tâm + nhiễu texture cho vật thể, mô phỏng đúng đặc điểm
của ảnh chụp thật (luôn có texture tự nhiên, hiếm khi màu đặc tuyệt đối).

## Tổng kết điểm mạnh / điểm yếu

**Điểm mạnh:** loại bỏ hoàn toàn seam cứng; không cần tiền xử lý màu phức
tạp; cài đặt một lần dùng được cho mọi cặp ảnh (chỉ cần đổi mask/offset).

**Điểm yếu:** (1) không giữ được vùng màu đặc hoàn toàn phẳng; (2) nhạy với
chất lượng/độ ôm sát của mask; (3) có thể làm đổi màu đối tượng khi ánh sáng
nền 2 ảnh quá khác biệt; (4) chi phí tính toán cao hơn hẳn copy-paste (phải
giải hệ phương trình thưa cho mỗi lần ghép).
