# database.py
import asyncpg
import logging
import bcrypt
import json

# Cấu hình Database
DB_USER = "openpg"
DB_PASSWORD = "openpgpwd"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_DATABASE = "postgres"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"

class DatabaseManager:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Khởi tạo Connection Pool khi ứng dụng Startup"""
        try:
            self.pool = await asyncpg.create_pool(DATABASE_URL)
            print("✅ Kết nối đến Database PostgreSQL thành công!")
        except Exception as e:
            print(f"❌ LỖI KẾT NỐI DATABASE: {e}")
            raise e

    async def disconnect(self):
        """Đóng Pool khi ứng dụng Shutdown"""
        if self.pool:
            await self.pool.close()
            print("🔒 Đã đóng toàn bộ kết nối Database.")

    async def save_document(
        self, 
        user_id, source_file, file_path, raw_text, content, 
        label, confidence, doc_type, doc_date, so_hieu, 
        noi_ban_hanh, trich_yeu
    ):
        """Hàm lưu tài liệu đã gắn kết nối với user_id thực tế từ frontend"""
        pg_user_id = int(user_id) if user_id else None

        async with self.pool.acquire() as connection:
            # 1. Kiểm tra tồn tại bản ghi dựa trên cặp (user_id, source_file)
            if pg_user_id is not None:
                check_query = "SELECT id FROM documents WHERE user_id = $1 AND source_file = $2;"
                doc_record = await connection.fetchrow(check_query, pg_user_id, source_file)
            else:
                check_query = "SELECT id FROM documents WHERE user_id IS NULL AND source_file = $1;"
                doc_record = await connection.fetchrow(check_query, source_file)

            # 2. Nếu đã tồn tại -> UPDATE
            if doc_record:
                document_id = doc_record['id']
                update_query = """
                    UPDATE documents SET 
                        file_path = $1, raw_text = $2, content = $3, label = $4, 
                        confidence = $5, doc_type = $6, doc_date = $7, so_hieu = $8, 
                        noi_ban_hanh = $9, trich_yeu = $10, status = 'COMPLETED', updated_at = CURRENT_TIMESTAMP
                    WHERE id = $11
                    RETURNING id;
                """
                await connection.execute(
                    update_query, file_path, raw_text, content, label, 
                    float(confidence), doc_type, doc_date, so_hieu, noi_ban_hanh, trich_yeu, document_id
                )
                return document_id
                
            # 3. Nếu chưa tồn tại -> INSERT kèm user_id
            else:
                insert_query = """
                    INSERT INTO documents (
                        user_id, source_file, file_path, raw_text, content, 
                        label, confidence, doc_type, doc_date, so_hieu, 
                        noi_ban_hanh, trich_yeu, status
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'COMPLETED')
                    RETURNING id;
                """
                document_id = await connection.fetchval(
                    insert_query, pg_user_id, source_file, file_path, raw_text, content, 
                    label, float(confidence), doc_type, doc_date, so_hieu, noi_ban_hanh, trich_yeu
                )
                return document_id
        
    async def create_user(self, username, email, password, role='employee'):
        """Đăng ký tài liệu người dùng mới, mật khẩu được băm bảo mật"""
        pwd_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')
        
        query = """
            INSERT INTO users (username, email, password_hash, role, is_active)
            VALUES ($1, $2, $3, $4, TRUE)
            RETURNING id, username, email, role;
        """
        async with self.pool.acquire() as connection:
            try:
                user_record = await connection.fetchrow(query, username, email, password_hash, role)
                return user_record
            except Exception as e:
                print(f"❌ Lỗi tạo user: {e}")
                raise e
            
    async def verify_user(self, username, password):
        """Kiểm tra thông tin đăng nhập và kết hợp lấy thông tin chi tiết hồ sơ"""
        query = """
            SELECT 
                u.id, u.username, u.email, u.password_hash, u.role, u.is_active, u.created_at,
                p.full_name, p.date_of_birth, p.phone_number, p.avatar_url, p.gender, p.address
            FROM users u
            LEFT JOIN user_profiles p ON u.id = p.user_id
            WHERE u.username = $1;
        """
        async with self.pool.acquire() as connection:
            user_record = await connection.fetchrow(query, username)
            
            if not user_record:
                return None
                
            stored_hash = user_record['password_hash'].encode('utf-8')
            pwd_bytes = password.encode('utf-8')
            
            if bcrypt.checkpw(pwd_bytes, stored_hash):
                return {
                    "id": user_record['id'],
                    "username": user_record['username'],
                    "email": user_record['email'],
                    "role": user_record['role'],
                    "is_active": user_record['is_active'],
                    "created_at": str(user_record['created_at']),
                    "full_name": user_record['full_name'] or '',
                    "date_of_birth": str(user_record['date_of_birth']) if user_record['date_of_birth'] else '',
                    "phone_number": user_record['phone_number'] or '',
                    "avatar_url": user_record['avatar_url'] or '',
                    "gender": user_record['gender'] or 'Khác',
                    "address": user_record['address'] or ''
                }
            return None

    async def update_user_profile(self, user_id, data):
        """Cập nhật song song cả 2 bảng bằng cách check SELECT trước để tránh hoàn toàn lỗi ON CONFLICT"""
        uid = int(user_id)
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                # 1. Cập nhật email ở bảng core users
                await connection.execute("UPDATE users SET email = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2;", data.get('email'), uid)
                
                dob = None
                if data.get('date_of_birth'):
                    from datetime import datetime
                    try:
                        dob = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
                    except ValueError:
                        dob = None

                # 2. Kiểm tra xem profile của user_id này đã tồn tại trong bảng user_profiles chưa
                check_profile = await connection.fetchrow("SELECT user_id FROM user_profiles WHERE user_id = $1;", uid)
                
                if check_profile:
                    # Nếu đã có bản ghi -> Tiến hành UPDATE
                    update_profile_query = """
                        UPDATE user_profiles SET 
                            full_name = $1,
                            date_of_birth = $2,
                            phone_number = $3,
                            gender = $4,
                            address = $5,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = $6;
                    """
                    await connection.execute(
                        update_profile_query, 
                        data.get('full_name'), dob, data.get('phone_number'), 
                        data.get('gender'), data.get('address'), uid
                    )
                else:
                    # Nếu chưa có bản ghi -> Tiến hành INSERT mới
                    insert_profile_query = """
                        INSERT INTO user_profiles (user_id, full_name, date_of_birth, phone_number, gender, address, updated_at)
                        VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP);
                    """
                    await connection.execute(
                        insert_profile_query, 
                        uid, data.get('full_name'), dob, 
                        data.get('phone_number'), data.get('gender'), data.get('address')
                    )
                return True

    async def update_user_avatar(self, user_id, avatar_url):
        """Cập nhật đường dẫn ảnh đại diện của người dùng (Sử dụng Check-then-Act)"""
        uid = int(user_id)
        async with self.pool.acquire() as connection:
            async with connection.transaction():
                check_profile = await connection.fetchrow("SELECT user_id FROM user_profiles WHERE user_id = $1;", uid)
                
                if check_profile:
                    query = "UPDATE user_profiles SET avatar_url = $1, updated_at = CURRENT_TIMESTAMP WHERE user_id = $2;"
                    await connection.execute(query, avatar_url, uid)
                else:
                    query = "INSERT INTO user_profiles (user_id, avatar_url, updated_at) VALUES ($1, $2, CURRENT_TIMESTAMP);"
                    await connection.execute(query, uid, avatar_url)
                return True

    async def update_user_password(self, user_id, current_password, new_password):
        """Kiểm tra mật khẩu hiện tại và cập nhật mật khẩu băm mới"""
        uid = int(user_id)
        async with self.pool.acquire() as connection:
            user = await connection.fetchrow("SELECT password_hash FROM users WHERE id = $1;", uid)
            if not user:
                return False, "Không tìm thấy người dùng."

            stored_hash = user['password_hash'].encode('utf-8')
            if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
                return False, "Mật khẩu hiện tại không chính xác."

            salt = bcrypt.gensalt()
            new_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt).decode('utf-8')
            
            await connection.execute("UPDATE users SET password_hash = $1, updated_at = CURRENT_TIMESTAMP WHERE id = $2;", new_hash, uid)
            return True, "Đổi mật khẩu thành công!"
            
    async def update_document_from_archive(self, doc_id, data, edited_by=None):
        """Cập nhật chi tiết văn bản từ Kho lưu trữ và ghi nhận Audit Log"""
        import uuid
        pg_doc_id = uuid.UUID(doc_id) if isinstance(doc_id, str) else doc_id
        pg_user_id = int(edited_by) if edited_by else None

        async with self.pool.acquire() as connection:
            async with connection.transaction():
                old_record = await connection.fetchrow("SELECT content, trich_yeu, so_hieu, doc_type, date FROM documents WHERE id = $1;", pg_doc_id)
                
                update_query = """
                    UPDATE documents SET
                        content = $1, trich_yeu = $2, so_hieu = $3, doc_type = $4, doc_date = $5, updated_at = CURRENT_TIMESTAMP
                    WHERE id = $6;
                """
                await connection.execute(
                    update_query, 
                    data.get('content'), data.get('trichYeu'), data.get('soHieu'), 
                    data.get('docType'), data.get('date'), pg_doc_id
                )

                if old_record:
                    old_values = json.dumps(dict(old_record), ensure_ascii=False)
                    new_values = json.dumps({
                        "content": data.get('content'), "trich_yeu": data.get('trichYeu'),
                        "so_hieu": data.get('soHieu'), "doc_type": data.get('docType'), "date": data.get('date')
                    }, ensure_ascii=False)

                    log_query = """
                        INSERT INTO document_audit_logs (document_id, edited_by, old_values, new_values)
                        VALUES ($1, $2, $3, $4);
                    """
                    await connection.execute(log_query, pg_doc_id, pg_user_id, old_values, new_values)
                
                return True

    async def delete_document(self, doc_id):
        """Xóa vĩnh viễn tài liệu khỏi hệ thống"""
        import uuid
        pg_doc_id = uuid.UUID(doc_id) if isinstance(doc_id, str) else doc_id
        
        query = "DELETE FROM documents WHERE id = $1;"
        async with self.pool.acquire() as connection:
            await connection.execute(query, pg_doc_id)
            return True

db_manager = DatabaseManager()