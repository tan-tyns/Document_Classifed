# 🚀 HƯỚNG DẪN CHI TIẾT: TRAIN MODEL AI PHÂN LOẠI 7 LOẠI VĂN BẢN

## 📋 MỤC LỤC
1. [Chuẩn bị dữ liệu](#1-chuẩn-bị-dữ-liệu)
2. [Cách thức hoạt động](#2-cách-thức-hoạt-động)
3. [Từng bước chi tiết](#3-từng-bước-chi-tiết)
4. [Tối ưu hóa & Tùy chỉnh](#4-tối-ưu-hóa--tùy-chỉnh)
5. [Xử lý sự cố](#5-xử-lý-sự-cố)

---

## 1. CỰA BỊ DỮ LIỆU

### Cấu trúc thư mục dữ liệu
```
data/raw/
├── bao_cao/           # Báo cáo (ghi chứng, báo cáo, tờ rơi,...)
│   ├── img1.jpg
│   ├── img2.png
│   └── ...
├── cong_van/          # Công văn
│   ├── doc1.jpg
│   └── ...
├── ke_hoach/          # Kế hoạch
│   ├── plan1.jpg
│   └── ...
├── quyet_dinh/        # Quyết định
│   ├── decision1.jpg
│   └── ...
├── thong_bao/         # Thông báo
│   ├── notice1.jpg
│   └── ...
├── thu_moi/           # Giấy mời
│   ├── invite1.jpg
│   └── ...
└── to_trinh/          # Tờ trình
    ├── proposal1.jpg
    └── ...
```

### Yêu cầu về dữ liệu
- **Định dạng**: JPG, PNG, BMP, GIF, WEBP, TIFF, **PDF** ✅ (Poppler sẵn có)
- **Số lượng tối thiểu**: 20-30 ảnh/loại (lý tưởng 50-100/loại)
- **Chất lượng**: Ảnh rõ ràng, không quá bị biến dạng
- **Cân bằng**: Cố gắng có số lượng ảnh gần bằng nhau giữa các loại

### Lấy tên thư mục chính xác
Phải sử dụng **đúng** tên thư mục này:
```
bao_cao, cong_van, ke_hoach, quyet_dinh, thong_bao, thu_moi, to_trinh
```

---

## 2. CÁCH THỨC HOẠT ĐỘNG

### Pipeline huấn luyện
```
┌─────────────────────────────────────────────────────────────┐
│ BƯỚC 1: KHÁM PHÁ DATASET (1_explore_dataset.py)              │
│ ├─ Đếm số lượng ảnh/loại                                    │
│ ├─ Kiểm tra cân bằng dữ liệu                                │
│ └─ Cảnh báo nếu thiếu dữ liệu                              │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ BƯỚC 2: XÂY DỰNG DATASET (2_build_dataset.py)                │
│ ├─ Tải OCR models (PaddleOCR + VietOCR)                     │
│ ├─ Trích xuất text từ mỗi ảnh                               │
│ ├─ Tạo file CSV: label | text | source_file                │
│ └─ Lưu vào data/processed/dataset.csv                       │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ BƯỚC 3: TRAIN MODEL (3_train_model.py)                      │
│ ├─ Load dataset từ CSV                                       │
│ ├─ Split: 70% train, 15% val, 15% test                     │
│ ├─ Fine-tune PhoBERT model                                  │
│ ├─ Evaluate trên validation set                            │
│ └─ Lưu model vào src/models/text_classifier/               │
└──────────────────┬──────────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────────┐
│ BƯỚC 4: TEST & ĐÁNH GIÁ (4_test_model.py)                   │
│ ├─ Test trên ảnh đơn lẻ                                     │
│ ├─ Test trên toàn bộ thư mục                                │
│ └─ In kết quả & thống kê                                    │
└─────────────────────────────────────────────────────────────┘
```

### Các công nghệ sử dụng
- **OCR**: PaddleOCR (detection) + VietOCR (recognition)
- **NLP**: PhoBERT (vinai/phobert-base)
- **Framework**: Hugging Face Transformers
- **Training**: PyTorch with Trainer API

---

## 3. TỪNG BƯỚC CHI TIẾT

### 🔍 BƯỚC 1: KHÁM PHÁ DATASET

**Mục đích**: Kiểm tra số lượng ảnh, cân bằng dữ liệu

**Chạy lệnh**:
```bash
python scripts/1_explore_dataset.py
```

**Kết quả mong đợi**:
```
========================================================================
📊 KHÁM PHÁ DATASET - TÍNH TOÁN THỐNG KÊ
========================================================================

🔍 Quét thư mục: d:\NCKH_LV\OCR\admin_doc_classifier\data\raw

Loại Văn Bản        Thư mục              Số lượng        Tỷ lệ (%)      
----------------------------------------------------------------------
✅ Báo cáo           bao_cao              45              15.0%
✅ Công văn          cong_van             52              17.3%
✅ Kế hoạch          ke_hoach             38              12.7%
✅ Quyết định        quyet_dinh           55              18.3%
✅ Thông báo         thong_bao            48              16.0%
✅ Giấy mời          thu_moi              42              14.0%
✅ Tờ trình          to_trinh             21                7.0%
----------------------------------------------------------------------
📈 TỔNG CỘNG: 301 ảnh
```

**Cảnh báo cơ thương**:
- Nếu có loại < 10 ảnh: ⚠️ Thêm dữ liệu cho loại đó
- Nếu không cân bằng (tỷ lệ > 2x): Có thể dùng oversampling trong training

---

### 🏗️ BƯỚC 2: XÂY DỰNG DATASET

**Mục đích**: Trích xuất text từ ảnh & PDF, tạo CSV training

**Chạy lệnh**:
```bash
python scripts/2_build_dataset.py
```

**Quá trình**:
1. Tải OCR models (PaddleOCR, VietOCR) - lần đầu khoảng 2-3 phút
2. Lặp qua từng loại văn bản
3. Lặp qua từng ảnh/PDF trong loại đó
4. Trích xuất text bằng OCR
5. Tạo file CSV với cột: `label | text | source_file`

**📌 Poppler đã sẵn có!**: 
- Poppler nằm tại `engine/poppler/Library/bin/`
- Script sẽ tự động sử dụng Poppler để xử lý PDF
- Hỗ trợ cả JPG/PNG + PDF → **+361 ảnh + 138 PDF = 499 file dữ liệu!**

**Thời gian dự kiến**:
- ~50 ảnh: 2-3 phút
- ~300 ảnh: 10-15 phút

**Kết quả**:
```
========================================================================
🏗️  XÂY DỰNG DATASET TỪ HÌNH ẢNH
========================================================================

📂 Báo cáo (bao_cao): 45 ảnh
   Extracting text from bao_cao: 100%|████████| 45/45
📂 Công văn (cong_van): 52 ảnh
   Extracting text from cong_van: 100%|████████| 52/52
...

========================================================================
✅ Kết quả: 298 ảnh xử lý thành công, 3 lỗi
========================================================================

💾 Lưu JSON: data/processed/dataset.json
💾 Lưu CSV:  data/processed/dataset.csv

📊 Thống kê:
Báo cáo        45
Công văn       52
Kế hoạch       38
Quyết định     55
Thông báo      48
Giấy mời       42
Tờ trình       21
```

**Kiểm tra**: Xem file `data/processed/dataset.csv`
```
label,text,source_file
Báo cáo,"Công ty TNHH ABC Báo cáo tổng kết năm 2024...",file1.jpg
Công văn,"Sở KHĐT Hà Nội Công văn số 123/SK-KHĐT...",file2.jpg
...
```

---

### 🤖 BƯỚC 3: TRAIN MODEL

**Mục đích**: Fine-tune PhoBERT cho phân loại văn bản

**Chạy lệnh cơ bản**:
```bash
python scripts/3_train_model.py
```

**Với tùy chỉnh**:
```bash
python scripts/3_train_model.py \
    --csv_file data/processed/dataset.csv \
    --output_dir src/models/text_classifier/phobert_finetuned \
    --epochs 3 \
    --batch_size 16 \
    --lr 2e-5
```

**Thông số quan trọng**:
| Thông số | Mặc định | Ghi chú |
|----------|----------|---------|
| `epochs` | 3 | Số lần lặp qua toàn bộ dataset. Tăng lên 5-10 cho dữ liệu nhiều |
| `batch_size` | 16 | Số mẫu/batch. Giảm xuống 8 nếu hết RAM |
| `lr` | 2e-5 | Learning rate. Giữ giá trị này cho PhoBERT |

**Quá trình training**:
```
========================================================================
🚀 TRAINING PHOBERT FOR VIETNAMESE DOCUMENT CLASSIFICATION
========================================================================

Cấu hình:
   CSV File:     data/processed/dataset.csv
   Output Dir:   src/models/text_classifier/phobert_finetuned
   Epochs:       3
   Batch Size:   16
   Learning Rate: 2e-5
   Model:        vinai/phobert-base

📂 Tải dataset từ: data/processed/dataset.csv
   📊 Tổng cộng: 298 mẫu dữ liệu
   📋 Các cột: ['label', 'text', 'source_file']
   ✅ Sau khi xóa trống: 298 mẫu

🔄 Chuẩn bị dataset...
   Max length: 256
   📌 Label mapping:
      0: Báo cáo
      1: Công văn
      2: Kế hoạch
      3: Quyết định
      4: Thông báo
      5: Giấy mời
      6: Tờ trình

   📊 Split:
      Train: 210 (70.5%)
      Val:   44 (14.8%)
      Test:  44 (14.8%)

   🔄 Tokenizing...
   ✅ Dataset prepared!

========================================================================
🤖 BẮT ĐẦU TRAINING MODEL
========================================================================

⏳ Đang training...

Epoch 1/3
 10%|███ | 13/130 [01:45<15:45, 8.1s/it]
 20%|██████ | 26/130 [03:28<13:55, 8.0s/it]
...
Epoch 3/3
100%|███████████| 130/130 [10:24<00:00, 4.8s/it]

✅ Training hoàn tất!

========================================================================
📊 ĐÁNH GIÁ MODEL TRÊN TEST SET
========================================================================

📈 Kết quả:
   Accuracy:  0.9091
   Precision: 0.9115
   Recall:    0.9091
   F1 Score:  0.9093

📋 Classification Report:
              precision    recall  f1-score   support

      Báo cáo      0.9000    1.0000    0.9474        9
      Công văn     0.9000    0.8000    0.8421        5
      Kế hoạch     1.0000    0.7143    0.8333        7
      Quyết định   0.8571    1.0000    0.9231        6
      Thông báo    1.0000    1.0000    1.0000        6
      Giấy mời     0.8000    0.8000    0.8000        5
      Tờ trình     1.0000    1.0000    1.0000        4

   micro avg      0.9091    0.9091    0.9091       42
   macro avg      0.9224    0.9147    0.9180       42

💾 Lưu model vào: src/models/text_classifier/phobert_finetuned
💾 Lưu label mapping vào: src/models/text_classifier/phobert_finetuned/label_mapping.json

========================================================================
✅ Training hoàn tất!
========================================================================

📌 Model được lưu vào: src/models/text_classifier/phobert_finetuned
📌 Để sử dụng model, cập nhật nlp_engine.py:
   PhoBertClassifier(model_path='src/models/text_classifier/phobert_finetuned')
```

**Kết quả mong đợi**:
- Accuracy: > 85% (với dữ liệu cân bằng, 100+ ảnh/loại)
- F1 Score: > 0.85

**Thời gian**:
- ~300 ảnh, 3 epochs: 15-20 phút trên CPU
- Nhanh hơn 3-5x trên GPU

---

### 📊 BƯỚC 4: TEST & ĐÁNH GIÁ

**Test trên ảnh đơn lẻ**:
```bash
python scripts/4_test_model.py --image "data/raw/quyet_dinh/sample.jpg"
```

**Kết quả**:
```
======================================================================
🖼️  Test: sample.jpg
======================================================================

📖 Trích xuất text từ ảnh...

📝 Text (đầu 200 ký tự):
Quyết định số 123/QĐ-UBND
Về việc phê duyệt dự án cải thiện cơ sở hạ tầng...

🎯 Kết quả dự đoán:
   Loại: Quyết định
   Tự tin: 97.84%

📊 Xác suất cho từng loại:
   Quyết định          97.84% ███████████████████
   Công văn             1.32% 
   Tờ trình             0.52% 
   Kế hoạch             0.18% 
   Báo cáo              0.08% 
   Thông báo            0.05% 
   Giấy mời             0.01% 
```

**Test trên toàn bộ thư mục**:
```bash
python scripts/4_test_model.py --directory "data/raw/quyet_dinh"
```

**Kết quả**:
```
======================================================================
📂 Test tất cả ảnh trong: data/raw/quyet_dinh
======================================================================

📊 Tìm thấy 55 ảnh

   [1/55] ✅ doc1.jpg: Quyết định (97.84%)
   [2/55] ✅ doc2.jpg: Quyết định (96.23%)
   [3/55] ✅ doc3.jpg: Quyết định (95.12%)
   ...

======================================================================
📊 Thống kê:
======================================================================
   Quyết định      54 ảnh ( 98.2%)
   Công văn         1 ảnh (  1.8%)
   Kế hoạch         0 ảnh (  0.0%)
   ...

   Độ tự tin trung bình: 96.34%
```

---

## 4. TỐI ƯU HÓA & TÙY CHỈNH

### 🎯 Nếu độ chính xác thấp (< 80%)

**Nguyên nhân & Giải pháp**:

| Vấn đề | Giải pháp |
|--------|----------|
| Dữ liệu quá ít (<20 ảnh/loại) | Thêm ảnh, sử dụng data augmentation |
| Dữ liệu không cân bằng | Sử dụng oversampling/undersampling |
| Text trích xuất sai (OCR) | Kiểm tra chất lượng ảnh, sửa lỗi OCR |
| Learning rate quá cao | Giảm từ 2e-5 xuống 1e-5 |
| Epochs quá ít | Tăng từ 3 lên 5-10 |
| Model underfitting | Tăng epochs, giảm learning rate |

**Lệnh điều chỉnh**:
```bash
# Epochs nhiều hơn, learning rate thấp hơn
python scripts/3_train_model.py \
    --epochs 10 \
    --lr 1e-5 \
    --batch_size 8
```

### 💾 Sử dụng model đã train trong main.py

**Bước 1**: Mở `src/core/nlp_engine.py`

**Bước 2**: Thay đổi dòng khởi tạo (dòng 6-8):
```python
# Cũ:
self.model = AutoModelForSequenceClassification.from_pretrained(
    "vinai/phobert-base",  # ← Không fine-tune
    num_labels=7,
)

# Mới:
self.model = AutoModelForSequenceClassification.from_pretrained(
    "src/models/text_classifier/phobert_finetuned",  # ← Đã fine-tune
    num_labels=7,
)
```

**Bước 3**: Kiểm tra labels (dòng 22-26) khớp với model:
```python
self.labels = [
    "Báo cáo", "Công văn", "Kế hoạch", 
    "Quyết định", "Thông báo", "Giấy mời", "Tờ trình"
]
```

**Bước 4**: Chạy `main.py`
```bash
python main.py
```

---

## 5. XỬ LÝ SỰ CỐ

### ❌ Lỗi: "Thư mục không tồn tại"
**Nguyên nhân**: Đường dẫn thư mục sai

**Giải pháp**:
```bash
# Kiểm tra cấu trúc
ls data/raw/

# Nên thấy:
# bao_cao  cong_van  ke_hoach  quyet_dinh  thong_bao  thu_moi  to_trinh
```

### ❌ Lỗi: "CUDA out of memory"
**Nguyên nhân**: Batch size quá lớn

**Giải pháp**:
```bash
python scripts/3_train_model.py --batch_size 8
```

### ❌ Lỗi: "No module named 'paddleocr'"
**Nguyên nhân**: Chưa cài dependencies

**Giải pháp**:
```bash
pip install -r requirements.txt
```

### ⚠️ Cảnh báo: OCR trích xuất text sai
**Nguyên nhân**: Ảnh bị nhiều lỗi, chữ nhỏ, ảnh đen

**Giải pháp**:
- Xóa ảnh chất lượng thấp khỏi dataset
- Hoặc tăng độ xử lý ảnh trong `preprocess_image_pro()`

### ⚠️ Cảnh báo: Model dự đoán sai (accuracy 50-60%)
**Nguyên nhân**:
1. Dữ liệu quá ít
2. OCR trích xuất sai
3. 7 loại văn bản quá giống nhau

**Giải pháp**:
- Tăng dữ liệu
- Kiểm tra chất lượng CSV
- Tăng epochs & giảm learning rate

---

## 📝 CHEAT SHEET - Lệnh nhanh

```bash
# 1. Khám phá dataset
python scripts/1_explore_dataset.py

# 2. Xây dựng dataset (trích xuất text từ ảnh)
python scripts/2_build_dataset.py

# 3. Train model (mặc định)
python scripts/3_train_model.py

# 3. Train model (tùy chỉnh)
python scripts/3_train_model.py --epochs 5 --batch_size 8 --lr 1e-5

# 4. Test trên ảnh đơn
python scripts/4_test_model.py --image "path/to/image.jpg"

# 4. Test trên thư mục
python scripts/4_test_model.py --directory "data/raw/quyet_dinh"

# Chạy main.py với model đã train
python main.py
```

---

## 🎓 KIẾN THỨC NỀN

### PhoBERT là gì?
- **PhoBERT**: BERT pre-trained trên dữ liệu tiếng Việt 20GB
- **Base model**: 12 transformer layers, 110M parameters
- **Fine-tune**: Thêm classification head cho 7 labels
- **Output**: Vector 768 chiều → 7 class probabilities

### Cách model dự đoán
```
1. Input: Text từ ảnh (ví dụ: "Quyết định số 123...")
2. Tokenize: Chia thành tokens (từ con)
3. Embedding: Chuyển thành vectors
4. PhoBERT: Xử lý contextual
5. Classification Head: 7 logits → softmax → probabilities
6. Output: (Quyết định, 97.8%)
```

### Train vs Fine-tune
- **Train từ đầu**: Khó, cần 1000+ ảnh, mất nhiều thời gian
- **Fine-tune** (TRANSFER LEARNING): Dễ, cần 50-100 ảnh, nhanh

### Tại sao split 70-15-15?
- **70% train**: Dùng để cập nhật trọng số model
- **15% val**: Kiểm tra performance, sử dụng early stopping
- **15% test**: Đánh giá độ chính xác cuối cùng (không bị bias)

---

## 📚 TÀI LIỆU THAM KHẢO

- PhoBERT: https://github.com/VinAIResearch/PhoBERT
- Transformers: https://huggingface.co/docs/transformers
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- VietOCR: https://github.com/pbcquoc/vietocr

---

**✅ Chúc bạn huấn luyện model thành công!** 🎉

Nếu có vấn đề, kiểm tra:
1. Cấu trúc thư mục `data/raw/`
2. Chất lượng ảnh
3. File `data/processed/dataset.csv`
4. Log khi train
