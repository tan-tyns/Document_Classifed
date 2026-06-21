import sys
import os
import cv2
import time
import numpy as np
import re
import difflib
import shutil
import tempfile
from PIL import Image

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Thiết lập đường dẫn dự án giống main.py
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# Import các core modules của bạn
from src.core.preprocess_image import preprocess_image_pro
from src.utils.image_io import load_image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from information_extraction import info_extractor
from src.core.nlp_engine import phobert_engine

# =================================================================
# 1. KHỞI TẠO FASTAPI & CORS
# =================================================================
app = FastAPI(title="Classify Doc AI - API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Mở CORS cho Frontend React (cổng 5173)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =================================================================
# 2. KHỞI TẠO CÁC MÔ HÌNH AI (CHẠY 1 LẦN)
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
# 3. KHỞI TẠO PHOBERT OCR CORRECTOR
# =================================================================
class OCRCorrector:
    """Sửa lỗi OCR sử dụng Regex kết hợp với PhoBERT (Masked Language Model)"""
    
    def __init__(self):
        self.common_errors = {
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
        if re.match(r'^\d{1,2}[gh:]\d{2}$', word.lower()):
            return False
        if '@' in word or '.vn' in word.lower() or '.com' in word.lower():
            return False
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{4}$', word):
            return False
        if re.match(r'^\d{4}$', word):
            return False
        if re.match(r'^\d+(/\d+)+', word):
            return False
        if word.startswith('-') or word.endswith('-'):
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
                            pred_token = p['token_str'].replace('_', ' ').replace('@@', '').strip()
                            similarity = difflib.SequenceMatcher(None, clean_word.lower(), pred_token.lower()).ratio()
                            if similarity > highest_similarity:
                                highest_similarity = similarity
                                best_match = pred_token
                        if highest_similarity > 0.75:  # Nâng ngưỡng tự tin lên 0.75 theo chuẩn mới nhất
                            words[i] = words[i].replace(clean_word, best_match)
                            self.corrections_made.append({
                                "original": clean_word, "corrected": best_match, "method": f"PhoBERT (Sim: {highest_similarity:.2f})"
                            })
                    except Exception:
                        pass 
            fixed_lines.append(" ".join(words))
        return "\n".join(fixed_lines)

ocr_corrector = OCRCorrector()

# =================================================================
# 4. ROUTE XỬ LÝ CHÍNH
# =================================================================
@app.post("/process")
def process_document_api(file: UploadFile = File(...)):
    start_time = time.time()
    
    # 1. Lưu file xuống thư mục tạm
    temp_dir = tempfile.mkdtemp()
    temp_file_path = os.path.join(temp_dir, file.filename)
    
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"\n[{file.filename}] Đang nạp dữ liệu...")
        
        # 2. Sử dụng load_image (Tự động hỗ trợ PDF/Ảnh như main.py)
        pages = load_image(temp_file_path)
        if not pages:
            raise HTTPException(status_code=400, detail="Không có trang ảnh nào để xử lý.")

        full_document_text = ""

        # 3. LUỒNG XỬ LÝ ẢNH CHÍNH (Đồng bộ 100% với main.py)
        for page_num, img in enumerate(pages, 1):
            print(f"🔍 ĐANG XỬ LÝ TRANG SỐ {page_num}/{len(pages)}")
            # 3.1 Tiền xử lý
            processed_img = preprocess_image_pro(img)
            gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
            
            # 3.2 Nhận diện khung chữ (PaddleOCR)
            result = det_model.ocr(processed_img, rec=False)
            boxes = result[0] if result and result[0] else []
            if not boxes: continue

            # 3.3 Chống lật ngược ảnh
            is_vertical = sum(1 for box in boxes if max(np.linalg.norm(np.array(box)[0] - np.array(box)[3]), np.linalg.norm(np.array(box)[1] - np.array(box)[2])) > max(np.linalg.norm(np.array(box)[0] - np.array(box)[1]), np.linalg.norm(np.array(box)[2] - np.array(box)[3])) * 1.2)
            if is_vertical > len(boxes) * 0.5:
                processed_img = cv2.rotate(processed_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
                result = det_model.ocr(processed_img, rec=False)
                boxes = result[0] if result and result[0] else []

            # 3.4 Tính toán dung sai dòng
            box_heights = []
            for b in boxes:
                pts = np.array(b, dtype=np.float32)
                h = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
                box_heights.append(h)
            
            median_h = np.median(box_heights) if box_heights else 20
            tolerance = int(median_h * 0.6)
            if tolerance < 5: tolerance = 5
            
            # Sắp xếp thô
            boxes = sorted(boxes, key=lambda b: (int(np.mean([p[1] for p in b]) // tolerance), int(np.mean([p[0] for p in b]))))

            # 3.5 Cắt ảnh & Chuẩn bị Batch
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

            # 3.6 Dự đoán hàng loạt (VietOCR)
            results_with_pos = []
            if list_pil_imgs:
                try:
                    batch_texts = rec_model.predict_batch(list_pil_imgs)
                except AttributeError:
                    batch_texts = [rec_model.predict(img) for img in list_pil_imgs]
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

            # 3.7 Ghép văn bản
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

        # 4. SỬA LỖI & NLP INFERENCE
        corrected_text = ocr_corrector.correct_text(full_document_text)
        
        extracted_info = info_extractor.extract_all_info(corrected_text)
        phobert_result = phobert_engine.predict(corrected_text)
        
        doc_type = extracted_info.get('loai_van_ban', 'Không xác định')
        doc_date = extracted_info.get('ngay_thang_nam', 'Không xác định')
        label = phobert_result['label']
        confidence = phobert_result['confidence']

        print(f"⏱ Xử lý thành công trong {time.time() - start_time:.2f} giây")

        # 5. TRẢ KẾT QUẢ CHO REACT FRONTEND
        return {
            "text": full_document_text,
            "content": corrected_text,
            "label": label,
            "confidence": confidence,
            "docType": doc_type,
            "date": doc_date,
            "soHieu": extracted_info.get('so_hieu', ''),   
            "trichYeu": extracted_info.get('trich_yeu', ''),
            "noiBanHanh": extracted_info.get('thanh_pho', '')
        }

    except Exception as e:
        print(f"Lỗi: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        # Dọn dẹp thư mục tạm
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)