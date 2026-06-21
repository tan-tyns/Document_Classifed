#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 BƯỚC 4: TEST MODEL (ĐÃ SỬA ĐỂ MATCH VỚI 3_train_model.py MỚI)

Các fix so với phiên bản cũ:
  1. predict() dùng extract_smart_input() giống lúc train
     → tránh mismatch input format giữa train và inference
  2. Regex header tăng từ 300 → 800 chars (đồng bộ với HEADER_CHARS lúc train)
  3. Sửa thứ tự priority regex: keyword MẠNH (ít nhập nhằng) check TRƯỚC
     VD: "TỜ TRÌNH" trước "THÔNG BÁO" để tránh bắt nhầm
  4. Thêm /CV vào regex số hiệu cho Công văn
  5. test_directory xuất kết quả ra CSV để dễ phân tích
"""

import os
import sys
import json
import re
import argparse
import csv
from pathlib import Path
from collections import Counter

import cv2
import numpy as np
from PIL import Image
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.core.preprocess_image import preprocess_image_pro
from src.utils.image_io import load_image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg


# =====================================================================
# PHẢI ĐỒNG BỘ VỚI 3_train_model.py
# =====================================================================
HEADER_CHARS  = 800   # ← phải bằng HEADER_CHARS trong 3_train_model.py
SNIPPET_CHARS = 300   # ← phải bằng SNIPPET_CHARS trong 3_train_model.py


# =====================================================================
# TEXT PREPROCESSING (copy từ 3_train_model.py — KHÔNG thay đổi)
# =====================================================================

def clean_ocr_text(text: str) -> str:
    """Làm sạch nhiễu OCR — giống hệt hàm trong 3_train_model.py."""
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' ')
    text = re.sub(
        r'[^\w\s\.,;:!?()\-/\'\"'
        r'àáảãạăắặằẳẵâầấậẩẫèéẻẽẹêềếệểễìíỉĩịòóỏõọôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđ'
        r'ÀÁẢÃẠĂẮẶẰẲẴÂẦẤẬẨẪÈÉẺẼẸÊỀẾỆỂỄÌÍỈĨỊÒÓỎÕỌÔỒỐỘỔỖƠỜỚỢỞỠÙÚỦŨỤƯỪỨỰỬỮỲÝỶỸỴĐ]',
        ' ', text,
    )
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_smart_input(text: str) -> str:
    """
    Tạo input cho model — PHẢI GIỐNG HỆT hàm trong 3_train_model.py
    (augment=False vì đây là inference, không phải training).

    Format: "[HEADER] <800 chars đầu> [CONTENT] <300 chars tiếp theo>"
    """
    text   = clean_ocr_text(text)
    header  = text[:HEADER_CHARS]
    snippet = text[HEADER_CHARS: HEADER_CHARS + SNIPPET_CHARS]
    return f"[HEADER] {header} [CONTENT] {snippet}"


# =====================================================================
# REGEX RULE-BASED (HYBRID)
# Thứ tự priority: keyword ĐẶC TRƯNG nhất → ít nhập nhằng nhất → TRƯỚC
# =====================================================================

# (keyword, label) theo thứ tự ưu tiên
# Từ khoá ngắn dễ xuất hiện trong nội dung (THÔNG BÁO, BÁO CÁO) đặt SAU
HEADER_RULES = [
    ("QUYẾT ĐỊNH",  "Quyết định"),   # rất đặc trưng, ít nhầm
    ("TỜ TRÌNH",    "Tờ trình"),     # đặc trưng
    ("GIẤY MỜI",    "Giấy mời"),
    ("THƯ MỜI",     "Giấy mời"),
    ("KẾ HOẠCH",    "Kế hoạch"),
    ("BÁO CÁO",     "Báo cáo"),
    ("THÔNG BÁO",   "Thông báo"),    # đặt SAU vì dễ xuất hiện trong câu nội dung
    # Công văn không có tiêu đề lớn → nhận qua V/v hoặc số hiệu
]

# Ký hiệu số hiệu → loại văn bản
# Pattern: "Số: 123/TTR-..." hoặc "Số 45/QĐ-UBND"
# Thêm CV cho Công văn so với phiên bản cũ
CODE_RULES = [
    (r'/TTR\b',  "Tờ trình"),
    (r'/Q[ĐD]\b', "Quyết định"),
    (r'/KH\b',   "Kế hoạch"),
    (r'/BC\b',   "Báo cáo"),
    (r'/TB\b',   "Thông báo"),
    (r'/GM\b',   "Giấy mời"),
    (r'/CV\b',   "Công văn"),    # ← thêm mới so với phiên bản cũ
]

def regex_predict(text: str) -> str | None:
    """
    Dự đoán bằng luật Regex.
    Trả về label nếu tìm thấy, None nếu không.

    Chiến lược 2 lớp:
    1. Tìm keyword tiêu đề lớn trong 800 chars đầu (sau clean)
    2. Tìm ký hiệu số hiệu trong 800 chars đầu
    """
    cleaned    = clean_ocr_text(text)
    header_800 = cleaned[:HEADER_CHARS].upper()

    # Lớp 1: keyword tiêu đề
    for keyword, label in HEADER_RULES:
        if keyword in header_800:
            return label

    # Lớp 2: ký hiệu số hiệu
    # Chuẩn hóa: "SỔ", "SO" → "SỐ", xóa khoảng trắng thừa quanh "/"
    normalized = re.sub(r'S[ỔO]\s*:', 'SỐ:', header_800)
    for pattern, label in CODE_RULES:
        if re.search(pattern, normalized):
            return label

    # Lớp 3: V/v hoặc Kính gửi → Công văn (fallback cuối)
    if re.search(r'\bV[/\\]V\b', header_800) or 'KÍNH GỬI' in header_800:
        return "Công văn"

    return None


# =====================================================================
# MODEL TESTER
# =====================================================================

class ModelTester:
    def __init__(self, model_path: str):
        print(f"\n🚀 Tải model từ: {model_path}")

        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model path không tồn tại: {model_path}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"   Device: {self.device}")

        # ── PhoBERT
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model     = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()

        # ── Label mapping
        label_map_file = os.path.join(model_path, "label_mapping.json")
        if os.path.exists(label_map_file):
            with open(label_map_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            self.id_to_label = {int(k): v for k, v in mapping['id_to_label'].items()}
        else:
            # Fallback mặc định
            self.id_to_label = {
                0: "Báo cáo", 1: "Công văn", 2: "Giấy mời",
                3: "Kế hoạch", 4: "Quyết định", 5: "Thông báo", 6: "Tờ trình",
            }

        print(f"   Labels: {list(self.id_to_label.values())}")

        # ── OCR
        print("\n🚀 Tải OCR models...")
        self.det_model = PaddleOCR(
            use_angle_cls=True, lang="vi", use_gpu=False, show_log=False
        )
        config = Cfg.load_config_from_name('vgg_seq2seq')
        config['device'] = 'cpu'
        config['predictor']['beamsearch'] = False
        self.rec_model = Predictor(config)

        # Warm-up VietOCR
        try:
            self.rec_model.predict(Image.new('RGB', (100, 32), color=255))
        except Exception:
            pass

        print("   ✅ Tất cả model đã tải xong!\n")

    # ── OCR ───────────────────────────────────────────────────────────
    def extract_text_from_image(self, image_path: str) -> str | None:
        """Trích xuất text từ ảnh/PDF — giữ nguyên logic OCR."""
        try:
            pages = load_image(image_path)
            if not pages:
                return None

            full_text = ""
            for page_img in pages:
                processed_img  = preprocess_image_pro(page_img)
                gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)

                result = self.det_model.ocr(processed_img, rec=False)
                boxes  = result[0] if result and result[0] else []
                if not boxes:
                    continue

                # Sắp xếp boxes theo y rồi x
                heights = []
                for b in boxes:
                    pts = np.array(b, dtype=np.float32)
                    h   = max(np.linalg.norm(pts[0] - pts[3]),
                              np.linalg.norm(pts[1] - pts[2]))
                    heights.append(h)

                tol = max(5, int(np.median(heights) * 0.6) if heights else 5)
                boxes = sorted(
                    boxes,
                    key=lambda b: (
                        int(np.mean([p[1] for p in b]) // tol),
                        int(np.mean([p[0] for p in b])),
                    ),
                )

                # Cắt + resize từng box
                pil_imgs   = []
                boxes_info = []
                for box in boxes:
                    pts    = np.array(box, dtype=np.float32).reshape(4, 2)
                    width  = int(max(np.linalg.norm(pts[0]-pts[1]),
                                     np.linalg.norm(pts[2]-pts[3])))
                    height = int(max(np.linalg.norm(pts[0]-pts[3]),
                                     np.linalg.norm(pts[1]-pts[2])))
                    if width <= 0 or height <= 0:
                        continue

                    dst = np.array([[0,0],[width-1,0],[width-1,height-1],[0,height-1]],
                                   dtype="float32")
                    M    = cv2.getPerspectiveTransform(pts, dst)
                    crop = cv2.warpPerspective(gray_processed, M, (width, height))

                    if height > width * 1.2:
                        crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)

                    crop = cv2.copyMakeBorder(crop, 4, 4, 8, 8,
                                              cv2.BORDER_CONSTANT, value=255)
                    scale = 32 / crop.shape[0]
                    nw    = max(1, min(int(crop.shape[1] * scale), 1500))
                    crop  = cv2.resize(crop, (nw, 32), interpolation=cv2.INTER_CUBIC)

                    pil_imgs.append(Image.fromarray(
                        cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
                    ))
                    boxes_info.append({
                        "y": np.mean([p[1] for p in box]),
                        "h": height,
                    })

                # Batch predict
                if not pil_imgs:
                    continue
                try:
                    texts = self.rec_model.predict_batch(pil_imgs)
                except AttributeError:
                    texts = [self.rec_model.predict(img) for img in pil_imgs]

                page_text = ""
                prev_y, prev_h = -100, 0
                for info, t in zip(boxes_info, texts):
                    if not t.strip():
                        continue
                    if prev_y == -100:
                        page_text += t
                    elif (info["y"] - prev_y) < (prev_h * 1.5):
                        page_text += " " + t
                    else:
                        page_text += "\n" + t
                    prev_y = info["y"]
                    prev_h = info["h"]

                full_text += page_text + "\n"

            return full_text.strip() or None

        except Exception as e:
            print(f"      ❌ OCR error: {e}")
            return None

    # ── Predict ───────────────────────────────────────────────────────
    def predict(self, text: str) -> dict:
        """
        Dự đoán loại văn bản theo 2 bước:

        Bước 1: Regex rule-based trên 800 chars đầu
                → Nếu tìm thấy keyword/số hiệu rõ ràng → trả về luôn (confidence 99.9%)

        Bước 2: PhoBERT với extract_smart_input() (ĐỒNG BỘ VỚI TRAINING)
                → Dùng format "[HEADER] ... [CONTENT] ..." giống lúc train
        """
        if not text or not text.strip():
            return {
                "label": "Không xác định",
                "confidence": 0.0,
                "probs": {},
                "method": "none",
            }

        # ── Bước 1: Regex
        regex_label = regex_predict(text)

        # ── Bước 2: PhoBERT
        # Dùng extract_smart_input() — GIỐNG HỆT lúc train
        model_input = extract_smart_input(text)

        inputs = self.tokenizer(
            model_input,
            return_tensors="pt",
            truncation=True,
            max_length=256,
            padding=False,
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits
            probs  = torch.softmax(logits, dim=-1)[0]

        pred_id    = torch.argmax(probs).item()
        phobert_lbl = self.id_to_label.get(pred_id, f"Loại {pred_id}")
        confidence  = probs[pred_id].item()

        probs_dict = {
            self.id_to_label.get(i, f"Loại {i}"): round(p.item() * 100, 2)
            for i, p in enumerate(probs)
        }

        # ── Quyết định
        if regex_label:
            return {
                "label":      regex_label,
                "confidence": 99.9,
                "probs":      probs_dict,   # PhoBERT probs vẫn trả về để tham khảo
                "method":     "regex",
            }
        else:
            return {
                "label":      phobert_lbl,
                "confidence": round(confidence * 100, 2),
                "probs":      probs_dict,
                "method":     "phobert",
            }

    # ── Test 1 ảnh ────────────────────────────────────────────────────
    def test_single_image(self, image_path: str):
        print(f"\n{'='*70}")
        print(f"🖼️  Test: {Path(image_path).name}")
        print(f"{'='*70}")

        print("\n📖 Trích xuất text...")
        text = self.extract_text_from_image(image_path)
        if not text:
            print("❌ Không thể trích xuất text!")
            return

        print(f"\n📝 Text (800 chars đầu):\n{text[:800]}\n")

        result = self.predict(text)

        method_tag = {
            "regex":   "🔍 Regex Rule",
            "phobert": "🤖 PhoBERT AI",
        }.get(result["method"], result["method"])

        print(f"🎯 Kết quả: {result['label']}  [{method_tag}]  {result['confidence']:.1f}%")
        print(f"\n📊 Xác suất PhoBERT (tất cả loại):")
        for label, prob in sorted(result['probs'].items(), key=lambda x: x[1], reverse=True):
            bar = "█" * int(prob / 5)
            print(f"   {label:<15} {prob:>6.2f}%  {bar}")

    # ── Test cả thư mục ───────────────────────────────────────────────
    def test_directory(self, directory: str, export_csv: bool = True):
        print(f"\n{'='*70}")
        print(f"📁 Test thư mục: {directory}")
        print(f"{'='*70}")

        image_files = sorted([
            f for f in os.listdir(directory)
            if Path(f).suffix.lower() in
               {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.pdf'}
        ])

        if not image_files:
            print("❌ Không có file nào trong thư mục!")
            return

        print(f"\n📊 Tìm thấy {len(image_files)} file\n")

        results = []
        for i, fname in enumerate(image_files, 1):
            fpath = os.path.join(directory, fname)
            text  = self.extract_text_from_image(fpath)

            if not text:
                print(f"   [{i:>3}/{len(image_files)}] ❌ {fname}: Không OCR được")
                results.append({
                    'file': fname, 'label': 'OCR_FAILED',
                    'confidence': 0.0, 'method': 'none',
                })
                continue

            res = self.predict(text)
            results.append({
                'file': fname,
                'label': res['label'],
                'confidence': res['confidence'],
                'method': res['method'],
            })

            method_icon = "🔍" if res['method'] == 'regex' else "🤖"
            print(
                f"   [{i:>3}/{len(image_files)}] ✅ {fname:<40} "
                f"{res['label']:<15} {res['confidence']:>5.1f}% {method_icon}"
            )

        # ── Thống kê
        print(f"\n{'='*70}")
        print("📊 Thống kê:")
        label_counts = Counter(r['label'] for r in results)
        for label, count in sorted(label_counts.items(), key=lambda x: x[1], reverse=True):
            pct = count / len(results) * 100
            print(f"   {label:<15} {count:>4} file  ({pct:>5.1f}%)")

        valid = [r for r in results if r['label'] != 'OCR_FAILED']
        if valid:
            avg_conf = np.mean([r['confidence'] for r in valid])
            n_regex   = sum(1 for r in valid if r['method'] == 'regex')
            n_phobert = sum(1 for r in valid if r['method'] == 'phobert')
            print(f"\n   Độ tự tin TB    : {avg_conf:.2f}%")
            print(f"   Regex quyết định: {n_regex}/{len(valid)} file")
            print(f"   PhoBERT quyết định: {n_phobert}/{len(valid)} file")

        # ── Export CSV
        if export_csv:
            csv_path = os.path.join(directory, "test_results.csv")
            with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=['file', 'label', 'confidence', 'method'])
                writer.writeheader()
                writer.writerows(results)
            print(f"\n💾 Kết quả lưu vào: {csv_path}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description='Test PhoBERT văn bản hành chính')
    parser.add_argument('--model_path', default=None, help='Đường dẫn model đã train')
    parser.add_argument('--image',      default=None, help='Đường dẫn 1 ảnh để test')
    parser.add_argument('--directory',  default=None, help='Thư mục ảnh để test hàng loạt')
    parser.add_argument('--no_csv',     action='store_true', help='Không xuất CSV kết quả')
    args = parser.parse_args()

    if args.model_path is None:
        args.model_path = os.path.join(
            ROOT_DIR, "src", "models", "text_classifier", "phobert_finetuned"
        )

    tester = ModelTester(args.model_path)

    if args.image:
        tester.test_single_image(args.image)
    elif args.directory:
        tester.test_directory(args.directory, export_csv=not args.no_csv)
    else:
        print("\n💡 Cách dùng:")
        print("   # Test 1 ảnh:")
        print("   python scripts/4_test_model.py --image <path/to/image.jpg>")
        print("\n   # Test cả thư mục:")
        print("   python scripts/4_test_model.py --directory <path/to/folder>")
        print("\n   # Không xuất CSV:")
        print("   python scripts/4_test_model.py --directory <folder> --no_csv")

        # Gợi ý thư mục có sẵn
        for folder in ["quyet_dinh", "thong_bao", "cong_van"]:
            d = os.path.join(ROOT_DIR, "data", "raw", folder)
            if os.path.exists(d):
                print(f"\n   Ví dụ: python scripts/4_test_model.py --directory {d}")
                break


if __name__ == "__main__":
    main()