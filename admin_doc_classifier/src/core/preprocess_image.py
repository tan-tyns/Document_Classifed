import cv2
import numpy as np

# ================================================================
# BƯỚC 0: KIỂM TRA CHẤT LƯỢNG ẢNH ĐẦU VÀO
# ================================================================
def check_image_quality(gray: np.ndarray) -> dict:
    """
    Đánh giá ảnh trước khi xử lý để chọn chiến lược phù hợp.
    - variance of Laplacian < 100: ảnh mờ → cần sharpen mạnh hơn
    - std < 30: ảnh thiếu tương phản → cần CLAHE mạnh hơn
    """
    blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    brightness = gray.mean()
    return {
        "is_blurry": blur_score < 100,
        "is_low_contrast": contrast < 30,
        "is_dark": brightness < 80,
        "blur_score": blur_score,
    }

# ================================================================
# BƯỚC 1: CHUẨN HÓA KÍCH THƯỚC
# ================================================================
def normalize_size(img: np.ndarray, target_height: int = 2000) -> np.ndarray:
    """
    Resize ảnh về chiều cao chuẩn, giữ tỷ lệ.
    PaddleOCR hoạt động tốt nhất ở 1500–2500px chiều cao.
    """
    h, w = img.shape[:2]
    if h < target_height:
        scale = target_height / h
        img = cv2.resize(img, (int(w * scale), target_height),
                         interpolation=cv2.INTER_CUBIC)  # CUBIC tốt hơn LINEAR khi phóng to
    return img

# ================================================================
# BƯỚC 2: KHỬ BÓNG ĐỔ (shadow removal)
# ================================================================
def remove_shadow(gray: np.ndarray) -> np.ndarray:
    """
    Loại bỏ bóng đổ bằng cách chia ảnh gốc cho background ước lượng.
    Đặc biệt hiệu quả với ảnh chụp điện thoại bị bóng tay/ánh sáng không đều.
    """
    # Dilate để "xóa" chữ, chỉ còn background
    dilated = cv2.dilate(gray, np.ones((21, 21), np.uint8))
    # Blur mạnh để làm mịn background
    bg = cv2.GaussianBlur(dilated, (21, 21), 0)
    # Chia để normalize ánh sáng
    result = cv2.divide(gray, bg, scale=255)
    return result

# ================================================================
# BƯỚC 3: KHỬ NHIỄU
# ================================================================
def denoise(gray: np.ndarray, is_blurry: bool) -> np.ndarray:
    """
    - Ảnh đã mờ: dùng bilateral (giữ cạnh, không làm mờ thêm)
    - Ảnh sắc nét: dùng fastNlMeans (mạnh hơn, loại nhiễu scan/fax)
    """
    if is_blurry:
        return cv2.bilateralFilter(gray, d=5, sigmaColor=50, sigmaSpace=50)
    else:
        return cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

# ================================================================
# BƯỚC 4: TĂNG TƯƠNG PHẢN (CLAHE thích nghi)
# ================================================================
def enhance_contrast(gray: np.ndarray, is_low_contrast: bool) -> np.ndarray:
    """
    clipLimit cao hơn khi ảnh thiếu sáng/tương phản kém.
    tileGridSize nhỏ hơn → local contrast tốt hơn cho văn bản nhỏ.
    """
    clip = 3.0 if is_low_contrast else 2.0
    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(8, 8))
    return clahe.apply(gray)

# ================================================================
# BƯỚC 5: LÀM SẮC NÉT (unsharp masking)
# ================================================================
def sharpen(gray: np.ndarray) -> np.ndarray:
    """
    Unsharp masking: cộng thêm phần "detail" đã trừ khỏi blur.
    Kết quả rõ nét hơn nhiều so với kernel sharpen cứng.
    """
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=2)
    sharpened = cv2.addWeighted(gray, 1.5, blurred, -0.5, 0)
    return sharpened

