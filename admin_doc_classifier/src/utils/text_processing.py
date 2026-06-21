import numpy as np
from PIL import Image
from src.core.ocr_engine import ocr_engine

def process_ocr_results(gray_img, paddle_result):
    """
    Hàm này nhận ảnh xám và kết quả detect của PaddleOCR, 
    cắt từng khung ảnh đưa vào VietOCR và ghép dòng.
    (Giữ nguyên 100% logic từ run_test.py cũ của bạn)
    """
    results = []
    
    if paddle_result is None or len(paddle_result) == 0:
        return ""

    for line in paddle_result:
        for word in line:
            box = word[0]
            # Tính bounding box
            x_min = int(min([pt[0] for pt in box]))
            x_max = int(max([pt[0] for pt in box]))
            y_min = int(min([pt[1] for pt in box]))
            y_max = int(max([pt[1] for pt in box]))

            # Mở rộng bounding box một chút để tránh cắt phạm chữ
            pad = 2
            x_min = max(0, x_min - pad)
            y_min = max(0, y_min - pad)
            x_max = min(gray_img.shape[1], x_max + pad)
            y_max = min(gray_img.shape[0], y_max + pad)

            if x_max <= x_min or y_max <= y_min:
                continue

            # Cắt ảnh theo box và nhận diện bằng VietOCR
            cropped_img = gray_img[y_min:y_max, x_min:x_max]
            pil_img = Image.fromarray(cropped_img)
            text = ocr_engine.vietocr.predict(pil_img)

            results.append({
                "text": text,
                "x": x_min,
                "y": y_min,
                "w": x_max - x_min,
                "h": y_max - y_min
            })

    # Thuật toán ghép dòng (Logic cũ của bạn)
    groups = {}
    for item in results:
        group_key = item["y"] // 15
        if group_key not in groups:
            groups[group_key] = []
        groups[group_key].append(item)

    final_lines = []
    for key in sorted(groups.keys()):
        line_items = sorted(groups[key], key=lambda i: i["x"])
        line_text = " ".join([i["text"] for i in line_items])
        final_lines.append(line_text)

    return "\n".join(final_lines)