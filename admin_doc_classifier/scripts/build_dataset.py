import sys
import os
import cv2
import time
import numpy as np
import re
import difflib
import json
import glob
from PIL import Image
from pdf2image import convert_from_path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

POPPLER_PATH = os.path.join(ROOT_DIR, "engine", "poppler", "Library", "bin")

# Import các core modules
from app.core.preprocess_image import preprocess_image_pro
from app.utils.image_io import imread 
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from information_extraction import info_extractor
from app.core.nlp_engine import phobert_engine  # Tích hợp PhoBERT Classifier

# =================================================================
# KHỞI TẠO CÁC MÔ HÌNH AI (CHẠY 1 LẦN)
# =================================================================
print("🚀 Đang tải mô hình PaddleOCR (Tìm khung chữ)...", flush=True)
det_model = PaddleOCR(use_angle_cls=True, lang="vi", use_gpu=False, show_log=False)

print("🚀 Đang tải mô hình VietOCR (Đọc tiếng Việt có dấu)...", flush=True)
config = Cfg.load_config_from_name('vgg_seq2seq')
config['device'] = 'cpu'
config['predictor']['beamsearch'] = False
rec_model = Predictor(config)

print("⏳ Đang khởi động lõi AI dịch chữ...")
dummy_img = Image.new('RGB', (100, 32), color=(255, 255, 255))
try:
    _ = rec_model.predict(dummy_img)
except Exception as e:
    print(f"⚠️ LỖI KHỞI TẠO VIETOCR: {e}")