# ================================================================
# BƯỚC 6: PHÁT HIỆN VÀ CHỈNH GÓC NGHIÊNG (deskew)
# ================================================================
def deskew(gray: np.ndarray) -> np.ndarray:
    """
    Dùng HoughLinesP để detect góc nghiêng của văn bản rồi xoay lại.
    Bỏ qua nếu góc < 0.5° (không đáng kể) hoặc > 45° (detect sai).
    """
    # Threshold nhanh để HoughLines chạy trên binary
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    lines = cv2.HoughLinesP(binary, 1, np.pi / 180, threshold=100,
                             minLineLength=100, maxLineGap=10)
    if lines is None:
        return gray
    
    angles = []
    for line in lines:
        x1, y1, x2, y2 = line[0]
        if x2 - x1 != 0:
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
            # Chỉ lấy các đường gần nằm ngang (văn bản)
            if -45 < angle < 45:
                angles.append(angle)
    
    if not angles:
        return gray
    
    median_angle = np.median(angles)
    
    # Bỏ qua góc nghiêng quá nhỏ
    if abs(median_angle) < 0.5:
        return gray
    
    h, w = gray.shape
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
    rotated = cv2.warpAffine(gray, M, (w, h),
                              flags=cv2.INTER_LINEAR,
                              borderMode=cv2.BORDER_REPLICATE,
                              borderValue=255) # Fill viền màu trắng
    return rotated

# ================================================================
# BƯỚC 7: XÓA MỘC ĐỎ, CHỮ KÝ XANH VÀ WATERMARK
# ================================================================
def remove_stamps_and_watermarks(img: np.ndarray) -> np.ndarray:
    """
    Phát hiện và xóa các vùng có màu đỏ (con dấu), màu xanh (chữ ký bút bi), 
    cắt bỏ dòng "Scanned with CamScanner" ở đáy ảnh.
    """
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 1. Dải màu đỏ trong HSV (Đỏ có 2 dải ở đầu và cuối dải Hue)
    lower_red1 = np.array([0, 50, 50])
    upper_red1 = np.array([10, 255, 255])
    lower_red2 = np.array([160, 50, 50])
    upper_red2 = np.array([180, 255, 255])
    
    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    red_mask = mask1 + mask2

    # 2. Dải màu xanh dương (Blue) cho chữ ký bút bi
    lower_blue = np.array([90, 50, 50])
    upper_blue = np.array([130, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Gộp mask đỏ và xanh
    combined_mask = red_mask + blue_mask
    
    # Làm phình mask một chút để xóa sạch viền lem luốc của mực
    kernel = np.ones((3,3), np.uint8)
    combined_mask = cv2.dilate(combined_mask, kernel, iterations=1)
    
    # Thay thế các pixel màu bị bắt mask bằng màu trắng (255, 255, 255)
    result = img.copy()
    result[combined_mask > 0] = (255, 255, 255)
    
    # 3. Xử lý "Scanned with CamScanner" bằng cách cắt 3% chiều cao ở đáy ảnh
    h, w = result.shape[:2]
    crop_bottom_margin = int(h * 0.03) 
    result = result[0:(h - crop_bottom_margin), :]
    
    return result

# ================================================================
# PIPELINE TỔNG HỢP CHO OCR (MAIN FUNCTION)
# ================================================================
def preprocess_image_pro(img: np.ndarray) -> np.ndarray:
    """
    Luồng xử lý ảnh hoàn chỉnh trước khi đưa vào PaddleOCR và VietOCR
    """
    # 1. Xóa mộc đỏ, chữ ký xanh, watermark (Phải làm lúc ảnh còn màu BGR)
    img = remove_stamps_and_watermarks(img)

    # 2. Resize ảnh về kích thước chuẩn giúp OCR dễ đọc hơn
    img = normalize_size(img, target_height=1600)

    # 3. Chuyển sang ảnh xám
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. Deskew (Xoay ảnh thẳng lại nếu bị scan nghiêng)
    gray = deskew(gray)

    # 5. Kiểm tra chất lượng ảnh
    quality = check_image_quality(gray)

    # 6. Khử bóng đổ nếu ảnh chụp bị tối góc / chênh sáng
    if quality["is_low_contrast"]:
        gray = remove_shadow(gray)

    # 7. Denoise (Lọc nhiễu hạt)
    gray = denoise(gray, is_blurry=quality["is_blurry"])

    # 8. Tăng tương phản
    gray = enhance_contrast(gray, is_low_contrast=quality["is_low_contrast"])

    # 9. Sharpen (Làm sắc nét chữ)
    blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.5)
    gray = cv2.addWeighted(gray, 1.3, blurred, -0.3, 0)

    # 10. Padding (Tạo viền trắng xung quanh để OCR không bị lẹm viền)
    padded = cv2.copyMakeBorder(gray, 30, 30, 30, 30,
                                 cv2.BORDER_CONSTANT, value=255)

    # Trả về ảnh định dạng 3 kênh màu (BGR) vì PaddleOCR yêu cầu input có 3 kênh
    return cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR)