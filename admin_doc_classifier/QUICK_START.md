# 📖 QUICK START - TRAIN MODEL PHÂN LOẠI VĂN BẢN

## ⚡ 4 Bước chính (30 phút - 1 giờ)

### 1️⃣ Khám phá dữ liệu
```bash
python scripts/1_explore_dataset.py
```
✅ Đếm số ảnh trong mỗi loại văn bản  
📌 Phát hiện: 361 JPG/PNG + 138 PDF = **499 file dữ liệu!**

---

### 2️⃣ Xây dựng dataset
```bash
python scripts/2_build_dataset.py
```
⏳ Trích xuất text từ ảnh + PDF bằng OCR (lâu nhất)  
💾 Tạo file `data/processed/dataset.csv`  
📌 **Poppler sẵn có!** - Xử lý cả 361 JPG/PNG + 138 PDF

---

### 3️⃣ Train model
```bash
python scripts/3_train_model.py
```
🤖 Fine-tune PhoBERT cho 7 loại văn bản  
✅ Lưu model vào `src/models/text_classifier/phobert_finetuned`

**Với tùy chỉnh** (nếu accuracy thấp):
```bash
python scripts/3_train_model.py --epochs 5 --batch_size 8 --lr 1e-5
```

---

### 4️⃣ Test model
```bash
# Test ảnh đơn lẻ
python scripts/4_test_model.py --image "data/raw/quyet_dinh/sample.jpg"

# Test cả thư mục
python scripts/4_test_model.py --directory "data/raw/quyet_dinh"
```

---

## 📊 Kết quả mong đợi

```
🎯 Accuracy: 85-95%
📈 F1 Score: 0.85-0.95
⏱️ Thời gian: 15-20 phút (CPU)
```

---

## 🚀 Sử dụng model trong main.py

Mở `src/core/nlp_engine.py` dòng 6-8, thay đổi:
```python
# Cũ (pretrain model - dự đoán ngẫu nhiên)
self.model = AutoModelForSequenceClassification.from_pretrained("vinai/phobert-base")

# Mới (fine-tune model - dự đoán chính xác)
self.model = AutoModelForSequenceClassification.from_pretrained("src/models/text_classifier/phobert_finetuned")
```

Sau đó chạy:
```bash
python main.py
```

---

## ⚠️ Cảnh báo trước khi bắt đầu

✅ **Kiểm tra có:**
- [ ] 50+ ảnh trong mỗi loại văn bản (lý tưởng 100+)
- [ ] Ảnh đặt trong `data/raw/{category}/`
- [ ] Tên thư mục: `bao_cao, cong_van, ke_hoach, quyet_dinh, thong_bao, thu_moi, to_trinh`
- [ ] Ảnh chất lượng tốt (rõ ràng, không quá tối)

❌ **Nếu thiếu gì:**
- Dữ liệu quá ít → Accuracy sẽ thấp (<70%)
- Ảnh chất lượng kém → OCR trích xuất sai

---

## 🔧 Xử lý sự cố nhanh

| Vấn đề | Giải pháp |
|--------|----------|
| **Accuracy < 70%** | Tăng `--epochs 10`, giảm `--lr 1e-5` |
| **Hết RAM / CUDA** | Giảm `--batch_size 8` |
| **OCR trích xuất sai** | Kiểm tra chất lượng ảnh trong `dataset.csv` |
| **Không có file CSV** | Chạy lại `2_build_dataset.py` |

---

## 📚 Tài liệu chi tiết

👉 Xem `TRAINING_GUIDE.md` để hiểu sâu hơn

---

## ✅ Quy trình đầy đủ

```bash
# Chuẩn bị
python scripts/1_explore_dataset.py

# Xây dựng dataset (chấp nhận: lâu ~15 phút)
python scripts/2_build_dataset.py

# Train model (CPU ~20 phút, GPU ~5 phút)
python scripts/3_train_model.py

# Test kết quả
python scripts/4_test_model.py --directory data/raw/quyet_dinh

# Cập nhật nlp_engine.py, rồi chạy main.py
python main.py
```

---

**🎉 Hoàn tất! Model của bạn đã sẵn sàng.**
