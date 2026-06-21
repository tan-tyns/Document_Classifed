#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🏗️ BƯỚC 2: XÂY DỰNG DATASET
Trích xuất text từ ảnh bằng OCR
Tạo file CSV với label và text cho training
"""

import os
import sys
import json
import time
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import cv2
import warnings

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from src.core.preprocess_image import preprocess_image_pro
from src.utils.image_io import imread, load_image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

# Suppress warnings
warnings.filterwarnings('ignore')

# Ánh xạ tên thư mục → nhãn
DOCUMENT_TYPE_MAPPING = {
    'bao_cao': 'Báo cáo',
    'cong_van': 'Công văn',
    'ke_hoach': 'Kế hoạch',
    'quyet_dinh': 'Quyết định',
    'thong_bao': 'Thông báo',
    'thu_moi': 'Giấy mời',
    'to_trinh': 'Tờ trình'
}

class DatasetBuilder:
    def __init__(self):
        """Khởi tạo OCR models"""
        print("\n🚀 Đang tải mô hình OCR...")
        
        # PaddleOCR cho text detection
        print("   📍 Tải PaddleOCR (Text Detection)...")
        self.det_model = PaddleOCR(
            use_angle_cls=True, 
            lang="vi", 
            use_gpu=False, 
            show_log=False
        )
        
        # VietOCR cho text recognition
        print("   📍 Tải VietOCR (Text Recognition)...")
        config = Cfg.load_config_from_name('vgg_seq2seq')
        config['device'] = 'cpu'
        config['predictor']['beamsearch'] = False
        self.rec_model = Predictor(config)
        
        # Warm-up
        dummy_img = Image.new('RGB', (100, 32), color=(255, 255, 255))
        try:
            _ = self.rec_model.predict(dummy_img)
        except Exception as e:
            print(f"   ⚠️  Lỗi warm-up VietOCR: {e}")
        
        print("   ✅ OCR models loaded successfully!\n")
        self.dataset = []
    
    def extract_text_from_image(self, image_path):
        """
        Trích xuất text từ 1 ảnh hoặc PDF
        Trả về text hoặc None nếu lỗi
        
        Hỗ trợ: JPG, PNG, BMP, GIF, WEBP, TIFF, PDF
        PDF được xử lý bằng Poppler (engine/poppler/)
        """
        try:
            pages = load_image(image_path)
            if not pages:
                return None
            
            full_text = ""
            for page_img in pages:
                # Tiền xử lý
                processed_img = preprocess_image_pro(page_img)
                gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
                
                # Text detection
                result = self.det_model.ocr(processed_img, rec=False)
                boxes = result[0] if result and result[0] else []
                
                if not boxes:
                    continue
                
                # Sắp xếp boxes theo y, x
                import numpy as np
                box_heights = []
                for b in boxes:
                    pts = np.array(b, dtype=np.float32)
                    h = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
                    box_heights.append(h)
                
                median_h = np.median(box_heights) if box_heights else 20
                tolerance = int(median_h * 0.6)
                if tolerance < 5:
                    tolerance = 5
                
                boxes = sorted(
                    boxes, 
                    key=lambda b: (int(np.mean([p[1] for p in b]) // tolerance), 
                                  int(np.mean([p[0] for p in b])))
                )
                
                # Cắt ảnh và chuẩn bị batch
                list_pil_imgs = []
                valid_boxes_info = []
                
                for box in boxes:
                    pts = np.array(box, dtype=np.float32).reshape(4, 2)
                    width = int(max(np.linalg.norm(pts[0] - pts[1]), np.linalg.norm(pts[2] - pts[3])))
                    height = int(max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2])))
                    
                    if width <= 0 or height <= 0:
                        continue
                    
                    dst_pts = np.array([[0, 0], [width-1, 0], [width-1, height-1], [0, height-1]], dtype="float32")
                    M = cv2.getPerspectiveTransform(pts, dst_pts)
                    crop = cv2.warpPerspective(gray_processed, M, (width, height))
                    
                    if height > width * 1.2:
                        crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                    margin_y, margin_x = 4, 8
                    crop_padded = cv2.copyMakeBorder(crop, margin_y, margin_y, margin_x, margin_x, 
                                                     cv2.BORDER_CONSTANT, value=255)
                    
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
                
                # Batch prediction
                if list_pil_imgs:
                    try:
                        batch_texts = self.rec_model.predict_batch(list_pil_imgs)
                    except AttributeError:
                        batch_texts = [self.rec_model.predict(img) for img in list_pil_imgs]
                    
                    page_text = ""
                    prev_y = -100
                    prev_h = 0
                    
                    for info, text in zip(valid_boxes_info, batch_texts):
                        if text.strip():
                            if prev_y == -100:
                                page_text += text
                            else:
                                if (info["y"] - prev_y) < (prev_h * 1.5):
                                    page_text += " " + text
                                else:
                                    page_text += "\n" + text
                            prev_y = info["y"]
                            prev_h = info["h"]
                    
                    full_text += page_text + "\n"
            
            return full_text if full_text.strip() else None
            
        except Exception as e:
            print(f"      ❌ Error processing {image_path}: {e}")
            return None
    
    def build_dataset(self, raw_data_dir, output_file):
        """
        Xây dựng dataset từ thư mục raw_data_dir
        Lưu vào output_file (JSON + CSV)
        
        Lưu ý: Hỗ trợ JPG/PNG/PDF. PDF được xử lý bằng Poppler
        """
        print("="*70)
        print("🏗️  XÂY DỰNG DATASET TỪ HÌNH ẢNH & PDF")
        print("="*70)
        
        if not os.path.exists(raw_data_dir):
            print(f"❌ Thư mục {raw_data_dir} không tồn tại!")
            return False
        
        self.dataset = []
        total_processed = 0
        total_failed = 0
        
        # Lặp qua từng loại văn bản
        for folder_name, doc_type_label in tqdm(DOCUMENT_TYPE_MAPPING.items(), 
                                                 desc="Processing categories"):
            folder_path = os.path.join(raw_data_dir, folder_name)
            
            if not os.path.exists(folder_path):
                print(f"   ⚠️  Thư mục không tồn tại: {folder_name}")
                continue
            
            # Lấy danh sách tất cả file (JPG/PNG/PDF/...)
            image_files = [
                f for f in os.listdir(folder_path)
                if Path(f).suffix.lower() in {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff', '.pdf'}
            ]
            
            if not image_files:
                print(f"   ⚠️  Thư mục trống: {folder_name}")
                continue
            
            print(f"\n📂 {doc_type_label} ({folder_name}): {len(image_files)} file")
            
            for img_file in tqdm(image_files, desc=f"  Extracting text from {folder_name}", leave=False):
                img_path = os.path.join(folder_path, img_file)
                
                try:
                    text = self.extract_text_from_image(img_path)
                    
                    if text and len(text.strip()) > 10:  # Yêu cầu tối thiểu độ dài
                        self.dataset.append({
                            'label': doc_type_label,
                            'text': text.strip(),
                            'source_file': img_file
                        })
                        total_processed += 1
                    else:
                        total_failed += 1
                except Exception as e:
                    print(f"      ❌ Error: {img_file} - {e}")
                    total_failed += 1
        
        print("\n" + "="*70)
        print(f"✅ Kết quả: {total_processed} file xử lý thành công")
        print(f"⚠️  {total_failed} file lỗi/không đủ dữ liệu")
        print("="*70)
        
        if not self.dataset:
            print("❌ Không có dữ liệu nào được trích xuất!")
            return False
        
        # Lưu thành JSON
        json_path = output_file.replace('.csv', '.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Lưu JSON: {json_path}")
        
        # Lưu thành CSV
        df = pd.DataFrame(self.dataset)
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"💾 Lưu CSV:  {output_file}")
        
        # Thống kê
        print(f"\n📊 Thống kê:")
        print(df['label'].value_counts().to_string())
        
        return True

def main():
    raw_data_dir = os.path.join(ROOT_DIR, "data", "raw")
    output_csv = os.path.join(ROOT_DIR, "data", "processed", "dataset.csv")
    
    # Tạo thư mục output nếu chưa tồn tại
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    builder = DatasetBuilder()
    success = builder.build_dataset(raw_data_dir, output_csv)
    
    if success:
        print(f"\n✅ Bước tiếp theo: Chạy `python scripts/3_train_model.py`\n")
    else:
        print("\n❌ Lỗi xây dựng dataset!\n")

if __name__ == "__main__":
    main()
    

