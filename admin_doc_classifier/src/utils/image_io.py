"""Helper đọc ảnh hỗ trợ đường dẫn Unicode (Windows).

Sử dụng Python I/O để đọc bytes rồi giải mã bằng `cv2.imdecode`.
Tránh dùng `cv2.imread` trực tiếp vì OpenCV trên Windows có thể không
hỗ trợ đường dẫn chứa ký tự Unicode (ví dụ tiếng Việt có dấu).
"""
from typing import Optional, List
import os
import cv2
import numpy as np
from pdf2image import convert_from_path


def imread_unicode(path: str, flags: int = cv2.IMREAD_COLOR) -> Optional[np.ndarray]:
    """Read image from `path` supporting Unicode filenames on Windows.

    Returns OpenCV BGR image or `None` if reading/decoding fails.
    """
    try:
        with open(path, 'rb') as f:
            data = f.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, flags)
        return img
    except Exception:
        return None


def imread(path: str, flags: int = cv2.IMREAD_COLOR) -> Optional[np.ndarray]:
    """Alias ngắn gọn cho `imread_unicode`.
    Giữ tên `imread` để thay thế trực tiếp những chỗ đang gọi `cv2.imread`.
    """
    return imread_unicode(path, flags)


def load_image(file_path: str) -> List[np.ndarray]:
    """Load ảnh từ file (PDF hoặc ảnh thông thường).
    
    Args:
        file_path: Đường dẫn đến file PDF hoặc ảnh
        
    Returns:
        Danh sách các ảnh OpenCV BGR format
    """
    cv2_images = []
    
    if file_path.lower().endswith('.pdf'):
        # Load PDF bằng convert_from_path
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # project_root là lùi 2 bước (từ src/utils -> src -> root)
            project_root = os.path.dirname(os.path.dirname(current_dir))
            
            # Tạo 2 phương án đường dẫn để bao lô mọi trường hợp cấu trúc thư mục
            poppler_path_1 = os.path.join(project_root, "engine", "poppler", "Library", "bin")
            poppler_path_2 = os.path.join(os.path.dirname(project_root), "engine", "poppler", "Library", "bin")
            
            # Kiểm tra xem poppler thực sự nằm ở đâu
            if os.path.exists(poppler_path_1):
                poppler_path = poppler_path_1
            elif os.path.exists(poppler_path_2):
                poppler_path = poppler_path_2
            else:
                raise FileNotFoundError(f"Không tìm thấy thư mục Poppler ở:\n1. {poppler_path_1}\n2. {poppler_path_2}")
            
            print(f"📄 Đang dùng Poppler bung các trang PDF thành ảnh...")
            # Bỏ in đường dẫn chi tiết ra màn hình để tránh lỗi đè chữ của tqdm (progress bar)
            
            pil_images = convert_from_path(file_path, dpi=200, poppler_path=poppler_path)
            
            for pil_img in pil_images:
                # Convert PIL RGB image sang OpenCV BGR image
                img_array = np.array(pil_img)
                bgr_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                cv2_images.append(bgr_img)
                
        except Exception as e:
            print(f"\n❌ Lỗi đọc PDF: {e}")
            print(f"💡 Hãy đảm bảo:")
            print(f"   1. Poppler được cài đặt đúng chỗ.")
            print(f"   2. File PDF tồn tại: {file_path}")
    else:
        # Load ảnh thông thường
        img = imread(file_path)
        if img is not None:
            cv2_images.append(img)
        else:
            print(f"\n❌ Lỗi đọc ảnh từ: {file_path}")
    
    return cv2_images


__all__ = ["imread_unicode", "imread", "load_image"]
