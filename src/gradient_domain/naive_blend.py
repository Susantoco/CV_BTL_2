import numpy as np


def naive_paste(background, source, mask, offset):
    oy, ox = offset
    h, w = mask.shape[:2]
    if oy < 0 or ox < 0 or oy + h > background.shape[0] or ox + w > background.shape[1]:
        raise ValueError("Offset and mask size exceed background dimensions.")

    result = background.copy()
    region = result[oy:oy + h, ox:ox + w]
    mask_bool = mask.astype(bool)
    region[mask_bool] = source[mask_bool]
    result[oy:oy + h, ox:ox + w] = region
    return result
