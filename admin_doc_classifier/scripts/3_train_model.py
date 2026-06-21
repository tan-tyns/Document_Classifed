#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 BƯỚC 3: TRAIN MODEL PHOBERT (ĐÃ TỐI ƯU)
Fine-tune PhoBERT để phân loại văn bản hành chính.

CÁC CẢI TIẾN SO VỚI PHIÊN BẢN CŨ:
  1. Trích header thông minh: chỉ lấy 800 chars đầu (nơi chứa loại văn bản)
     thay vì full text → model focus vào phần quan trọng nhất.
  2. Class weights: bù đắp cho imbalanced dataset (Giấy mời 159 vs Báo cáo 100).
  3. Data augmentation nhẹ: random crop vị trí lấy text để model không overfit header.
  4. Tăng epochs 3 → 5, warmup steps tăng lên, scheduler cosine.
  5. Hybrid input: [HEADER] + [SEP] + snippet nội dung (không bị cắt mất keyword).
  6. Lưu confusion matrix và report ra file để dễ phân tích.
"""

import os
import sys
import json
import re
import argparse
import random
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    confusion_matrix,
    classification_report,
)
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)
from datasets import Dataset

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)


# =====================================================================
# CONFIG
# =====================================================================

# Keyword nhận diện loại văn bản — dùng để check data và extract header
LABEL_KEYWORDS = {
    'Báo cáo':    ['BÁO CÁO', '/BC-', '/BC'],
    'Công văn':   ['V/v', 'V/V', 'Kính gửi', '/CV-', '/CV'],
    'Giấy mời':   ['GIẤY MỜI', 'Giấy mời', '/GM-', '/GM', 'THƯ MỜI'],
    'Kế hoạch':   ['KẾ HOẠCH', '/KH-', '/KH'],
    'Quyết định': ['QUYẾT ĐỊNH', '/QĐ-', '/QĐ'],
    'Thông báo':  ['THÔNG BÁO', '/TB-', '/TB'],
    'Tờ trình':   ['TỜ TRÌNH', '/TTr-', '/TTr'],
}

# Số ký tự lấy từ phần đầu văn bản (nơi chứa quốc hiệu, số hiệu, loại VB)
HEADER_CHARS = 800

# Số ký tự snippet nội dung ghép thêm sau header
SNIPPET_CHARS = 300


# =====================================================================
# TEXT PREPROCESSING
# =====================================================================

def clean_ocr_text(text: str) -> str:
    """
    Làm sạch nhiễu OCR trước khi đưa vào model:
    - Chuẩn hóa khoảng trắng
    - Bỏ các ký tự đặc biệt vô nghĩa
    - Giữ dấu câu tiếng Việt quan trọng (V/v, /, -)
    """
    # Chuẩn hóa newline và tab
    text = text.replace('\r\n', '\n').replace('\r', '\n').replace('\t', ' ')

    # Bỏ ký tự lạ không phải tiếng Việt/số/dấu câu cơ bản
    text = re.sub(r'[^\w\s\.,;:!?()\-/\'\"àáảãạăắặằẳẵâầấậẩẫèéẻẽẹêềếệểễìíỉĩịòóỏõọôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđÀÁẢÃẠĂẮẶẰẲẴÂẦẤẬẨẪÈÉẺẼẸÊỀẾỆỂỄÌÍỈĨỊÒÓỎÕỌÔỒỐỘỔỖƠỜỚỢỞỠÙÚỦŨỤƯỪỨỰỬỮỲÝỶỸỴĐ]', ' ', text)

    # Chuẩn hóa nhiều space thành 1
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def extract_smart_input(text: str, augment: bool = False) -> str:
    """
    Tạo input thông minh cho model:
    - Phần HEADER: 800 chars đầu (chứa quốc hiệu, số hiệu, loại văn bản)
    - Phần SNIPPET: 300 chars tiếp theo (hoặc random crop nếu augment=True)
    - Format: "[HEADER] <header> [CONTENT] <snippet>"

    Tại sao làm vậy:
    - Keyword loại VB nằm ở ~160-220 chars → header 800 chars là đủ
    - Thêm snippet nội dung giúp model phân biệt các loại VB có cấu trúc tương tự
    - Augmentation: random crop giúp model không overfit vị trí cố định
    """
    text = clean_ocr_text(text)

    header = text[:HEADER_CHARS]

    if augment and len(text) > HEADER_CHARS + SNIPPET_CHARS:
        # Random lấy snippet ở vị trí khác nhau trong nội dung
        max_start = len(text) - SNIPPET_CHARS
        start = random.randint(HEADER_CHARS, min(max_start, HEADER_CHARS + 500))
        snippet = text[start: start + SNIPPET_CHARS]
    else:
        snippet = text[HEADER_CHARS: HEADER_CHARS + SNIPPET_CHARS]

    return f"[HEADER] {header} [CONTENT] {snippet}"


# =====================================================================
# WEIGHTED TRAINER — thêm class weights để xử lý imbalanced data
# =====================================================================

class WeightedTrainer(Trainer):
    """
    Custom Trainer với class-weighted cross entropy loss.
    Giúp model không bị bias về các loại VB có nhiều mẫu (Giấy mời 159)
    và bỏ qua các loại ít mẫu (Báo cáo 100).
    """
    def __init__(self, class_weights: torch.Tensor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits

        loss_fn = nn.CrossEntropyLoss(
            weight=self.class_weights.to(logits.device)
        )
        loss = loss_fn(logits, labels)

        return (loss, outputs) if return_outputs else loss


# =====================================================================
# MAIN TRAINER CLASS
# =====================================================================

class PhoBertTrainer:
    def __init__(self, model_name: str = "vinai/phobert-base", num_labels: int = 7):
        print("\n🚀 Khởi tạo PhoBERT Trainer...")

        self.model_name  = model_name
        self.num_labels  = num_labels
        self.device      = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        print(f"   Device     : {self.device}")
        print(f"   Model      : {model_name}")
        print(f"   Num labels : {num_labels}")

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            ignore_mismatched_sizes=True,
        )
        self.model.to(self.device)
        print("   ✅ Khởi tạo xong!\n")

    # ── Tải CSV ───────────────────────────────────────────────────────
    def load_dataset(self, csv_file: str) -> pd.DataFrame | None:
        print(f"📂 Tải dataset: {csv_file}")

        if not os.path.exists(csv_file):
            print(f"❌ File không tồn tại: {csv_file}")
            return None

        df = pd.read_csv(csv_file).dropna(subset=['label', 'text'])

        print(f"   Tổng mẫu : {len(df):,}")
        print(f"   Phân bố  :")
        for label, count in df['label'].value_counts().items():
            print(f"      • {label}: {count}")

        return df

    # ── Chuẩn bị dataset ──────────────────────────────────────────────
    def prepare_dataset(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        val_size:  float = 0.1,
        max_length: int  = 256,
    ) -> dict:
        """
        Chuẩn bị dataset với smart input extraction + augmentation.
        Split: 70% train / 10% val / 20% test.
        """
        print(f"\n🔄 Chuẩn bị dataset (max_length={max_length})...")

        # ── Label encoding
        unique_labels = sorted(df['label'].unique())
        label_to_id   = {l: i for i, l in enumerate(unique_labels)}
        id_to_label   = {i: l for l, i in label_to_id.items()}
        df = df.copy()
        df['label_id'] = df['label'].map(label_to_id)

        print("   Label mapping:")
        for l, i in label_to_id.items():
            print(f"      {i}: {l}")

        # ── Class weights
        counts  = df['label_id'].value_counts().sort_index()
        weights = torch.tensor(
            [len(df) / (len(unique_labels) * counts[i]) for i in range(len(unique_labels))],
            dtype=torch.float32,
        )
        print(f"\n   Class weights: {[f'{w:.3f}' for w in weights.tolist()]}")

        # ── Train / val / test split
        train_df, test_df = train_test_split(
            df, test_size=test_size, random_state=42, stratify=df['label_id']
        )
        train_df, val_df = train_test_split(
            train_df,
            test_size=val_size / (1 - test_size),
            random_state=42,
            stratify=train_df['label_id'],
        )

        print(f"\n   Split → train={len(train_df)} / val={len(val_df)} / test={len(test_df)}")

        # ── Smart input extraction
        # Train: augment=True để random crop snippet
        # Val/Test: augment=False để kết quả ổn định
        train_df = train_df.copy()
        val_df   = val_df.copy()
        test_df  = test_df.copy()

        train_df['input_text'] = train_df['text'].apply(
            lambda t: extract_smart_input(t, augment=True)
        )
        val_df['input_text']  = val_df['text'].apply(
            lambda t: extract_smart_input(t, augment=False)
        )
        test_df['input_text'] = test_df['text'].apply(
            lambda t: extract_smart_input(t, augment=False)
        )

        # ── Tokenize
        def tokenize(examples):
            return self.tokenizer(
                examples['input_text'],
                padding='max_length',
                truncation=True,
                max_length=max_length,
            )

        def make_hf_dataset(frame: pd.DataFrame) -> Dataset:
            ds = Dataset.from_pandas(frame[['input_text', 'label_id']])
            ds = ds.map(tokenize, batched=True)
            ds = ds.rename_column('label_id', 'labels')
            ds = ds.remove_columns(['input_text'])
            return ds

        print("   🔄 Tokenizing...")
        train_ds = make_hf_dataset(train_df)
        val_ds   = make_hf_dataset(val_df)
        test_ds  = make_hf_dataset(test_df)
        print("   ✅ Dataset sẵn sàng!\n")

        return {
            'train':        train_ds,
            'val':          val_ds,
            'test':         test_ds,
            'label_to_id':  label_to_id,
            'id_to_label':  id_to_label,
            'class_weights': weights,
            'test_df':      test_df,   # giữ lại để debug sau
        }

    # ── Compute metrics ───────────────────────────────────────────────
    @staticmethod
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=1)
        acc = accuracy_score(labels, preds)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, preds, average='weighted', zero_division=0 # average='weighted'
        )
        return {'accuracy': acc, 'precision': precision, 'recall': recall, 'f1': f1}

    # ── Train ─────────────────────────────────────────────────────────
    def train(
        self,
        train_ds,
        val_ds,
        class_weights: torch.Tensor,
        output_dir: str,
        epochs: int     = 5,
        batch_size: int = 8,
        lr: float       = 2e-5,
    ) -> 'WeightedTrainer':
        """
        Train với WeightedTrainer + cosine scheduler + early stopping.

        batch_size=8 thay vì 16 vì chạy CPU RAM hạn chế;
        nếu có GPU tăng lên 16-32 để nhanh hơn.
        """
        print("\n" + "="*70)
        print("🤖 BẮT ĐẦU TRAINING")
        print("="*70)

        os.makedirs(output_dir, exist_ok=True)

        training_args = TrainingArguments(
            output_dir=output_dir,

            # ── Epochs & batch
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,

            # ── LR & scheduler
            learning_rate=lr,
            weight_decay=0.01,
            lr_scheduler_type='cosine',       # cosine tốt hơn linear cho fine-tune
            warmup_ratio=0.1,                 # warmup 10% steps đầu

            # ── Eval & save
            eval_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='f1',
            greater_is_better=True,
            save_total_limit=2,               # Chỉ giữ 2 checkpoint tốt nhất

            # ── Mixed precision (chỉ dùng nếu có GPU)
            fp16=torch.cuda.is_available(),

            # ── Logging
            logging_steps=20,
            logging_dir=os.path.join(output_dir, 'logs'),
            report_to='none',                 # Không cần wandb

            seed=42,
            push_to_hub=False,
        )

        trainer = WeightedTrainer(
            class_weights=class_weights,
            model=self.model,
            args=training_args,
            train_dataset=train_ds,
            eval_dataset=val_ds,
            compute_metrics=self.compute_metrics,
            callbacks=[
                EarlyStoppingCallback(early_stopping_patience=2)
            ],
        )

        print("\n⏳ Training...\n")
        trainer.train()
        print("\n✅ Training xong!")
        return trainer

    # ── Evaluate ──────────────────────────────────────────────────────
    def evaluate(
        self,
        trainer: 'WeightedTrainer',
        test_ds,
        id_to_label: dict,
        output_dir:  str,
    ):
        print("\n" + "="*70)
        print("📊 ĐÁNH GIÁ TRÊN TEST SET")
        print("="*70)

        preds_output = trainer.predict(test_ds)
        pred_ids     = np.argmax(preds_output.predictions, axis=1)
        true_ids     = preds_output.label_ids

        pred_labels = [id_to_label[i] for i in pred_ids]
        true_labels = [id_to_label[i] for i in true_ids]

        label_names = [id_to_label[i] for i in sorted(id_to_label)]

        report = classification_report(
            true_labels, pred_labels,
            labels=label_names,
            digits=4,
            zero_division=0,
        )
        print("\n📋 Classification Report:")
        print(report)

        cm = confusion_matrix(true_labels, pred_labels, labels=label_names)
        print("📊 Confusion Matrix (rows=true, cols=pred):")
        header = ''.join(f"{l[:6]:>8}" for l in label_names)
        print(f"{'':>12}{header}")
        for i, row in enumerate(cm):
            row_str = ''.join(f"{v:>8}" for v in row)
            print(f"{label_names[i][:12]:>12}{row_str}")

        # Lưu report ra file
        report_path = os.path.join(output_dir, 'eval_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=== CLASSIFICATION REPORT ===\n\n")
            f.write(report)
            f.write("\n\n=== CONFUSION MATRIX ===\n")
            f.write(f"Labels: {label_names}\n")
            f.write(str(cm))
        print(f"\n💾 Lưu report: {report_path}")

        # Overall metrics
        acc = accuracy_score(true_labels, pred_labels)
        p, r, f1, _ = precision_recall_fscore_support(
            true_labels, pred_labels, average='weighted', zero_division=0
        )
        print(f"\n📈 Overall:")
        print(f"   Accuracy : {acc:.4f}")
        print(f"   Precision: {p:.4f}")
        print(f"   Recall   : {r:.4f}")
        print(f"   F1       : {f1:.4f}")


# =====================================================================
# MAIN
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description='Train PhoBERT phân loại văn bản')
    parser.add_argument('--csv_file',    default=None,                    help='Path CSV dataset')
    parser.add_argument('--output_dir',  default=None,                    help='Thư mục lưu model')
    parser.add_argument('--epochs',      type=int,   default=5,           help='Số epochs (mặc định 5)')
    parser.add_argument('--batch_size',  type=int,   default=8,           help='Batch size (8 cho CPU, 16-32 cho GPU)')
    parser.add_argument('--lr',          type=float, default=2e-5,        help='Learning rate')
    parser.add_argument('--max_length',  type=int,   default=256,         help='Max token length')
    parser.add_argument('--model_name',  default='vinai/phobert-base',    help='Model HuggingFace')
    args = parser.parse_args()

    # Default paths
    if args.csv_file is None:
        args.csv_file   = os.path.join(ROOT_DIR, 'data', 'processed', 'dataset.csv')
    if args.output_dir is None:
        args.output_dir = os.path.join(ROOT_DIR, 'src', 'models', 'text_classifier', 'phobert_finetuned')

    print("\n" + "="*70)
    print("🚀 PHOBERT TRAINING — PHÂN LOẠI VĂN BẢN HÀNH CHÍNH VIỆT NAM")
    print("="*70)
    print(f"  CSV       : {args.csv_file}")
    print(f"  Output    : {args.output_dir}")
    print(f"  Epochs    : {args.epochs}")
    print(f"  Batch     : {args.batch_size}")
    print(f"  LR        : {args.lr}")
    print(f"  MaxLen    : {args.max_length}")
    print(f"  Model     : {args.model_name}")

    # ── Detect labels
    if not os.path.exists(args.csv_file):
        print(f"❌ CSV không tồn tại: {args.csv_file}")
        sys.exit(1)

    df_temp = pd.read_csv(args.csv_file).dropna(subset=['label', 'text'])
    num_labels = df_temp['label'].nunique()
    print(f"  Labels    : {num_labels} loại")

    # ── Khởi tạo
    trainer_obj = PhoBertTrainer(
        model_name=args.model_name,
        num_labels=num_labels,
    )

    # ── Load data
    df = trainer_obj.load_dataset(args.csv_file)
    if df is None:
        sys.exit(1)

    # ── Chuẩn bị
    ds_dict = trainer_obj.prepare_dataset(
        df,
        max_length=args.max_length,
    )

    # ── Train
    trained = trainer_obj.train(
        train_ds=ds_dict['train'],
        val_ds=ds_dict['val'],
        class_weights=ds_dict['class_weights'],
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
    )

    # ── Evaluate
    trainer_obj.evaluate(
        trainer=trained,
        test_ds=ds_dict['test'],
        id_to_label=ds_dict['id_to_label'],
        output_dir=args.output_dir,
    )

    # ── Lưu model + tokenizer + label mapping
    print(f"\n💾 Lưu model vào: {args.output_dir}")
    trained.model.save_pretrained(args.output_dir)
    trainer_obj.tokenizer.save_pretrained(args.output_dir)

    label_map_path = os.path.join(args.output_dir, 'label_mapping.json')
    with open(label_map_path, 'w', encoding='utf-8') as f:
        json.dump(
            {
                'label_to_id': ds_dict['label_to_id'],
                'id_to_label': {int(k): v for k, v in ds_dict['id_to_label'].items()},
            },
            f, ensure_ascii=False, indent=2,
        )
    print(f"💾 Label mapping : {label_map_path}")

    print("\n" + "="*70)
    print("✅ Hoàn tất! Để dùng model, cập nhật nlp_engine.py:")
    print(f"   PhoBertClassifier(model_path='{args.output_dir}')")
    print("="*70 + "\n")


if __name__ == '__main__':
    main()