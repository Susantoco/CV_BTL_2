# Mục 3.2 — Phần I: Gradient Domain Editing (hiện thực chi tiết)

> **Bản nháp (Part 1).** Mục 2.1/2.2 đã trình bày lý thuyết (phương trình
> Poisson, rời rạc hóa, mixed gradients) — mục này tập trung vào **cách lý
> thuyết đó được chuyển thành code** trong `src/gradient_domain/`. Người phụ
> trách đọc lại, đối chiếu với code thật, diễn đạt lại theo văn phong riêng
> trước khi đưa vào báo cáo (xem lưu ý học thuật trong `docs/HD-BTL-CV.pdf`).

## Tổng quan pipeline

```
mask_tool.py ──► mask.png ─┐
                            │
generate_synthetic.py ──► bộ ảnh test (background/source/mask) ─┤
                            │                                     ▼
data/gradient_domain/raw/ ─┴──────────────────────────►  run_pipeline.py (CLI)
                                                              │
                                                    ┌─────────┴─────────┐
                                                    ▼                   ▼
                                             naive_blend.py       poisson_blend.py
                                           (baseline so sánh)      (thuật toán chính)
                                                    │                   │
                                                    └─────────┬─────────┘
                                                              ▼
                                                   io_utils.py (đọc/ghi ảnh)
                                                              │
                                                              ▼
                                            results/gradient_domain/*.png
                                            (ảnh so sánh 4 panel + 2 ảnh riêng lẻ)
```

6 file trong `src/gradient_domain/` chia làm 3 nhóm vai trò:

| Nhóm | File | Vai trò |
|---|---|---|
| Tiện ích I/O | `io_utils.py` | Đọc/ghi ảnh, chuẩn hóa định dạng số |
| Chuẩn bị dữ liệu | `mask_tool.py`, `generate_synthetic.py` | Tạo input (mask thủ công / ảnh test tổng hợp) |
| Thuật toán + CLI | `naive_blend.py`, `poisson_blend.py`, `run_pipeline.py` | Lõi xử lý và điểm vào chạy thử nghiệm |

## `io_utils.py` — chuẩn hóa định dạng ảnh

Toàn bộ thuật toán trong module này làm việc trên ảnh **float64, giá trị
trong `[0, 1]`** (không phải `uint8 [0, 255]` như OpenCV đọc mặc định), vì hệ
phương trình tuyến tính ở bước Poisson cần số thực chính xác cao, không làm
tròn — bốn hàm ở đây là lớp chuyển đổi 2 chiều duy nhất giữa định dạng ảnh
trên đĩa và định dạng dùng nội bộ:

- `read_image_float` / `read_mask_float`: đọc bằng `cv2.imread`, chia `255.0`.
- `write_image_float`: nhân lại `255`, `clip` về `[0, 255]`, ép `uint8` trước
  khi ghi — bước `clip` cần thiết vì nghiệm Poisson có thể vượt nhẹ ra ngoài
  `[0, 1]` tại vài pixel biên.
- `binarize_mask(mask_float, threshold=0.5)`: mask đọc từ PNG grayscale có
  thể có giá trị trung gian (do nén/anti-aliasing ở biên) — hàm này ép về
  đúng 2 giá trị `{0, 1}` trước khi đưa vào `poisson_blend`, tránh trường hợp
  một pixel biên bị tính nửa trong nửa ngoài vùng Ω.

## `naive_blend.py` — baseline copy-paste

```python
region[mask_bool] = source[mask_bool]
```

Chỉ 1 dòng logic: thay trực tiếp pixel trong vùng mask bằng pixel nguồn
tương ứng, không xử lý biên. Dùng làm đối chứng để minh họa **tại sao cần
Poisson blending** (mục 2.1, phần "Vì sao copy-paste trực tiếp không đủ") —
không có giá trị thuật toán, nhưng là phép so sánh định tính bắt buộc trong
báo cáo (mục 4.1, 5.1).

## `poisson_blend.py` — thuật toán lõi

Đây là phần hiện thực trực tiếp công thức rời rạc ở mục 2.2. File gồm 3 hàm,
ứng với 3 giai đoạn: **dựng ma trận hệ số A** → **dựng vế phải b cho từng
kênh màu** → **giải hệ và ghép kết quả**.

### 1. `_build_system` — dựng ma trận thưa `A`

Vì chỉ các pixel *bên trong mask* mới là ẩn số của hệ phương trình, bước đầu
tiên là đánh số (id) cho từng pixel trong mask để ánh xạ từ tọa độ `(y, x)`
sang chỉ số hàng/cột của ma trận thưa:

```python
mask_p = np.pad(mask_center, 1, mode="constant", constant_values=False)
ids_p = -np.ones_like(mask_p, dtype=np.int64)
ids_p[mask_p] = np.arange(mask_p.sum())
```

