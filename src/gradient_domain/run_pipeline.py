import argparse
import os
import time

import cv2
import numpy as np

from .io_utils import read_image_float, read_mask_float, write_image_float, binarize_mask
from .naive_blend import naive_paste
from .poisson_blend import poisson_blend


def _label(img_uint8, text):
    out = img_uint8.copy()
    cv2.rectangle(out, (0, 0), (out.shape[1], 24), (0, 0, 0), -1)
    cv2.putText(out, text, (6, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--background", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--mask", required=True)
    parser.add_argument("--offset", type=int, nargs=2, default=[0, 0], metavar=("OY", "OX"),
                         help="Offset (OY, OX) to paste source into background")
    parser.add_argument("--out", required=True)
    parser.add_argument("--mixed-gradients", action="store_true",
                         help="Use mixed gradients in Poisson blending (default: use source gradients only)")
    args = parser.parse_args()

    background = read_image_float(args.background)
    source = read_image_float(args.source)
    mask = binarize_mask(read_mask_float(args.mask))
    oy, ox = args.offset

    t0 = time.perf_counter()
    naive_result = naive_paste(background, source, mask, (oy, ox))
    t_naive = time.perf_counter() - t0

    t0 = time.perf_counter()
    poisson_result = poisson_blend(background, source, mask, (oy, ox), mixed_gradients=args.mixed_gradients)
    t_poisson = time.perf_counter() - t0

    print(f"Naive paste:     {t_naive * 1000:.1f} ms")
    print(f"Poisson blend:   {t_poisson * 1000:.1f} ms")

    bg_u8 = np.clip(background * 255, 0, 255).astype(np.uint8)
    src_u8 = np.clip(source * 255, 0, 255).astype(np.uint8)
    naive_u8 = np.clip(naive_result * 255, 0, 255).astype(np.uint8)
    poisson_u8 = np.clip(poisson_result * 255, 0, 255).astype(np.uint8)

    h, w = bg_u8.shape[:2]
    src_show = cv2.resize(src_u8, (w, h)) if src_u8.shape[:2] != (h, w) else src_u8
    panels = [
        _label(bg_u8, "Background"),
        _label(src_show, "Source"),
        _label(naive_u8, "Naive copy-paste"),
        _label(poisson_u8, "Poisson blend"),
    ]
    comparison = np.vstack([np.hstack(panels[:2]), np.hstack(panels[2:])])

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    cv2.imwrite(args.out, comparison)

    base, ext = os.path.splitext(args.out)
    write_image_float(f"{base}_naive{ext}", naive_result)
    write_image_float(f"{base}_poisson{ext}", poisson_result)
    print(f"Saved results: {args.out}")
    print(f"Saved individual results: {base}_naive{ext}, {base}_poisson{ext}")


if __name__ == "__main__":
    main()