# =================================================================
# KHỞI TẠO PHOBERT OCR CORRECTOR
# =================================================================
class OCRCorrector:
    """Sửa lỗi OCR sử dụng Regex kết hợp với PhoBERT (Masked Language Model)"""
    
    def __init__(self):
        self.common_errors = {
            # ==================== LỖI CƠ BẢN ĐÃ CÓ ====================
            r'\bthang\b': 'tháng', r'\bthả[ng]\b': 'tháng', r'\bthạ[ng]\b': 'tháng',
            r'\bChinh\s+phu\b': 'Chính phủ', r'\bchinh\s+phu\b': 'chính phủ',
            r'\bViêt\s+Nam\b': 'Việt Nam', r'\bThê\s+Giới\b': 'Thế Giới',
            r'\bhương\s+dẫn\b': 'hướng dẫn', r'\bhanh\b': 'hành',
            r'\bquvet\b': 'quyết', r'\bquyet\s+dinh\b': 'quyết định',
            r'\bđâu\s+tu\b': 'đầu tư', r'\bđâu\s+tư\b': 'đầu tư',
            r'\bquán\s+lý\b': 'quản lý', r'\bquân\s+lý\b': 'quản lý',
            r'\bgiá[ys]\s+m[oọ]i\b': 'giấy mời', r'\bkính\s+mời\b': 'kính mời',
            r'\bcông\s+v[ặa]n\b': 'công văn', r'\bthong\s+bao\b': 'thông báo',
            r'\bto\s+trinh\b': 'tờ trình', r'\bke\s+hoach\b': 'kế hoạch',
            
            # ==================== LỖI BỔ SUNG ====================
            r'\bđị\s+lịm\b': 'đi làm', r'\bđi\s+lịm\b': 'đi làm', r'\bđị\s+làm\b': 'đi làm',
            r'\bChiên\s+thăng\b': 'Chiến thắng', r'\bchiên\s+thăng\b': 'chiến thắng',
            r'\bnghi\s+lễ\b': 'nghỉ lễ', r'\bnghi\s+lê\b': 'nghỉ lễ', r'\bnghĩ\s+lễ\b': 'nghỉ lễ',
            r'\bhoán\s+đối\b': 'hoán đổi', r'\bhợp\s+thuy\s+lý\b': 'hợp lý',
            r'\btố\s+chức\b': 'tổ chức', r'\bnghi,\b': 'nghỉ,',
        }
        self.corrections_made = []
        print("🚀 Đang tải PhoBERT Fill-Mask Model để sửa chính tả nâng cao...")
        try:
            from transformers import pipeline
            self.fill_mask = pipeline("fill-mask", model="vinai/phobert-base", device=-1)
            print("✅ PhoBERT Mask Load thành công.")
        except Exception as e:
            print(f"⚠️ Không tải được PhoBERT Mask: {e}. Sẽ chỉ dùng Regex.")
            self.fill_mask = None

    def correct_text(self, text):
        self.corrections_made = []
        corrected = self._apply_regex_fixes(text)
        if self.fill_mask:
            corrected = self._apply_phobert_fixes(corrected)
        return corrected
        
    def _apply_regex_fixes(self, text):
        corrected = text
        for pattern, replacement in self.common_errors.items():
            matches = re.finditer(pattern, corrected, flags=re.IGNORECASE)
            for match in matches:
                self.corrections_made.append({
                    'original': match.group(0), 'corrected': replacement, 'method': 'Regex'
                })
            corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
        
        def fix_in_date(match):
            result = match.group(0)
            result = re.sub(r'[lL]', '1', result)
            result = re.sub(r'[Oo]', '0', result)
            return result
        corrected = re.sub(r'(?:ngày|tháng|năm)\s+[\dloO]+', fix_in_date, corrected, flags=re.IGNORECASE)
        corrected = re.sub(r'(ngày\s+)(\d{1,2})[1lI]([1-9]|1[0-2])\b', r'\g<1>\g<2>/\g<3>', corrected, flags=re.IGNORECASE)
        return corrected

    def _is_suspicious_word(self, word):
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{4}$', word):
            return False
        if re.match(r'^\d{4}$', word):
            return False
        if re.match(r'^\d+(/\d+)+', word):
            return False
        
        if re.search(r'\d', word) and re.search(r'[a-zA-Z]', word): return True
        if re.search(r'[^\w\s]', word, re.UNICODE): return True
        if len(word) == 1 and not word.isdigit() and word.lower() not in ['a', 'o', 'e', 'u', 'i', 'y', 'à', 'á', 'ả', 'ã', 'ạ', 'ơ', 'ở', 'ô', 'ổ', 'ố', 'ỳ', 'ý']:
            return True
        return False

    def _apply_phobert_fixes(self, text):
        lines = text.split('\n')
        fixed_lines = []
        for line in lines:
            if not line.strip():
                fixed_lines.append(line)
                continue
            words = line.split()
            for i, word in enumerate(words):
                clean_word = word.strip(".,;:!()[]{}")
                if len(clean_word) > 1 and self._is_suspicious_word(clean_word):
                    masked_words = words.copy()
                    masked_words[i] = masked_words[i].replace(clean_word, "<mask>")
                    start, end = max(0, i - 15), min(len(masked_words), i + 15)
                    masked_sentence = " ".join(masked_words[start:end])
                    try:
                        preds = self.fill_mask(masked_sentence, top_k=3)
                        best_match = clean_word
                        highest_similarity = 0.0
                        for p in preds:
                            pred_token = p['token_str'].replace('_', ' ').strip()
                            similarity = difflib.SequenceMatcher(None, clean_word.lower(), pred_token.lower()).ratio()
                            if similarity > highest_similarity:
                                highest_similarity = similarity
                                best_match = pred_token
                        if highest_similarity > 0.4:
                            words[i] = words[i].replace(clean_word, best_match)
                            self.corrections_made.append({
                                "original": clean_word, "corrected": best_match, "method": f"PhoBERT (Sim: {highest_similarity:.2f})"
                            })
                    except Exception:
                        pass 
            fixed_lines.append(" ".join(words))
        return "\n".join(fixed_lines)

    def get_corrections_summary(self):
        if not self.corrections_made: return "✅ Không phát hiện lỗi OCR cần sửa"
        summary = f"📊 Tổng cộng {len(self.corrections_made)} lỗi đã sửa:\n"
        groups = {}
        for corr in self.corrections_made:
            key = f"[{corr['method']}] {corr['original']} → {corr['corrected']}"
            groups[key] = groups.get(key, 0) + 1
        for pattern, count in list(groups.items())[:15]: summary += f"   • {pattern} ({count}x)\n"
        if len(groups) > 15: summary += f"   ... và {len(groups) - 15} lỗi khác"
        return summary

