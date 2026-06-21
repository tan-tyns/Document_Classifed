import os
import shutil
from bing_image_downloader import downloader

# 1. Gắn cứng đường dẫn tuyệt đối để không bao giờ bị lưu sai chỗ
RAW_DATA_DIR = r"D:\NCKH_LV\OCR\admin_doc_classifier\data\raw"
LIMIT_PER_QUERY = 30  # Giảm xuống 30 để test cho nhanh

# 2. Bỏ 'filetype:jpg' vì Bing tự động tải ảnh rồi, nới lỏng từ khóa
search_queries = {
    "bao_cao": [
        'văn bản "báo cáo" "độc lập tự do hạnh phúc"',
        'mẫu "báo cáo tổng kết" có dấu đỏ'
    ],
    "ke_hoach": [
        'văn bản "kế hoạch" "độc lập tự do hạnh phúc"',
        'mẫu "kế hoạch tổ chức" có dấu đỏ'
    ]
}

def crawl_and_organize():
    print(f"🚀 Bắt đầu quá trình thu thập hình ảnh...\n")
    print(f"📁 Thư mục đích: {RAW_DATA_DIR}\n")
    
    temp_dir = os.path.join(RAW_DATA_DIR, "temp_downloads")
    os.makedirs(temp_dir, exist_ok=True)

    for label, queries in search_queries.items():
        target_dir = os.path.join(RAW_DATA_DIR, label)
        os.makedirs(target_dir, exist_ok=True)
        
        print(f"--- Đang xử lý nhãn: {label.upper()} ---")
        
        for query in queries:
            print(f"🔍 Đang tìm kiếm: {query}")
            try:
                # Đặt verbose=True để xem nó có thực sự đang tải không
                downloader.download(
                    query, 
                    limit=LIMIT_PER_QUERY,  
                    output_dir=temp_dir, 
                    adult_filter_off=True, 
                    force_replace=False, 
                    timeout=60,
                    verbose=True  # Đã đổi thành True
                )
                
                query_folder = os.path.join(temp_dir, query)
                if os.path.exists(query_folder):
                    downloaded_count = 0
                    for filename in os.listdir(query_folder):
                        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                            base_name, ext = os.path.splitext(filename)
                            new_filename = f"crawled_{label}_{base_name}{ext}"
                            
                            src_path = os.path.join(query_folder, filename)
                            dst_path = os.path.join(target_dir, new_filename)
                            
                            shutil.move(src_path, dst_path)
                            downloaded_count += 1
                    
                    shutil.rmtree(query_folder)
                    print(f"   ✅ Đã di chuyển {downloaded_count} ảnh vào {target_dir}")
                    
            except Exception as e:
                print(f"❌ Lỗi khi tải từ khóa '{query}': {e}")
                
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        
    print(f"\n🎉 Hoàn tất! Hãy vào kiểm tra {RAW_DATA_DIR}")

if __name__ == "__main__":
    crawl_and_organize()