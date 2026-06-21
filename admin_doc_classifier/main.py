import sys
import os
import cv2
import time
import numpy as np
import re
import difflib
from PIL import Image


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

# Import các core modules
from src.core.preprocess_image import preprocess_image_pro
from src.utils.image_io import imread, load_image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from information_extraction import info_extractor
from src.core.nlp_engine import phobert_engine  # Tích hợp PhoBERT Classifier

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
        if re.match(r'^\d{1,2}[gh:]\d{2}$', word.lower()):
            return False
        # KHÔNG sửa email hoặc website (chứa @ hoặc .vn, .com)
        if '@' in word or '.vn' in word.lower() or '.com' in word.lower():
            return False
        # KHÔNG sửa các từ trông như ngày tháng (định dạng: dd/mm/yyyy hoặc d/m/yyyy)
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{4}$', word):
            return False
        # KHÔNG sửa các số hoặc năm (ví dụ: "2011", "2015") hoặc mã số (ví dụ: "061/2005/QH11")
        if re.match(r'^\d{4}$', word):
            return False
        # KHÔNG sửa các mã số/quyết định (ví dụ: "61/2005/QH11", "16/2003/QH11")
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
                            pred_token = p['token_str'].replace('_', ' ').replace('@@', '').strip()
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
# LUỒNG CHẠY CHÍNH TỐI ƯU HÓA (BATCH INFERENCE + NLP)
# =================================================================
if __name__ == "__main__":
    start_time = time.time()
    
    # 📌 Thay đổi đường dẫn file test tại đây
    TEST_FILE_PATH = os.path.join(ROOT_DIR, "data", "raw", "thu_moi", "20251222131023_0045.jpg")
    print(f"\n[{TEST_FILE_PATH}] Đang nạp dữ liệu...")
    
    pages = load_image(TEST_FILE_PATH)
    if not pages:
        print("⚠️ Không có trang ảnh nào để xử lý. Dừng chương trình.")
        sys.exit()

    full_document_text = ""

    for page_num, img in enumerate(pages, 1):
        print(f"\n🔍 ĐANG XỬ LÝ TRANG SỐ {page_num}/{len(pages)}")
        page_start = time.time()
        
        # 1. Tiền xử lý ảnh
        t1 = time.time()
        processed_img = preprocess_image_pro(img)
        print(f"   ⏱ Tiền xử lý: {time.time()-t1:.2f}s")
        gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
        
        # 2. Tìm khung chữ (Text Detection)
        t2 = time.time()
        result = det_model.ocr(processed_img, rec=False)
        print(f"   ⏱ Text Detection: {time.time()-t2:.2f}s")
        boxes = result[0] if result and result[0] else []
        if not boxes: continue

        # 3. Chống lật ngược ảnh
        is_vertical = sum(1 for box in boxes if max(np.linalg.norm(np.array(box)[0] - np.array(box)[3]), np.linalg.norm(np.array(box)[1] - np.array(box)[2])) > max(np.linalg.norm(np.array(box)[0] - np.array(box)[1]), np.linalg.norm(np.array(box)[2] - np.array(box)[3])) * 1.2)
        if is_vertical > len(boxes) * 0.5:
            processed_img = cv2.rotate(processed_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
            gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
            result = det_model.ocr(processed_img, rec=False)
            boxes = result[0] if result and result[0] else []

        # 4. Tính toán dung sai dòng (Dung sai động dựa trên chiều cao thực tế)
        box_heights = []
        for b in boxes:
            pts = np.array(b, dtype=np.float32)
            h = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
            box_heights.append(h)
        
        median_h = np.median(box_heights) if box_heights else 20
        tolerance = int(median_h * 0.6)
        if tolerance < 5: tolerance = 5
        
        # Sắp xếp thô các khung
        boxes = sorted(boxes, key=lambda b: (int(np.mean([p[1] for p in b]) // tolerance), int(np.mean([p[0] for p in b]))))

        # 5. Cắt ảnh và chuẩn bị Batch (Không giới hạn width quá gắt)
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
            
            # Nâng max width để chữ không bị méo
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

        # 6. Dự đoán hàng loạt bằng VietOCR (Batch Predict)
        results_with_pos = []
        if list_pil_imgs:
            try:
                t_ocr = time.time()
                batch_texts = rec_model.predict_batch(list_pil_imgs)
                print(f"   ⏱ VietOCR Batch ({len(list_pil_imgs)} ảnh): {time.time()-t_ocr:.2f}s") 
            except AttributeError:
                t_ocr = time.time()
                batch_texts = [rec_model.predict(img) for img in list_pil_imgs]
                print(f"   ⏱ VietOCR Sequential ({len(list_pil_imgs)} ảnh): {time.time()-t_ocr:.2f}s")
            except Exception as e:
                print(f"⚠️ Lỗi Batch Predict: {e}. Đang chuyển về tuần tự...")
                t_ocr = time.time()
                batch_texts = [rec_model.predict(img) for img in list_pil_imgs]
                print(f"   ⏱ VietOCR Sequential ({len(list_pil_imgs)} ảnh): {time.time()-t_ocr:.2f}s")

            for info, text in zip(valid_boxes_info, batch_texts):
                if text.strip():
                    results_with_pos.append({
                        "text": text,
                        "y": info["y"],
                        "x": info["x"],
                        "h": info["h"]
                    })

        # 7. Sắp xếp lại lần cuối và ghép văn bản
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
        print(f"✅ Trang {page_num} xong trong {time.time()-page_start:.2f}s")

    # =================================================================
    # BƯỚC SỬA LỖI & NLP INFERENCE
    # =================================================================
    print("\n" + "="*70)
    print("🔧 BƯỚC: SỬA LỖI OCR BẰNG REGEX & PHOBERT MASK")
    print("="*70)
    
    t_fix = time.time()
    corrected_text = ocr_corrector.correct_text(full_document_text)
    print(f"⏱ Tổng thời gian sửa lỗi: {time.time()-t_fix:.2f}s")
    print(ocr_corrector.get_corrections_summary())
    
    print("\n" + "="*70)
    print("📝 VĂN BẢN TRÍCH XUẤT (SAU SỬA LỖI OCR):")
    print("="*70)
    print(corrected_text.strip())
    
    print("\n" + "="*70)
    print("📋 TRÍCH XUẤT THÔNG TIN TÀI LIỆU (NLP CLASSIFICATION)")
    print("="*70)
    
    # Trích xuất Regex cơ bản
    extracted_info = info_extractor.extract_all_info(corrected_text)
    
    # --- TÍCH HỢP PHOBERT OVERRIDE CHỖ NÀY ---
    # Lấy văn bản OCR đã được sửa lỗi đưa vào mô hình phân loại để lấy nhãn
    phobert_result = phobert_engine.predict(corrected_text)
    extracted_info['loai_van_ban'] = f"{phobert_result['label']} (Tự tin: {phobert_result['confidence']}%)"
    # -----------------------------------------
    
    print(f"📅 Ngày tháng năm      : {extracted_info.get('ngay_thang_nam', 'Không xác định')}")
    print(f"📄 Loại văn bản        : {extracted_info.get('loai_van_ban', 'Không xác định')}")
    print(f"🔢 Số hiệu             : {extracted_info.get('so_hieu', 'Không xác định')}")
    print(f"🏙️ Nơi ban hành        : {extracted_info.get('thanh_pho', 'Không xác định')}")
    print(f"📌 Trích yếu           : {extracted_info.get('trich_yeu', 'Không xác định')}")
    print("\n📖 Nội dung (tóm tắt):")
    print(extracted_info.get('noi_dung', 'Nội dung không rõ'))

    print("="*70)
    print(f"⏱ Tổng thời gian chạy (Xử lý ảnh + OCR + NLP): {time.time() - start_time:.2f} giây")