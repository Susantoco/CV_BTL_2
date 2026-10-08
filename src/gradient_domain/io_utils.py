import cv2
import numpy as np


def read_image_float(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return img.astype(np.float64) / 255.0


def read_mask_float(path):
    m = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(f"Could not read mask: {path}")
    return m.astype(np.float64) / 255.0


def write_image_float(path, img_float):
    img_uint8 = np.clip(img_float * 255.0, 0, 255).astype(np.uint8)
    cv2.imwrite(path, img_uint8)


def binarize_mask(mask_float, threshold=0.5):
    return (mask_float >= threshold).astype(np.uint8)
