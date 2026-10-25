"""
Registry cac detector dac trung dung cho pipeline stitching (pipeline.py).

Moi detector phai cung cap cung mot interface:
    keypoints, descriptors = detector.detect_and_compute(gray_image)
    detector.norm_type -> cv2.NORM_L2 (SIFT/SURF) hoac cv2.NORM_HAMMING (ORB)

Them detector moi (vd AKAZE, BRISK): viet 1 class ke thua BaseDetector roi
dang ky vao DETECTOR_REGISTRY ben duoi. pipeline.py KHONG can sua gi - day la
noi DUY NHAT Phan 3 can dung toi de doi/them phuong phap trich xuat dac trung.
"""
from abc import ABC, abstractmethod

import cv2


class BaseDetector(ABC):
    name = "base"
    norm_type = cv2.NORM_L2

    @abstractmethod
    def detect_and_compute(self, gray):
        ...


class SIFTDetector(BaseDetector):
    name = "sift"
    norm_type = cv2.NORM_L2

    def __init__(self, n_features=0):
        self._impl = cv2.SIFT_create(nfeatures=n_features)

    def detect_and_compute(self, gray):
        return self._impl.detectAndCompute(gray, None)


class ORBDetector(BaseDetector):
    name = "orb"
    norm_type = cv2.NORM_HAMMING

    def __init__(self, n_features=4000):
        self._impl = cv2.ORB_create(nfeatures=n_features)

    def detect_and_compute(self, gray):
        return self._impl.detectAndCompute(gray, None)


class SURFDetector(BaseDetector):
    """
    CHU Y: can opencv-contrib-python ban "nonfree" (cv2.xfeatures2d). Build
    opencv-python chuan (da kiem tra trong moi truong chung cua repo nay)
    KHONG co module nay vi SURF con patent - goi detector nay se raise
    RuntimeError ro rang thay vi loi import mo ho. Xem ghi chu chi tiet trong
    README.md o muc goc repo.
    """
    name = "surf"
    norm_type = cv2.NORM_L2

    def __init__(self, hessian_threshold=400):
        if not hasattr(cv2, "xfeatures2d"):
            raise RuntimeError(
                "SURF can opencv-contrib-python (ban nonfree) - khong co san "
                "trong moi truong hien tai. Dung 'sift' hoac 'orb' thay the."
            )
        self._impl = cv2.xfeatures2d.SURF_create(hessian_threshold)

    def detect_and_compute(self, gray):
        return self._impl.detectAndCompute(gray, None)


DETECTOR_REGISTRY = {
    "sift": SIFTDetector,
    "orb": ORBDetector,
    "surf": SURFDetector,
}


def get_detector(name, **kwargs):
    key = name.lower()
    if key not in DETECTOR_REGISTRY:
        raise ValueError(f"Detector khong ho tro: '{name}'. Cac lua chon: {list(DETECTOR_REGISTRY)}")
    return DETECTOR_REGISTRY[key](**kwargs)
