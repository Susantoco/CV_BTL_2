# Mục 2.2 — Cơ sở lý thuyết (Gradient Domain Editing)

> Phạm vi: chỉ trình bày đúng những gì được hiện thực trong
> `src/gradient_domain/` (`poisson_blend.py`, `naive_blend.py`,
> `run_pipeline.py`, `io_utils.py`). Không trình bày các biến thể Poisson
> editing không có trong code (seamless cloning mix nhiều nguồn, local
> illumination/color change, v.v.).

## Mô hình bài toán và pipeline xử lý

**Input:**
- Ảnh nền `T` (target/background) và ảnh nguồn `S` (source), đọc bằng
  `io_utils.read_image_float` — chuẩn hóa về `float64`, miền giá trị `[0,1]`,
  3 kênh màu (BGR).
- Mask nhị phân `M` cùng kích thước `H×W` với `S`, xác định vùng Ω cần ghép
  (vẽ tay bằng `mask_tool.py`, đọc bằng `read_mask_float` rồi nhị phân hóa ở
  ngưỡng 0.5 — `binarize_mask`).
- Offset `(oy, ox)`: tọa độ góc trên-trái đặt patch `(S, M)` vào `T`.

**Pipeline xử lý** (`run_pipeline.py`):

```
đọc T, S, M  →  nhị phân hóa M
      │
      ├─► naive_paste(T, S, M, offset)        — baseline so sánh
      │
      └─► poisson_blend(T, S, M, offset)      — thuật toán chính
               │
               ├─ build_system(M): dựng ma trận hệ số A (1 lần,
               │    dùng chung cho cả 3 kênh màu)
               ├─ với mỗi kênh c ∈ {B, G, R}:
               │     dựng vế phải b từ gradient(S) + điều kiện biên(T)
               │     giải A f = b  (scipy.sparse.linalg.splu)
               │     gán f vào vùng Ω của kênh c
               └─ ghép patch đã giải vào đúng vị trí offset trong T
      │
      └─► ghép panel so sánh (background/source/naive/poisson), xuất ảnh
```

**Output:** ảnh nền đã ghép đối tượng, biên vùng Ω không còn bước nhảy màu
đột ngột (seam), trong khi vẫn giữ texture nội bộ của đối tượng.

## Vì sao không ghép trực tiếp (naive copy-paste)?

`naive_paste` chỉ thay thế giá trị pixel: `result[M] = S[M]`. Mắt người nhạy
với *sự gián đoạn của gradient* tại biên hơn là chênh lệch màu tuyệt đối, nên
nếu tông màu/độ sáng nền quanh đối tượng trong `S` khác với `T`, biên mask sẽ
lộ thành một đường cắt rõ rệt dù màu từng vùng riêng lẻ không sai.

## Nguyên lý Poisson Image Editing (công thức chính được hiện thực)

**Bài toán biến phân:** thay vì khớp giá trị màu tuyệt đối tại biên, tìm ảnh
kết quả `f` trong Ω sao cho gradient của `f` khớp gradient của nguồn `S`,
còn giá trị đúng tại biên ∂Ω khớp với nền `T` (điều kiện biên Dirichlet):

$$
\min_{f} \iint_{\Omega} |\nabla f - \nabla S|^2 \, dA
\quad \text{sao cho } f\big|_{\partial\Omega} = T\big|_{\partial\Omega}
$$

Theo phép tính biến phân (Euler–Lagrange), nghiệm cực tiểu thỏa phương trình
Poisson:

$$
\Delta f = \Delta S \ \text{trong } \Omega, \qquad f = T \ \text{trên } \partial\Omega
$$

**Rời rạc hóa (lưới pixel, 4 láng giềng):** với mỗi pixel `p ∈ Ω` và tập
láng giềng `N(p)` (trên/dưới/trái/phải), Laplacian rời rạc dẫn tới hệ
phương trình tuyến tính:

$$
4f(p) - \sum_{q \in N(p)\cap\Omega} f(q)
= \sum_{q \in N(p)} \big(S(p)-S(q)\big) + \sum_{q \in N(p)\setminus\Omega} T(q)
$$

Đây là hệ thưa `A f = b` với `A` **không phụ thuộc kênh màu** — hiện thực
trong `_build_system`: dựng `A` một lần, factorize bằng `scipy.sparse.linalg.
splu`, rồi tái dùng nghiệm LU để giải cho cả 3 kênh (R, G, B) độc lập, mỗi
kênh một vế phải `b` khác nhau (`_channel_rhs`). Ảnh được pad thêm 1 pixel
viền (`edge` cho ảnh, `constant` cho mask) để mọi pixel trong Ω luôn có đủ 4
láng giềng hợp lệ, tránh phải xử lý riêng trường hợp biên ảnh.

**Mixed gradients (tùy chọn, cờ `--mixed-gradients`):** tại mỗi cạnh
`(p,q)`, thay vì luôn lấy gradient của nguồn, chọn gradient có trị tuyệt đối
lớn hơn giữa nguồn và nền:

$$
\nabla f^{*}(p,q) =
\begin{cases}
\nabla S(p,q) & \text{nếu } |\nabla S(p,q)| > |\nabla T(p,q)| \\
\nabla T(p,q) & \text{ngược lại}
\end{cases}
$$

Hiện thực trong `_channel_rhs` bằng `np.where(use_target, target_grad,
grad_term)`, dùng khi vùng ghép có texture yếu hơn nền xung quanh (ví dụ vật
thể có lỗ/trong suốt).

## Giới hạn của công thức (hệ quả trực tiếp từ việc chỉ ràng buộc gradient)

1. Phương trình chỉ ràng buộc *gradient*, không ràng buộc màu tuyệt đối →
   vùng màu đặc (gradient = 0) sẽ suy biến thành nội suy điều hòa giữa các
   giá trị biên, tức đối tượng phẳng màu sẽ "bốc hơi" nếu không có texture
   nội bộ.
2. Điều kiện biên Dirichlet lấy từ `T` tại ∂Ω → nếu tông màu nền quanh đối
   tượng trong `S` lệch nhiều so với `T`, nghiệm sẽ kéo cả vùng Ω về tông màu
   của `T` (đặc tính, không phải lỗi, của phương pháp).
