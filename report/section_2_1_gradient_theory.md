# Mục 2.1 — Gradient Domain Editing: bài toán & cơ sở lý thuyết

> Nguồn code tương ứng: `src/gradient_domain/`. Ảnh minh họa: `results/gradient_domain/`.

## Mô tả bài toán

**Input:**
- Ảnh nền `background` (target scene).
- Ảnh nguồn `source` chứa đối tượng cần ghép, cùng kích thước với `source`.
- Mask nhị phân xác định vùng đối tượng cần ghép từ `source` (vẽ bằng
  `src/gradient_domain/mask_tool.py`).
- Vị trí dán `offset = (oy, ox)` — tọa độ góc trên-trái của `source`/`mask`
  trong hệ tọa độ `background`.

**Output:** ảnh `background` đã được ghép đối tượng vào, sao cho đường biên
giữa đối tượng và nền mới **không lộ seam** (không có bước nhảy đột ngột về
màu sắc/độ sáng tại biên mask), trong khi texture/chi tiết nội bộ của đối
tượng vẫn được giữ lại.

**Giả định/phạm vi:** mask được cho trước (vẽ tay/bán tự động), không tự động
phân vùng đối tượng (không làm segmentation). Chỉ xét ghép 1 vùng duy nhất
mỗi lần gọi; muốn ghép nhiều vùng thì gọi lại nhiều lần.

## Vì sao copy-paste trực tiếp không đủ?

Ghép trực tiếp (`naive_blend.py`) chỉ đơn thuần thay thế pixel:

```
result[mask] = source[mask]
```

Nếu độ sáng/tông màu nền của `source` tại vùng lân cận mask khác với
`background`, biên mask sẽ lộ rõ như một đường cắt — vì mắt người rất nhạy với
*sự gián đoạn đột ngột của gradient* tại biên, dù sự khác biệt màu tuyệt đối
có thể không lớn.

## Nguyên lý Gradient Domain Editing (Poisson Image Editing)

Ý tưởng cốt lõi (Pérez, Gangnet, Blake — *Poisson Image Editing*, SIGGRAPH
2003): thay vì khớp **giá trị màu tuyệt đối** tại biên, ta khớp **gradient**
(đạo hàm không gian) của ảnh kết quả với gradient của ảnh nguồn trong vùng
Ω (mask), còn giá trị tại đúng biên ∂Ω thì khớp với ảnh nền (điều kiện biên
Dirichlet). Bài toán trở thành:

$$
\min_{f} \iint_{\Omega} |\nabla f - \nabla S|^2 \, dA
\quad \text{với } f|_{\partial\Omega} = T|_{\partial\Omega}
$$

trong đó `S` là ảnh nguồn, `T` là ảnh nền, `f` là ảnh kết quả cần tìm trong
Ω. Theo phép tính biến phân, nghiệm `f` thỏa mãn phương trình Poisson:

$$
\Delta f = \Delta S \quad \text{trong } \Omega, \qquad f = T \quad \text{trên } \partial\Omega
$$

### Rời rạc hóa

Với mỗi pixel `p ∈ Ω` và 4 pixel lân cận `N(p)` (trên/dưới/trái/phải),
Laplacian rời rạc cho hệ phương trình tuyến tính:

$$
4f(p) - \sum_{q \in N(p) \cap \Omega} f(q)
= \sum_{q \in N(p)} \big(S(p) - S(q)\big) + \sum_{q \in N(p) \setminus \Omega} T(q)
$$

Đây là một hệ **sparse linear system** `A f = b` (một biến `f(p)` cho mỗi
pixel trong mask), giải độc lập cho từng kênh màu (R, G, B). Hiện thực trong
`poisson_blend.py`:

- `A` (ma trận hệ số) **không phụ thuộc kênh màu** → chỉ cần factorize một
  lần (`scipy.sparse.linalg.splu`) rồi tái sử dụng cho cả 3 kênh — nhanh hơn
  nhiều so với giải lại từ đầu mỗi kênh.
- Để tránh phải xử lý riêng trường hợp pixel ở biên ảnh, mảng được pad thêm 1
  pixel viền (`np.pad(..., mode="edge")` cho ảnh, `mode="constant"` cho
  mask) — nhờ vậy mọi pixel trong mask luôn có đủ 4 neighbor hợp lệ.

### Mixed gradients (tùy chọn)

Khi vùng cần ghép có texture yếu hơn nền xung quanh (ví dụ ghép một vật thể
trong suốt/có lỗ), có thể dùng **mixed gradient**: tại mỗi cạnh, chọn gradient
có độ lớn lớn hơn giữa `source` và `target`:

$$
\nabla f^* (p,q) = \begin{cases} \nabla S(p,q) & |\nabla S(p,q)| > |\nabla T(p,q)| \\ \nabla T(p,q) & \text{ngược lại} \end{cases}
$$

Hiện thực bằng cờ `--mixed-gradients` trong `run_pipeline.py`
(`poisson_blend(..., mixed_gradients=True)`).

## Hạn chế lý thuyết quan trọng (rút ra khi thực nghiệm)

1. **Vùng màu đặc tuyệt đối (flat fill) sẽ không được giữ nguyên.** Vì
   phương trình chỉ ràng buộc *gradient* (= 0 với vùng flat), nghiệm trong
   vùng đó suy biến về nội suy điều hòa (harmonic interpolation) giữa các
   giá trị biên — tức object "bốc hơi" thành màu nền nếu nó không có texture
   nội bộ. → Khi tạo ảnh test tổng hợp, đối tượng ghép **bắt buộc phải có
   gradient/texture thật sự** (xem `generate_synthetic.py`), không vẽ bằng
   `cv2.circle(..., -1)` tô đặc màu.
2. **Mask càng ôm sát đối tượng, kết quả càng tự nhiên.** Nếu mask bao gồm
   nhiều vùng nền phẳng xung quanh đối tượng (không chỉ riêng đối tượng),
   điều kiện biên sẽ "kéo" cả những vùng phẳng đó theo giá trị nền đích, dễ để
   lại viền/halo quanh đối tượng dù không còn seam cứng. Xem so sánh
   `mask.png` (tight) và `mask_loose.png` trong
   `data/gradient_domain/sample/`.
3. **Chênh lệch tông màu nền giữa 2 ảnh càng lớn, đối tượng càng bị đổi màu
   theo ánh sáng đích.** Đây là đặc tính (không phải lỗi) của phương pháp —
   Poisson blending ưu tiên "ánh sáng tự nhiên" hơn "giữ đúng màu tuyệt đối".
   Xem bộ `data/gradient_domain/sample/challenging/` (nền cam vs nền xanh —
   gần như bù màu) để thấy rõ giới hạn này.
