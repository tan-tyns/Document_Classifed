#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 BƯỚC 1: KHÁM PHÁ DATASET
Đếm số lượng ảnh trong mỗi loại văn bản
Kiểm tra các định dạng tệp được hỗ trợ
"""

import os
import sys
from pathlib import Path
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# Các định dạng ảnh được hỗ trợ
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.tiff'}

def explore_dataset(raw_data_dir):
    """
    Khám phá dataset từ thư mục data/raw
    In ra số lượng ảnh theo loại văn bản
    
    Lưu ý: PDF sẽ bỏ qua (cần cài đặt Poppler)
    """
    print("\n" + "="*70)
    print("📊 KHÁM PHÁ DATASET - TÍNH TOÁN THỐNG KÊ")
    print("="*70)
    
    if not os.path.exists(raw_data_dir):
        print(f"❌ Thư mục {raw_data_dir} không tồn tại!")
        return
    
    # Danh sách loại văn bản
    doc_types = {
        'bao_cao': 'Báo cáo',
        'cong_van': 'Công văn',
        'ke_hoach': 'Kế hoạch',
        'quyet_dinh': 'Quyết định',
        'thong_bao': 'Thông báo',
        'thu_moi': 'Giấy mời',
        'to_trinh': 'Tờ trình'
    }
    
    statistics = defaultdict(int)
    pdf_statistics = defaultdict(int)
    total_images = 0
    total_pdfs = 0
    
    print(f"\n🔍 Quét thư mục: {raw_data_dir}\n")
    print(f"{'Loại Văn Bản':<20} {'Thư mục':<20} {'JPG/PNG':<15} {'PDF':<10} {'Tỷ lệ (%)':<15}")
    print("-" * 80)
    
    for folder_name, doc_type_name in doc_types.items():
        folder_path = os.path.join(raw_data_dir, folder_name)
        
        if not os.path.exists(folder_path):
            print(f"⚠️  [{doc_type_name:<17}] {folder_name:<20} {'N/A':<15} {'N/A':<10} {'0%':<15}")
            continue
        
        # Đếm ảnh (không bao gồm PDF)
        image_count = 0
        pdf_count = 0
        for file in os.listdir(folder_path):
            file_ext = Path(file).suffix.lower()
            if file_ext in SUPPORTED_FORMATS:
                image_count += 1
            elif file_ext == '.pdf':
                pdf_count += 1
        
        statistics[folder_name] = image_count
        pdf_statistics[folder_name] = pdf_count
        total_images += image_count
        total_pdfs += pdf_count
        
        percentage = (image_count / 1) if image_count > 0 else 0
        
        status = "✅" if image_count > 0 else "⚠️"
        print(f"{status} {doc_type_name:<17} {folder_name:<20} {image_count:<15} {pdf_count:<10} {percentage:>6.1f}%")
    
    print("-" * 80)
    print(f"📈 TỔNG CỘNG: {total_images} JPG/PNG ảnh + {total_pdfs} PDF files\n")
    
    # Kiểm tra cân bằng dữ liệu
    if total_images == 0:
        print("❌ KHÔNG CÓ HÌNH ẢNH JPG/PNG NÀO! Vui lòng thêm ảnh vào data/raw/{category}/")
        if total_pdfs > 0:
            print(f"⚠️  Có {total_pdfs} file PDF nhưng chúng sẽ bỏ qua (cần cài Poppler để xử lý)")
        return False
    
    # Cảnh báo về cân bằng dữ liệu
    non_zero_counts = [v for v in statistics.values() if v > 0]
    
    if non_zero_counts:
        min_count = min(non_zero_counts)
        max_count = max(non_zero_counts)
        
        imbalance_ratio = max_count / min_count if min_count > 0 else 0
        if imbalance_ratio > 2:
            print(f"⚠️  CẢNH BÁO: Dữ liệu không cân bằng!")
            print(f"   Tỷ lệ không cân bằng: {imbalance_ratio:.1f}x")
            print(f"   (Min: {min_count}, Max: {max_count})")
            print(f"   💡 Gợi ý: Cân bằng dữ liệu bằng oversampling hoặc undersampling\n")
    
    # Chi tiết về dữ liệu trống
    empty_categories = [k for k, v in statistics.items() if v == 0]
    if empty_categories:
        print(f"⚠️  Thư mục trống (JPG/PNG): {', '.join(empty_categories)}")
    
    # Chi tiết về PDF
    if total_pdfs > 0:
        print(f"\n💡 Lưu ý về PDF files:")
        print(f"   {total_pdfs} file PDF được tìm thấy nhưng sẽ bỏ qua")
        print(f"   Để xử lý PDF, cài đặt Poppler:")
        print(f"   📌 Windows: choco install poppler (hoặc tải từ https://github.com/oschwartz10612/poppler-windows/releases/)")
        print(f"   📌 Linux: apt-get install poppler-utils")
        print(f"   📌 Mac: brew install poppler")
        print(f"   Sau đó sửa config trong src/utils/image_io.py")
    
    return True

if __name__ == "__main__":
    data_dir = os.path.join(ROOT_DIR, "data", "raw")
    success = explore_dataset(data_dir)
    
    if success:
        print("\n✅ Bước tiếp theo: Chạy `python scripts/2_build_dataset.py`\n")
    else:
        print("\n❌ Hãy thêm dữ liệu vào data/raw/{category}/ trước khi tiếp tục!\n")
