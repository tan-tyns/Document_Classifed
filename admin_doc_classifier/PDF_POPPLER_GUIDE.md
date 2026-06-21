# 📋 POPPLER - ĐÌNH & CẢU HÌNH

## ✅ TỐI: POPPLER ĐÃ CÓ!

Poppler đã được tải về và đặt tại:
```
engine/poppler/
├── Library/
│   ├── bin/          ← Poppler binary (chính)
│   ├── include/
│   ├── lib/
│   └── share/
└── share/
```

**Script sẽ tự động sử dụng Poppler này để xử lý PDF!**

✅ **Không cần cài đặt gì thêm**

---

## 📊 Lợi ích

Vì Poppler sẵn có, bạn có:
- ✅ 361 JPG/PNG ảnh
- ✅ **+ 138 file PDF**
- ✅ = **499 file dữ liệu tổng cộng!**

So sánh:
| | Có Poppler | Không Poppler |
|------|-----------|-------------|
| JPG/PNG | 361 | 361 |
| PDF | ✅ 138 | ❌ 0 |
| **Tổng** | **499** | 361 |

---

## 🚀 Cách sử dụng

Chỉ cần chạy script 2 bình thường:
```bash
python scripts/2_build_dataset.py
```

Script sẽ tự động:
1. Phát hiện Poppler tại `engine/poppler/Library/bin/`
2. Xử lý JPG/PNG ảnh
3. Xử lý PDF file bằng Poppler
4. Tạo file CSV với **499 mẫu dữ liệu**

---

## ⚙️ CẤU HÌNH (Nếu cần thay đổi)

File cấu hình: `src/utils/image_io.py` (dòng 51-54)

```python
# Hiện tại (tự động tìm Poppler):
poppler_path = os.path.join(project_root, "engine", "poppler", "Library", "bin")
```

Nếu muốn dùng Poppler khác:
```python
# Tuỳ chỉnh:
poppler_path = "/path/to/your/poppler/bin"
```

---

## ✅ KIỂM TRA

Nếu muốn kiểm tra Poppler hoạt động:

```python
from src.utils.image_io import load_image

# Test với PDF
pdf_path = "data/raw/cong_van/1.pdf"
pages = load_image(pdf_path)
print(f"Trích xuất được {len(pages)} trang")
```

Hoặc chạy script 2_build_dataset.py - nó sẽ báo nếu có lỗi.

---

## 🎉 Tóm tắt

**Poppler đã sẵn có → Bạn có thêm 138 file PDF dữ liệu → Model sẽ tốt hơn!**

Hãy chạy: `python scripts/2_build_dataset.py`