ocr_corrector = OCRCorrector()

# =================================================================
# HÀM PHỤ TRỢ ĐỌC PDF/ẢNH
# =================================================================
def load_images_from_file(file_path):
    cv2_images = []
    if file_path.lower().endswith('.pdf'):
        print(f"📄 Đang dùng Poppler bung các trang PDF thành ảnh...")
        try:
            pil_images = convert_from_path(file_path, dpi=200, poppler_path=POPPLER_PATH)
            for pil_img in pil_images: cv2_images.append(cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR))
        except Exception as e:
            print(f"❌ Lỗi đọc PDF: {e}")
    else:
        img = imread(file_path)
        if img is not None: cv2_images.append(img)
    return cv2_images

# =================================================================
# LUỒNG CHẠY CHÍNH TỐI ƯU HÓA (BATCH INFERENCE + DATASET GENERATION)
# =================================================================
if __name__ == "__main__":
    start_time_total = time.time()
    
    # 📌 Cấu hình thư mục đầu vào và đầu ra
    INPUT_DIR = os.path.join(ROOT_DIR, "data", "raw")
    OUTPUT_JSON_PATH = os.path.join(ROOT_DIR, "data", "extracted_dataset.json")
    
    # Quét tất cả các file ảnh/pdf trong thư mục raw (kể cả thư mục con)
    valid_extensions = ('*.jpg', '*.jpeg', '*.png', '*.pdf')
    file_list = []
    for ext in valid_extensions:
        file_list.extend(glob.glob(os.path.join(INPUT_DIR, "**", ext), recursive=True))
    
    print(f"📁 Đã tìm thấy {len(file_list)} file cần xử lý trong {INPUT_DIR}")
    
    # Khởi tạo list chứa dữ liệu cho dataset
    dataset = []

    for idx, file_path in enumerate(file_list, 1):
        print("\n" + "="*80)
        print(f"🚀 [{idx}/{len(file_list)}] ĐANG XỬ LÝ: {file_path}")
        print("="*80)
        
        file_start = time.time()
        
        try:
            pages = load_images_from_file(file_path)
            if not pages:
                print(f"⚠️ Không đọc được nội dung từ {file_path}. Bỏ qua.")
                continue

            full_document_text = ""

            for page_num, img in enumerate(pages, 1):
                # 1. Tiền xử lý ảnh
                processed_img = preprocess_image_pro(img)
                gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
                
                # 2. Tìm khung chữ (Text Detection)
                result = det_model.ocr(processed_img, rec=False)
                boxes = result[0] if result and result[0] else []
                if not boxes: continue

                # 3. Chống lật ngược ảnh
                is_vertical = sum(1 for box in boxes if max(np.linalg.norm(np.array(box)[0] - np.array(box)[3]), np.linalg.norm(np.array(box)[1] - np.array(box)[2])) > max(np.linalg.norm(np.array(box)[0] - np.array(box)[1]), np.linalg.norm(np.array(box)[2] - np.array(box)[3])) * 1.2)
                if is_vertical > len(boxes) * 0.5:
                    processed_img = cv2.rotate(processed_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
                    result = det_model.ocr(processed_img, rec=False)
                    boxes = result[0] if result and result[0] else []

                # 4. Tính toán dung sai dòng
                box_heights = []
                for b in boxes:
                    pts = np.array(b, dtype=np.float32)
                    h = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
                    box_heights.append(h)
                
                median_h = np.median(box_heights) if box_heights else 20
                tolerance = int(median_h * 0.6)
                if tolerance < 5: tolerance = 5
                
                boxes = sorted(boxes, key=lambda b: (int(np.mean([p[1] for p in b]) // tolerance), int(np.mean([p[0] for p in b]))))

                # 5. Cắt ảnh và chuẩn bị Batch
                list_pil_imgs = []
                valid_boxes_info = []

                for box in boxes:
                    pts = np.array(box, dtype=np.float32).reshape(4, 2)
                    width = int(max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3])))
                    height = int(max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))
                    
                    if width <= 0 or height <= 0: continue
                        
                    dst_pts = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]], dtype="float32")
                    M = cv2.getPerspectiveTransform(pts, dst_pts)
                    crop = cv2.warpPerspective(gray_processed, M, (width, height))
                    
                    if height > width * 1.2: 
                        crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                    margin_y, margin_x = 4, 8 
                    crop_padded = cv2.copyMakeBorder(crop, margin_y, margin_y, margin_x, margin_x, cv2.BORDER_CONSTANT, value=255)
                    
                    scale = 32 / crop_padded.shape[0]
                    new_w = max(1, min(int(crop_padded.shape[1] * scale), 1500)) 
                    crop_resized = cv2.resize(crop_padded, (new_w, 32), interpolation=cv2.INTER_CUBIC)
                    
                    pil_img = Image.fromarray(cv2.cvtColor(crop_resized, cv2.COLOR_GRAY2RGB))
                    
                    list_pil_imgs.append(pil_img)
                    valid_boxes_info.append({
                        "y": np.mean([p[1] for p in box]),
                        "x": np.mean([p[0] for p in box]),
                        "h": height
                    })

                # 6. Dự đoán hàng loạt bằng VietOCR
                results_with_pos = []
                if list_pil_imgs:
                    try:
                        batch_texts = rec_model.predict_batch(list_pil_imgs)
                    except Exception:
                        batch_texts = [rec_model.predict(img) for img in list_pil_imgs]

                    for info, text in zip(valid_boxes_info, batch_texts):
                        if text.strip():
                            results_with_pos.append({
                                "text": text,
                                "y": info["y"],
                                "x": info["x"],
                                "h": info["h"]
                            })

                # 7. Sắp xếp và ghép văn bản
                results_with_pos.sort(key=lambda item: (int(item["y"] // tolerance), item["x"]))
                
                page_text = ""
                prev_y = -100
                prev_h = 0
                
                for item in results_with_pos:
                    if prev_y == -100: 
                        page_text += item["text"]
                    else:
                        if (item["y"] - prev_y) < (prev_h * 1.5): 
                            page_text += " " + item["text"]
                        else: 
                            page_text += "\n" + item["text"]
                    prev_y = item["y"]
                    prev_h = item["h"]

                full_document_text += page_text + "\n\n"

            # ---- NLP & TRÍCH XUẤT THÔNG TIN ----
            corrected_text = ocr_corrector.correct_text(full_document_text)
            extracted_info = info_extractor.extract_all_info(corrected_text)
            
            phobert_result = phobert_engine.predict(corrected_text)
            extracted_info['loai_van_ban'] = f"{phobert_result['label']}"
            extracted_info['do_tu_tin_phan_loai'] = phobert_result['confidence']
            
            # Lưu dữ liệu của file này vào cấu trúc dataset
            data_record = {
                "file_name": os.path.basename(file_path),
                "file_path": file_path,
                "raw_text": full_document_text.strip(),
                "corrected_text": corrected_text.strip(),
                "extracted_info": extracted_info,
                "processing_time_seconds": round(time.time() - file_start, 2)
            }
            dataset.append(data_record)
            
            print(f"✅ Xử lý thành công trong {data_record['processing_time_seconds']}s")

        except Exception as e:
            print(f"❌ LỖI NGHIÊM TRỌNG KHI XỬ LÝ FILE {file_path}: {e}")
            continue

    # =================================================================
    # LƯU KẾT QUẢ DATASET RA FILE JSON
    # =================================================================
    print("\n" + "="*80)
    print(f"💾 ĐANG LƯU DATASET VÀO: {OUTPUT_JSON_PATH}")
    
    # Tạo thư mục chứa file json nếu chưa tồn tại
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=4)
        
    print(f"🎉 HOÀN THÀNH! Đã tạo dataset với {len(dataset)} bản ghi.")
    print(f"⏱ Tổng thời gian chạy: {time.time() - start_time_total:.2f} giây")