Việc `pad` thêm viền 1 pixel (giá trị `False`) quanh mask giải quyết gọn vấn
đề "pixel ở biên mask thì 1 trong 4 hàng-xóm có thể nằm ngoài mảng" — sau khi
pad, mọi pixel trong mask luôn truy cập được cả 4 hàng-xóm bằng slicing đơn
giản (`neighbor_slices`), không cần `if` kiểm tra biên mảng.

Với mỗi pixel `p` trong mask, dòng tương ứng của `A` có hệ số `4` trên đường
chéo (từ số hạng `4f(p)` trong công thức Laplacian rời rạc) và `-1` tại cột
ứng với mỗi hàng-xóm `q` **cũng nằm trong mask**:

```python
for key in neighbor_slices:              # up / down / left / right
    sel = mask_center & mask_dirs[key]    # hàng-xóm hướng `key` cũng trong mask
    rows.append(ids_center[sel]); cols.append(ids_dirs[key][sel])
    data.append(np.full(..., -1.0))
```

Hàng-xóm *ngoài* mask không tạo thêm cột (chúng là hằng số biết trước, không
phải ẩn số) — đóng góp của chúng được chuyển sang vế phải `b` ở bước sau. Ma
trận được dựng dạng `coo_matrix` (dễ cộng dồn theo index) rồi chuyển sang
`csc_matrix` để `splu` factorize hiệu quả.

**Điểm quan trọng: `A` không phụ thuộc giá trị màu, chỉ phụ thuộc hình dạng
mask** → chỉ cần dựng và factorize (`scipy.sparse.linalg.splu`) **một lần**,
dùng lại cho cả 3 kênh RGB ở bước giải — đây là tối ưu hiệu năng chính của
toàn bộ module, được gọi 1 lần trong `poisson_blend()` thay vì lặp lại trong
vòng lặp kênh màu.

### 2. `_channel_rhs` — dựng vế phải `b` cho 1 kênh màu

Với mỗi pixel trong mask, vế phải là tổng chênh lệch gradient nguồn tới 4
hàng-xóm, cộng thêm giá trị nền tại các hàng-xóm nằm ngoài mask (điều kiện
biên Dirichlet):

```python
grad_term = source_center - source_dir        # ∇S theo 1 hướng
boundary_term = np.where(mask_dirs[key], 0.0, target_dir)  # chỉ cộng nếu hàng-xóm ngoài mask
b_full += grad_term + boundary_term
```

**Mixed gradients** (tùy chọn, cờ `--mixed-gradients`) được cài trực tiếp
trong vòng lặp này: tại mỗi cạnh, so sánh độ lớn `|∇S|` và `|∇T|`, giữ
gradient nào lớn hơn —

```python
if mixed_gradients:
    target_grad = target_center - target_dir
    use_target = np.abs(target_grad) > np.abs(grad_term)
    grad_term = np.where(use_target, target_grad, grad_term)
```

Cuối cùng chỉ trả về `b_full[mask_center]` — vector 1 chiều độ dài bằng số
ẩn số, đúng thứ tự id đã đánh ở bước 1 (vì `mask_center` dùng để index đúng
là mask gốc, cùng cách duyệt với lúc gán `ids_p[mask_p] = np.arange(...)`).

### 3. `poisson_blend` — điều phối chung

```python
A, mask_dirs, neighbor_slices = _build_system(mask_center)
lu = splu(A)                                   # factorize 1 lần
for c in range(background.shape[2]):           # lặp 3 kênh B, G, R
    b = _channel_rhs(source[...,c], target_patch[...,c], ...)
    f = lu.solve(b)                            # giải hệ, tái dùng LU
    result_patch[...,c][mask_center] = np.clip(f, 0.0, 1.0)
```

Hàm còn đảm nhiệm validate input (kích thước mask phải khớp source; offset +
mask không được vượt khung background) và xử lý edge case mask rỗng (trả về
nguyên background, không giải hệ gì). Kết quả được ghép lại vào đúng vị trí
`[oy:oy+h, ox:ox+w]` trên một bản copy của `background`, giữ nguyên phần ảnh
nền ngoài vùng dán.

## `mask_tool.py` — công cụ tạo mask thủ công

Vì đề bài không yêu cầu segmentation tự động (mục 2.1, "Giả định/phạm vi"),
mask phải được vẽ tay. File cung cấp 2 chế độ, dùng `cv2.setMouseCallback` để
bắt sự kiện chuột trên một cửa sổ OpenCV:

- **`PolygonMaskTool`**: click trái thêm điểm, click phải xóa điểm cuối,
  phím `c` đóng đa giác (`cv2.fillPoly`) và tô mask. Phù hợp với vật thể có
  biên rõ ràng, dễ khoanh bằng vài điểm (ví dụ các bộ test trong đề bài).
