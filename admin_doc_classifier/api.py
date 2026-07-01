# api.py
import sys
import os
import cv2
import time
import numpy as np
import re
import difflib
import shutil
import tempfile
from database import db_manager 
import asyncpg
from PIL import Image

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(ROOT_DIR)

from src.core.preprocess_image import preprocess_image_pro
from src.utils.image_io import load_image
from paddleocr import PaddleOCR
from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg
from src.core.information_extraction import info_extractor
from src.core.nlp_engine import phobert_engine
from pydantic import BaseModel
from typing import Optional, Any

# =================================================================
# 1. KHỞI TẠO FASTAPI & CORS
# =================================================================
app = FastAPI(title="Classify Doc AI - API Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOADS_DIR = os.path.join(ROOT_DIR, "uploads")
AVATAR_DIR = os.path.join(UPLOADS_DIR, "avatars")
DOCS_DIR = os.path.join(UPLOADS_DIR, "docs")
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")

@app.on_event("startup")
async def startup_event():
    await db_manager.connect()
    await _ensure_delete_requests_table()

@app.on_event("shutdown")
async def shutdown_event():
    await db_manager.disconnect()

async def _ensure_delete_requests_table():
    """Tự động tạo bảng delete_requests nếu chưa tồn tại, kiểm tra bảng documents trước"""
    try:
        async with db_manager.pool.acquire() as connection:
            # 1. Kiểm tra bảng documents có tồn tại không
            table_exists = await connection.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents');"
            )
            if not table_exists:
                # Tạo bảng documents tối giản (nếu chưa có)
                await connection.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        user_id INTEGER,
                        source_file TEXT,
                        file_path TEXT,
                        raw_text TEXT,
                        content TEXT,
                        label TEXT,
                        confidence FLOAT,
                        doc_type TEXT,
                        doc_date TEXT,
                        so_hieu TEXT,
                        noi_ban_hanh TEXT,
                        trich_yeu TEXT,
                        status TEXT DEFAULT 'COMPLETED',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                print("✅ Bảng documents đã được tạo (nếu chưa có).")

            # 2. Tạo bảng document_delete_requests (bỏ khóa ngoại tạm thời để tránh lỗi)
            await connection.execute("""
                CREATE TABLE IF NOT EXISTS document_delete_requests (
                    id SERIAL PRIMARY KEY,
                    doc_id UUID,   -- không khóa ngoại để đảm bảo tạo thành công
                    requested_by INTEGER,
                    reason TEXT,
                    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                    reviewed_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Bảng document_delete_requests sẵn sàng (không ràng buộc khóa ngoại).")
    except Exception as e:
        print(f"⚠️ Lỗi tạo bảng delete_requests: {e}")
        
# =================================================================
# 2. KHỞI TẠO CÁC MÔ HÌNH AI
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
# 3. KHỞI TẠO PHOBERT OCR CORRECTOR
# =================================================================
class OCRCorrector:
    def __init__(self):
        self.common_errors = {
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
            r'\bđị\s+lịm\b': 'đi làm', r'\bđi\s+lịm\b': 'đi làm', r'\bđị\s+làm\b': 'đi làm',
            r'\bChiên\s+thăng\b': 'Chiến thắng', r'\bchiên\s+thăng\b': 'chiến thắng',
            r'\bnghi\s+lễ\b': 'nghỉ lễ', r'\bnghi\s+lê\b': 'nghỉ lễ', r'\bnghĩ\s+lễ\b': 'nghỉ lễ',
            r'\bhoán\s+đối\b': 'hoán đổi', r'\bhợp\s+thuy\s+lý\b': 'hợp lý',
            r'\btố\s+chức\b': 'tổ chức', r'\bnghi,\b': 'nghỉ,',
        }
        self.corrections_made = []
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
        if re.match(r'^\d{1,2}[gh:]\d{2}$', word.lower()): return False
        if '@' in word or '.vn' in word.lower() or '.com' in word.lower(): return False
        if re.match(r'^\d{1,2}[/\-]\d{1,2}[/\-]\d{4}$', word): return False
        if re.match(r'^\d{4}$', word): return False
        if re.match(r'^\d+(/\d+)+', word): return False
        if word.startswith('-') or word.endswith('-'): return False
        if re.search(r'\d', word) and re.search(r'[a-zA-Z]', word): return True
        if re.search(r'[^\w\s]', word, re.UNICODE): return True
        if len(word) == 1 and not word.isdigit() and word.lower() not in ['a', 'o', 'e', 'u', 'i', 'y', 'à', 'á', 'ả', 'ã', 'ạ', 'ơ', 'ở', 'ô', 'ổ', 'ố', 'ỳ', 'ý']: return True
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
                        if highest_similarity > 0.75:
                            words[i] = words[i].replace(clean_word, best_match)
                    except Exception:
                        pass 
            fixed_lines.append(" ".join(words))
        return "\n".join(fixed_lines)

ocr_corrector = OCRCorrector()

# =================================================================
# SCHEMAS (PYDANTIC)
# =================================================================
class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    role: str = "employee" 

class UpdateDocumentRequest(BaseModel):
    docType: str
    soHieu: str
    date: str
    trichYeu: str
    content: str
    noiBanHanh: Optional[str] = ""
    edited_by: Optional[Any] = None  # Chấp nhận cả int lẫn str từ frontend

class UpdateProfileRequest(BaseModel):
    email: str
    full_name: str
    date_of_birth: Optional[str] = None
    phone_number: Optional[str] = None
    gender: str = "Khác"
    address: Optional[str] = None

class UpdatePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class DeleteRequestPayload(BaseModel):
    requested_by: int
    reason: Optional[str] = ""

class ApproveDeletePayload(BaseModel):
    approved_by: int

class RejectDeletePayload(BaseModel):
    rejected_by: int

class AdminUpdateUserRequest(BaseModel):
    fullName: Optional[str] = None
    email: Optional[str] = None
    phoneNumber: Optional[str] = None
    address: Optional[str] = None
    role: str
    requestByRole: str # Role của người đang thao tác

# =================================================================
# ENDPOINTS AUTH
# =================================================================
@app.post("/auth/register")
async def register_api(payload: RegisterRequest):
    try:
        new_user = await db_manager.create_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role=payload.role
        )
        return {"message": "Tạo tài khoản thành công!", "user": dict(new_user)}
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Tên tài khoản hoặc Email đã tồn tại!")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")

@app.post("/auth/login")
async def login_api(payload: LoginRequest):
    user_data = await db_manager.verify_user(username=payload.username, password=payload.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Tài khoản hoặc mật khẩu không chính xác!")
    return {"message": "Đăng nhập thành công!", "user": user_data}

# =================================================================
# ENDPOINTS USER PROFILE
# =================================================================
@app.put("/users/{user_id}/profile")
async def update_profile_endpoint(user_id: int, payload: UpdateProfileRequest):
    try:
        success = await db_manager.update_user_profile(user_id, payload.dict())
        if not success:
            raise HTTPException(status_code=404, detail="Cập nhật hồ sơ thất bại.")
        return {"message": "Cập nhật hồ sơ cá nhân thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users/{user_id}/avatar")
async def upload_avatar_endpoint(user_id: int, file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File tải lên phải là hình ảnh!")
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"avatar_{user_id}_{int(time.time())}{file_extension}"
    file_path = os.path.join(AVATAR_DIR, unique_filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        avatar_url = f"http://localhost:8000/uploads/avatars/{unique_filename}"
        success = await db_manager.update_user_avatar(user_id, avatar_url)
        if not success:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        return {"message": "Cập nhật ảnh đại diện thành công!", "avatar_url": avatar_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi upload: {str(e)}")

@app.put("/users/{user_id}/password")
async def update_password_endpoint(user_id: int, payload: UpdatePasswordRequest):
    try:
        success, message = await db_manager.update_user_password(user_id, payload.current_password, payload.new_password)
        if not success:
            raise HTTPException(status_code=400, detail=message)
        return {"message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =================================================================
# ENDPOINTS DOCUMENTS
# =================================================================
@app.post("/process")
async def process_document_api(file: UploadFile = File(...), user_id: str = Form(None)):
    start_time = time.time()
    
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"doc_{int(time.time())}{file_extension}"
    saved_file_path = os.path.join(DOCS_DIR, unique_filename)
    
    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        document_url = f"http://localhost:8000/uploads/docs/{unique_filename}"
            
        pages = load_image(saved_file_path)
        if not pages:
            raise HTTPException(status_code=400, detail="Không có trang ảnh nào để xử lý.")

        full_document_text = ""

        for page_num, img in enumerate(pages, 1):
            processed_img = preprocess_image_pro(img)
            gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
            
            result = det_model.ocr(processed_img, rec=False)
            boxes = result[0] if result and result[0] else []
            if not boxes: continue

            is_vertical = sum(1 for box in boxes if max(np.linalg.norm(np.array(box)[0] - np.array(box)[3]), np.linalg.norm(np.array(box)[1] - np.array(box)[2])) > max(np.linalg.norm(np.array(box)[0] - np.array(box)[1]), np.linalg.norm(np.array(box)[2] - np.array(box)[3])) * 1.2)
            if is_vertical > len(boxes) * 0.5:
                processed_img = cv2.rotate(processed_img, cv2.ROTATE_90_COUNTERCLOCKWISE)
                gray_processed = cv2.cvtColor(processed_img, cv2.COLOR_BGR2GRAY)
                result = det_model.ocr(processed_img, rec=False)
                boxes = result[0] if result and result[0] else []

            box_heights = []
            for b in boxes:
                pts = np.array(b, dtype=np.float32)
                h = max(np.linalg.norm(pts[0] - pts[3]), np.linalg.norm(pts[1] - pts[2]))
                box_heights.append(h)
            
            median_h = np.median(box_heights) if box_heights else 20
            tolerance = int(median_h * 0.6)
            if tolerance < 5: tolerance = 5
            
            boxes = sorted(boxes, key=lambda b: (int(np.mean([p[1] for p in b]) // tolerance), int(np.mean([p[0] for p in b]))))

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

            results_with_pos = []
            if list_pil_imgs:
                try:
                    batch_texts = rec_model.predict_batch(list_pil_imgs)
                except Exception:
                    batch_texts = [rec_model.predict(img) for img in list_pil_imgs]

                for info, text in zip(valid_boxes_info, batch_texts):
                    if text.strip():
                        results_with_pos.append({"text": text, "y": info["y"], "x": info["x"], "h": info["h"]})

            results_with_pos.sort(key=lambda item: (int(item["y"] // tolerance), item["x"]))
            page_text = ""
            prev_y = -100
            prev_h = 0
            for item in results_with_pos:
                if prev_y == -100: page_text += item["text"]
                else:
                    if (item["y"] - prev_y) < (prev_h * 1.5): page_text += " " + item["text"]
                    else: page_text += "\n" + item["text"]
                prev_y = item["y"]
                prev_h = item["h"]

            full_document_text += page_text + "\n\n"

        corrected_text = ocr_corrector.correct_text(full_document_text)
        extracted_info = info_extractor.extract_all_info(corrected_text)
        phobert_result = phobert_engine.predict(corrected_text)
        
        doc_type = extracted_info.get('loai_van_ban', 'Không xác định')
        doc_date = extracted_info.get('ngay_thang_nam', 'Không xác định')
        label = phobert_result['label']
        confidence = phobert_result['confidence']
        
        document_id = await db_manager.save_document(
            user_id=user_id,
            source_file=file.filename,
            file_path=document_url,
            raw_text=full_document_text,
            content=corrected_text,
            label=label,
            confidence=confidence,
            doc_type=doc_type,
            doc_date=doc_date,
            so_hieu=extracted_info.get('so_hieu', ''),
            noi_ban_hanh=extracted_info.get('thanh_pho', ''),
            trich_yeu=extracted_info.get('trich_yeu', '')
        )
        
        return {
            "id": str(document_id), 
            "fileName": file.filename,
            "filePath": document_url,
            "text": full_document_text, 
            "content": corrected_text,
            "label": label, 
            "confidence": confidence, 
            "docType": doc_type, 
            "date": doc_date,
            "soHieu": extracted_info.get('so_hieu', ''), 
            "trichYeu": extracted_info.get('trich_yeu', ''),
            "noiBanHanh": extracted_info.get('thanh_pho', '')
        }

    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=400, detail="File này đã tồn tại trong hệ thống.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def get_all_documents_endpoint(user_id: int = None, role: str = "employee"):
    """Lấy danh sách văn bản từ DB theo phân quyền, kèm tên người upload cho admin/manager"""
    try:
        async with db_manager.pool.acquire() as connection:
            if role in ['admin', 'manager']:
                query = """
                    SELECT d.id, d.source_file, d.file_path, d.raw_text, d.content, d.label, 
                           d.confidence, d.doc_type, d.doc_date, d.so_hieu, d.noi_ban_hanh, 
                           d.trich_yeu, d.user_id,
                           COALESCE(p.full_name, u.username) as uploader_name
                    FROM documents d
                    LEFT JOIN users u ON d.user_id = u.id
                    LEFT JOIN user_profiles p ON d.user_id = p.user_id
                    ORDER BY d.created_at DESC;
                """
                records = await connection.fetch(query)
            else:
                query = """
                    SELECT d.id, d.source_file, d.file_path, d.raw_text, d.content, d.label, 
                           d.confidence, d.doc_type, d.doc_date, d.so_hieu, d.noi_ban_hanh, 
                           d.trich_yeu, d.user_id, NULL as uploader_name
                    FROM documents d
                    WHERE d.user_id = $1
                    ORDER BY d.created_at DESC;
                """
                records = await connection.fetch(query, user_id)
            
            processed_documents = []
            for r in records:
                processed_documents.append({
                    "id": str(r["id"]),
                    "fileName": r["source_file"] or "",
                    "filePath": r["file_path"] or "",
                    "rawText": r["raw_text"] or "",
                    "content": r["content"] or "",
                    "label": r["label"] or "",
                    "confidence": float(r["confidence"]) if r["confidence"] else 0.0,
                    "docType": r["doc_type"] or "Khác",
                    "date": r["doc_date"] or "Chưa rõ",
                    "soHieu": r["so_hieu"] or "",
                    "noiBanHanh": r["noi_ban_hanh"] or "",
                    "trichYeu": r["trich_yeu"] or "",
                    "user_id": r["user_id"],
                    "uploaderName": r["uploader_name"] or ""
                })
            
            return processed_documents
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải dữ liệu kho lưu trữ: {str(e)}")
    
# =================================================================
# ENDPOINTS YÊU CẦU XÓA — ĐẶT TRƯỚC /{doc_id} ĐỂ TRÁNH CONFLICT ROUTE
# =================================================================

@app.get("/documents/delete-requests")
async def get_delete_requests():
    """Lấy danh sách tất cả yêu cầu xóa (cho manager/admin)"""
    try:
        async with db_manager.pool.acquire() as connection:
            query = """
                SELECT r.id, r.doc_id::text, r.requested_by, r.reason, r.status,
                       r.reviewed_by, r.created_at,
                       COALESCE(p.full_name, u.username) as requester_name
                FROM document_delete_requests r
                LEFT JOIN users u ON r.requested_by = u.id
                LEFT JOIN user_profiles p ON r.requested_by = p.user_id
                ORDER BY r.created_at DESC;
            """
            records = await connection.fetch(query)
            return [
                {
                    "id": r["id"],
                    "doc_id": r["doc_id"],
                    "requested_by": r["requested_by"],
                    "requester_name": r["requester_name"] or f"User #{r['requested_by']}",
                    "reason": r["reason"] or "",
                    "status": r["status"],
                    "reviewed_by": r["reviewed_by"],
                    "created_at": r["created_at"].isoformat() if r["created_at"] else ""
                }
                for r in records
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi tải danh sách yêu cầu: {str(e)}")

@app.post("/documents/delete-requests/{request_id}/approve")
async def approve_delete_request(request_id: int, payload: ApproveDeletePayload):
    """Manager/Admin phê duyệt yêu cầu xóa → xóa văn bản vĩnh viễn"""
    import uuid
    try:
        async with db_manager.pool.acquire() as connection:
            # Lấy thông tin yêu cầu
            req = await connection.fetchrow(
                "SELECT doc_id, status FROM document_delete_requests WHERE id = $1;",
                request_id
            )
            if not req:
                raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
            if req["status"] != "pending":
                raise HTTPException(status_code=400, detail="Yêu cầu này đã được xử lí.")
            
            doc_id = req["doc_id"]
            
            async with connection.transaction():
                # Cập nhật trạng thái yêu cầu
                await connection.execute(
                    """UPDATE document_delete_requests 
                       SET status = 'approved', reviewed_by = $1, updated_at = CURRENT_TIMESTAMP 
                       WHERE id = $2;""",
                    payload.approved_by, request_id
                )
                # Xóa văn bản
                await connection.execute("DELETE FROM documents WHERE id = $1;", doc_id)
        
        return {"message": "Đã phê duyệt và xóa văn bản thành công!", "doc_id": str(doc_id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi phê duyệt: {str(e)}")

@app.post("/documents/delete-requests/{request_id}/reject")
async def reject_delete_request(request_id: int, payload: RejectDeletePayload):
    """Manager/Admin từ chối yêu cầu xóa"""
    try:
        async with db_manager.pool.acquire() as connection:
            req = await connection.fetchrow(
                "SELECT status FROM document_delete_requests WHERE id = $1;",
                request_id
            )
            if not req:
                raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu.")
            if req["status"] != "pending":
                raise HTTPException(status_code=400, detail="Yêu cầu này đã được xử lí.")
            
            await connection.execute(
                """UPDATE document_delete_requests 
                   SET status = 'rejected', reviewed_by = $1, updated_at = CURRENT_TIMESTAMP 
                   WHERE id = $2;""",
                payload.rejected_by, request_id
            )
        return {"message": "Đã từ chối yêu cầu xóa."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi từ chối: {str(e)}")

# =================================================================
# ENDPOINTS /{doc_id} — ĐẶT SAU static routes để tránh conflict
# =================================================================

@app.put("/documents/{doc_id}")
async def update_document_endpoint(doc_id: str, payload: UpdateDocumentRequest):
    if not payload.content or payload.content.strip() == "":
        raise HTTPException(status_code=400, detail="Nội dung văn bản không được để trống!")
    if not payload.trichYeu or payload.trichYeu.strip() == "":
        raise HTTPException(status_code=400, detail="Trích yếu không được để trống!")

    try:
        edited_by_str = str(payload.edited_by) if payload.edited_by is not None else None
        success = await db_manager.update_document_from_archive(
            doc_id=doc_id, data=payload.dict(), edited_by=edited_by_str
        )
        if success:
            return {"message": "Cập nhật dữ liệu tài liệu thành công!"}
        raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu yêu cầu.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật: {str(e)}")

@app.delete("/documents/{doc_id}")
async def delete_document_endpoint(doc_id: str):
    try:
        await db_manager.delete_document(doc_id)
        return {"message": "Đã xóa văn bản vĩnh viễn thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi xóa dữ liệu: {str(e)}")

@app.post("/documents/{doc_id}/request-delete")
async def request_delete_document(doc_id: str, payload: DeleteRequestPayload):
    """Nhân viên gửi yêu cầu xóa văn bản, chờ quản lí phê duyệt"""
    import uuid
    try:
        pg_doc_id = uuid.UUID(doc_id)
        async with db_manager.pool.acquire() as connection:
            existing = await connection.fetchrow(
                "SELECT id FROM document_delete_requests WHERE doc_id = $1 AND status = 'pending';",
                pg_doc_id
            )
            if existing:
                raise HTTPException(status_code=409, detail="Đã có yêu cầu xóa đang chờ xử lí cho văn bản này.")
            await connection.execute(
                """INSERT INTO document_delete_requests (doc_id, requested_by, reason, status)
                   VALUES ($1, $2, $3, 'pending');""",
                pg_doc_id, payload.requested_by, payload.reason or ""
            )
        return {"message": "Đã gửi yêu cầu xóa. Chờ quản lí phê duyệt."}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi gửi yêu cầu: {str(e)}")

# =================================================================
# ENDPOINTS USERS / EMPLOYEES
# =================================================================
@app.get("/users")
async def get_all_employees_endpoint():
    """API lấy danh sách toàn bộ nhân sự chuẩn hóa"""
    try:
        async with db_manager.pool.acquire() as connection:
            query = """
                SELECT 
                    u.id, u.username, u.email, u.role, u.is_active, u.created_at,
                    p.full_name, p.date_of_birth, p.phone_number, p.avatar_url, p.gender, p.address
                FROM users u
                LEFT JOIN user_profiles p ON u.id = p.user_id
                ORDER BY u.id ASC;
            """
            records = await connection.fetch(query)
            
            employee_list = []
            for r in records:
                created_at_str = r["created_at"].strftime("%Y-%m-%d %H:%M:%S") if r["created_at"] else ""
                dob_str = r["date_of_birth"].strftime("%Y-%m-%d") if r["date_of_birth"] else "Chưa cập nhật"
                
                employee_list.append({
                    "id": r["id"],
                    "username": r["username"],
                    "email": r["email"] or "",
                    "role": r["role"] or "employee",
                    "isActive": r["is_active"] if r["is_active"] is not None else True,
                    "createdAt": created_at_str,
                    "fullName": r["full_name"] or r["username"],
                    "dateOfBirth": dob_str,
                    "phoneNumber": r["phone_number"] or "Chưa cập nhật",
                    "avatarUrl": r["avatar_url"] or "",
                    "gender": r["gender"] or "Khác",
                    "address": r["address"] or "Chưa cập nhật"
                })
            return employee_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi kết nối cơ sở dữ liệu: {str(e)}")

@app.put("/admin/users/{target_user_id}")
async def admin_update_user_endpoint(target_user_id: int, payload: AdminUpdateUserRequest):
    """API để Admin/Manager cập nhật thông tin nhân viên"""
    # 1. Chặn bảo mật nếu người gửi không phải Admin hoặc Manager
    if payload.requestByRole not in ['admin', 'manager']:
        raise HTTPException(status_code=403, detail="Bạn không có quyền thực hiện thao tác này.")
    
    try:
        # Gọi hàm xử lý đã viết ở database.py
        await db_manager.admin_update_user(target_user_id, payload.dict(), payload.requestByRole)
        return {"message": "Cập nhật thông tin nhân sự thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/admin/users/{target_user_id}")
async def admin_delete_user_endpoint(target_user_id: int, requesterRole: str):
    """API để Admin xóa nhân sự"""
    if requesterRole != 'admin':
        raise HTTPException(status_code=403, detail="Từ chối truy cập: Chỉ Admin mới có quyền xóa tài khoản.")
    
    try:
        await db_manager.admin_delete_user(target_user_id)
        return {"message": "Xóa nhân viên thành công!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống khi xóa: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)