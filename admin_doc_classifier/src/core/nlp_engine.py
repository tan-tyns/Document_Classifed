import os
import re
import json
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# =====================================================================
# PHẢI ĐỒNG BỘ VỚI 3_train_model.py VÀ 4_test_model.py
# =====================================================================
HEADER_CHARS  = 500
SNIPPET_CHARS = 300


def clean_ocr_text(text: str) -> str:
    """
    Làm sạch nhiễu OCR — giữ nguyên dấu tiếng Việt.
    KHÔNG dùng [^\\w\\s] vì sẽ xóa mất àáảã... PhoBERT mất context.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' ')
    # Chỉ xóa các ký tự thực sự vô nghĩa, GIỮ LẠI dấu tiếng Việt
    # Giữ lại: chữ cái (kể cả Unicode tiếng Việt), số, dấu câu cơ bản
    text = re.sub(r'[ \t]+', ' ', text)   # chuẩn hóa space
    # Xóa ký tự điều khiển và ký tự lạ không phải text
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def extract_smart_input(text: str) -> str:
    """
    Tạo input cho model — PHẢI GIỐNG HỆT hàm trong 3_train_model.py.
    Format: "[HEADER] <800 chars đầu> [CONTENT] <300 chars tiếp>"
    """
    text    = clean_ocr_text(text)
    header  = text[:HEADER_CHARS]
    snippet = text[HEADER_CHARS: HEADER_CHARS + SNIPPET_CHARS]
    return f"[HEADER] {header} [CONTENT] {snippet}"


class PhoBertClassifier:
    def __init__(self, model_path: str = "vinai/phobert-base"):
        """
        Khởi tạo model phân loại văn bản.

        model_path:
          - Khi chưa train: "vinai/phobert-base" (dự đoán ngẫu nhiên)
          - Khi đã train  : đường dẫn thư mục chứa model đã fine-tune
                            VD: "src/models/text_classifier/phobert_finetuned"
        """
        print(f"🚀 Đang tải PhoBERT từ: {model_path}")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # ── Tokenizer: load từ model_path (đã save khi train)
        # Nếu model_path chưa có tokenizer (lần đầu) thì load từ HuggingFace
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)

        # ── Label mapping: đọc từ file label_mapping.json do 3_train_model.py lưu
        # KHÔNG hardcode vì thứ tự labels phụ thuộc vào sorted() lúc train
        label_map_file = os.path.join(model_path, "label_mapping.json")
        if os.path.exists(label_map_file):
            with open(label_map_file, "r", encoding="utf-8") as f:
                mapping = json.load(f)
            self.id_to_label = {
                int(k): v for k, v in mapping["id_to_label"].items()
            }
            num_labels = len(self.id_to_label)
            print(f"   Label mapping: {self.id_to_label}")
        else:
            # Fallback khi chưa train: thứ tự sorted() alphabet
            # (khớp với cách 3_train_model.py tạo label_to_id)
            default_labels = sorted([
                "Báo cáo", "Công văn", "Giấy mời",
                "Kế hoạch", "Quyết định", "Thông báo", "Tờ trình"
            ])
            self.id_to_label = {i: l for i, l in enumerate(default_labels)}
            num_labels = len(default_labels)
            print(f"   ⚠️  Không tìm thấy label_mapping.json — dùng mặc định sorted()")

        # ── Model
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            num_labels=num_labels,
            ignore_mismatched_sizes=True,
        )
        self.model.to(self.device)
        self.model.eval()

        print(f"   Device: {self.device}")
        print(f"   ✅ Model sẵn sàng!\n")

    def predict(self, text: str) -> dict:
        """
        Phân loại văn bản từ text OCR.

        Input : raw text từ OCR (chưa xử lý)
        Output: {"label": str, "confidence": float (0-100)}
        """
        if not text or not text.strip():
            return {"label": "Không xác định", "confidence": 0.0}

        # Dùng extract_smart_input() — ĐỒNG BỘ với lúc train
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
        confidence = probs[pred_id].item()

        return {
            "label":      self.id_to_label.get(pred_id, f"Loại {pred_id}"),
            "confidence": round(confidence * 100, 2),
        }


# ── Singleton — load 1 lần duy nhất khi import module
# Đổi model_path thành đường dẫn model đã train của bạn
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "models", "text_classifier", "phobert_finetuned"
)

phobert_engine = PhoBertClassifier(
    model_path=_MODEL_PATH if os.path.exists(_MODEL_PATH) else "vinai/phobert-base"
)