- **`BrushMaskTool`**: giữ chuột trái để "vẽ" mask bằng cọ tròn
  (`brush_size` chỉnh được), phù hợp vùng biên không đều/phức tạp hơn.

Cả 2 class đều expose cùng 1 API tối giản (`.run()` trả về mask `uint8` hoặc
`None` nếu thoát không lưu), CLI (`main()`) chỉ chọn class theo `--mode` rồi
ghi mask ra PNG bằng `cv2.imwrite` — không qua `io_utils.py` vì mask ở đây
được tạo trực tiếp dạng `uint8 {0,255}`, không cần biểu diễn float.

## `generate_synthetic.py` — sinh bộ ảnh test có kiểm soát

Vì ảnh thật (`raw/fish.jpg`, `raw/water.jpg`) không đủ để minh họa các
trường hợp biên (mục 2.1, "Hạn chế lý thuyết quan trọng"), file này dựng
bằng tay 3 bộ ảnh tổng hợp dưới `data/gradient_domain/edgecase/`, mỗi bộ
nhắm vào đúng 1 hiện tượng cần phân tích:

- **Vật thể luôn có texture nội tại**: `make_source_and_masks` vẽ một
  "mặt trời" có gradient màu từ tâm ra rìa (`core_color` → `rim_color` theo
  `rim_t`), cộng thêm nhiễu Gaussian và một dao động sin theo bán kính
  (`6 * sin(...)`) — **cố ý tránh vùng màu đặc phẳng**, vì mục 2.1 đã chỉ ra
  vùng flat-fill sẽ "bốc hơi" dưới Poisson blending (chỉ ràng buộc gradient,
  không ràng buộc giá trị tuyệt đối).
- **Mask tight vs. loose**: `tight_mask` bám sát hình dạng vật thể
  (`cv2.dilate` thêm vài pixel đệm); `loose_mask` là một hình tròn lớn hơn
  nhiều so với vật thể — dùng để minh họa ảnh hưởng của kích thước mask (mục
  2.1, hạn chế #2 và mục 5.3).
- **Bộ `challenging/`**: nền nguồn và nền đích được sinh với tông màu gần bù
  nhau (cam/vàng vs. xanh dương, `_linear_gradient_bg` với seed khác nhau) —
  minh họa hạn chế #3 (đổi màu vật thể khi 2 nền lệch tông mạnh).

Mỗi lần chạy `python -m src.gradient_domain.generate_synthetic` tái sinh lại
toàn bộ 3 bộ ảnh một cách xác định (các `np.random.default_rng(seed)` cố
định seed) — đảm bảo kết quả thực nghiệm trong báo cáo có thể tái lập.

## `run_pipeline.py` — CLI điều phối, điểm vào thực nghiệm

Không chứa logic thuật toán, chỉ điều phối theo đúng vai trò của 1 CLI:

1. Đọc `--background/--source/--mask/--offset` qua `io_utils`, nhị phân hóa
   mask bằng `binarize_mask`.
2. Chạy `naive_paste` và `poisson_blend` trên cùng input, đo thời gian chạy
   từng cách bằng `time.perf_counter()` (số liệu định lượng cho mục 4.1).
3. Dựng 1 ảnh ghép 4 panel (`Background | Source` / `Naive | Poisson`, có
   nhãn chữ đè lên từng ảnh qua hàm `_label`) để so sánh trực quan trong 1
   hình duy nhất — thuận tiện chèn thẳng vào báo cáo mà không cần ghép ảnh
   thủ công.
4. Ghi ra 3 file: ảnh so sánh 4-panel + 2 ảnh kết quả riêng lẻ
   (`*_naive.ext`, `*_poisson.ext`) để có thể phóng to xem chi tiết từng ảnh
   khi cần.

Cờ `--mixed-gradients` được truyền thẳng xuống `poisson_blend(...,
mixed_gradients=True)`, không có logic riêng ở tầng CLI.

## Liên kết với các mục khác trong báo cáo

- Công thức toán + lý do thiết kế thuật toán: đã trình bày ở **mục 2.1/2.2**,
  không lặp lại ở đây — mục này chỉ giải thích *cách hiện thực*.
- Kiến trúc tổng thể (vị trí module này trong toàn hệ thống): **mục 3.1**.
- Ảnh kết quả cụ thể từ 3 bộ test: **mục 4.1**.
- Phân tích ưu/nhược điểm, nguyên nhân sai lệch: **mục 5.1/5.3/5.4** (dựa
  trên 3 hạn chế đã nêu ở mục 2.1, được minh họa bằng dữ liệu sinh từ
  `generate_synthetic.py` ở trên).
