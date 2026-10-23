import cv2

def get_detector(name):
    """
    Hàm tạo detector và matcher tương ứng.
    Chỉ dùng SIFT và ORB (bỏ qua SURF do vấn đề bản quyền OpenCV).
    """
    name = name.lower()
    
    if name == 'sift':
        detector = cv2.SIFT_create()
        # SIFT dùng L2 norm
        matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        return detector, matcher
        
    elif name == 'orb':
        # Tăng nfeatures lên 2000 để bắt đủ điểm ghép Panorama
        detector = cv2.ORB_create(nfeatures=2000)
        # ORB trả về binary descriptor nên BẮT BUỘC dùng NORM_HAMMING
        matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        return detector, matcher
        
    elif name == 'surf':
        raise NotImplementedError(
            "SURF không khả dụng trên opencv-python tiêu chuẩn do bản quyền. "
            "Chỉ sử dụng SIFT và ORB theo yêu cầu."
        )
    else:
        raise ValueError(f"Không hỗ trợ detector: {name}")