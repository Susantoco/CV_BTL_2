import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import splu


def _build_system(mask_center):
    h, w = mask_center.shape
    mask_p = np.pad(mask_center, 1, mode="constant", constant_values=False)
    ids_p = -np.ones_like(mask_p, dtype=np.int64)
    num_vars = int(mask_p.sum())
    ids_p[mask_p] = np.arange(num_vars)

    ids_center = ids_p[1:h + 1, 1:w + 1]
    neighbor_slices = {
        "up": (slice(0, h), slice(1, w + 1)),
        "down": (slice(2, h + 2), slice(1, w + 1)),
        "left": (slice(1, h + 1), slice(0, w)),
        "right": (slice(1, h + 1), slice(2, w + 2)),
    }
    mask_dirs = {k: mask_p[s] for k, s in neighbor_slices.items()}
    ids_dirs = {k: ids_p[s] for k, s in neighbor_slices.items()}

    rows = [np.arange(num_vars)]
    cols = [np.arange(num_vars)]
    data = [np.full(num_vars, 4.0)]
    for key in neighbor_slices:
        sel = mask_center & mask_dirs[key]
        r = ids_center[sel]
        c = ids_dirs[key][sel]
        rows.append(r)
        cols.append(c)
        data.append(np.full(r.shape[0], -1.0))

    A = sp.coo_matrix(
        (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
        shape=(num_vars, num_vars),
    ).tocsc()
    return A, mask_dirs, neighbor_slices


def _channel_rhs(source_c, target_c, mask_center, mask_dirs, neighbor_slices, mixed_gradients):
    h, w = mask_center.shape
    source_p = np.pad(source_c, 1, mode="edge")
    target_p = np.pad(target_c, 1, mode="edge")
    source_center = source_p[1:h + 1, 1:w + 1]
    target_center = target_p[1:h + 1, 1:w + 1]

    b_full = np.zeros((h, w), dtype=np.float64)
    for key, s in neighbor_slices.items():
        source_dir = source_p[s]
        target_dir = target_p[s]
        grad_term = source_center - source_dir
        if mixed_gradients:
            target_grad = target_center - target_dir
            use_target = np.abs(target_grad) > np.abs(grad_term)
            grad_term = np.where(use_target, target_grad, grad_term)
        boundary_term = np.where(mask_dirs[key], 0.0, target_dir)
        b_full += grad_term + boundary_term
    return b_full[mask_center]


def poisson_blend(background, source, mask, offset, mixed_gradients=False):
    oy, ox = offset
    h, w = mask.shape
    if h != source.shape[0] or w != source.shape[1]:
        raise ValueError("Mask and source dimensions do not match.")
    if oy < 0 or ox < 0 or oy + h > background.shape[0] or ox + w > background.shape[1]:
        raise ValueError("Offset and mask size exceed background dimensions.")

    mask_center = mask.astype(bool)
    if not mask_center.any():
        return background.copy()

    target_patch = background[oy:oy + h, ox:ox + w]

    A, mask_dirs, neighbor_slices = _build_system(mask_center)
    lu = splu(A)

    result_patch = target_patch.copy()
    for c in range(background.shape[2]):
        b = _channel_rhs(
            source[:, :, c], target_patch[:, :, c], mask_center,
            mask_dirs, neighbor_slices, mixed_gradients,
        )
        f = lu.solve(b)
        channel = result_patch[:, :, c]
        channel[mask_center] = np.clip(f, 0.0, 1.0)
        result_patch[:, :, c] = channel

    result = background.copy()
    result[oy:oy + h, ox:ox + w] = result_patch
    return result
