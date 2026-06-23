import re
from typing import Dict, List, Tuple
from datetime import datetime

class DocumentInfoExtractor:
    """
    Trích xuất thông tin cơ bản từ văn bản OCR tiếng Việt:
    - Ngày tháng năm
    - Loại văn bản
    - Số hiệu
    - Trích yếu (tóm tắt)
    - Nội dung chính
    """
    
    # Định nghĩa các loại văn bản
    DOCUMENT_TYPES = {
        "công_văn": ["công văn", "cong van", "cv"],
        "quyết_định": ["quyết định", "quyet dinh", "qđ", "qd"],
        "thông_báo": ["thông báo", "thong bao", "tb"],
        "giấy_mời": ["giấy mời", "giay moi", "gm", "giấy mời họp", "giay moi hop", "thư mời", "thu moi"],
        "tờ_trình": ["tờ trình", "to trinh", "tt"],
        "báo_cáo": ["báo cáo", "bao cao", "bc"],
        "kế_hoạch": ["kế hoạch", "ke hoach"]
    }

    @staticmethod
    def extract_date(text: str) -> str:
        """
        Trích xuất ngày tháng năm.
        Cập nhật: Bắt thêm lỗi OCR "tháng" -> "thảng", "thạng"...
        """
        lines = text.split('\n')[:15]
        header_text = " ".join(lines)
        
        # Thêm các ký tự dấu vào pattern để bắt được chữ "thảng"
        pattern_vn = r'(?:ngày\s+)?(\d{1,2})\s+th[áaảãạ]\w*\s+(\d{1,2})\s+năm\s+(\d{4})'
        match = re.search(pattern_vn, header_text, re.IGNORECASE)
        if match:
            day, month, year = match.groups()
            return f"{day}/{month}/{year}"
        
        pattern_slash = r'(\d{1,2})/(\d{1,2})/(\d{4})'
        match = re.search(pattern_slash, header_text)
        if match:
            return match.group(0)
            
        pattern_dash = r'(\d{4})-(\d{1,2})-(\d{1,2})'
        match = re.search(pattern_dash, header_text)
        if match:
            year, month, day = match.groups()
            return f"{day}/{month}/{year}"
        
        return "Không xác định"
    
    @staticmethod
    def extract_document_number(text: str) -> str:
        """
        Trích xuất số hiệu văn bản.
        Cập nhật: Cải thiện nhận diện vị trí, lọc tên thành phố/quận, và xử lý nhiều định dạng.
        """
        # Danh sách vị trí (thành phố/quận/phường) để loại bỏ
        location_keywords = [
            "Hà Nội", "Hồ Chí Minh", "TP HCM", "Sài Gòn", "HCM",
            "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bình Dương", "Đồng Nai",
            "Quận 1", "Quận 2", "Quận 3", "Quận 4", "Quận 5", "Quận 6", 
            "Quận 7", "Quận 8", "Quận 9", "Quận 10", "Quận 11", "Quận 12",
            "Quận Bình Thạnh", "Quận Gò Vấp", "Quận Phú Nhuận", "Quận Tân Bình",
            "Phường", "Quận", "Tỉnh"
        ]
        
        lines = text.split('\n')[:20]
        
        for line in lines:
            # Tìm "Số" theo nhiều định dạng: "Số:", "Số ", "số :"
            m = re.search(r'Số\s*[:\s]\s*([^\n]+)', line, re.IGNORECASE)
            if not m:
                continue
                
            raw_str = m.group(1).strip()
            
            # Cắt bỏ nội dung sau "ngày", dấu phẩy hoặc lúc gặp thành phố chính
            # Pattern: cắt tại comma, "ngày", "tháng", "năm" hoặc tên vị trí
            cut_m = re.search(r'(,|\bngày\b|\bth[áaảãạ]\w*\b|\bnăm\b)', raw_str, re.IGNORECASE)
            if cut_m:
                raw_str = raw_str[:cut_m.start()].strip()
            
            # Loại bỏ tên vị trí phổ biến (nếu xuất hiện ở đầu phần còn lại)
            for location in sorted(location_keywords, key=len, reverse=True):
                # Chỉ loại bỏ nếu nó nằm SAU một dấu cách hoặc ở đầu (ngay sau số hiệu)
                location_pattern = rf'(\s+|^){re.escape(location)}(?:\s|,|$)'
                cut_loc = re.search(location_pattern, raw_str, re.IGNORECASE)
                if cut_loc:
                    raw_str = raw_str[:cut_loc.start()].strip()
                    break
            
            # Tách thành các phần
            parts = raw_str.split()
            valid_parts = []
            
            # Xác định điểm dừng: khi gặp từ không hợp lệ liên tục, dừng
            consecutive_invalid = 0
            for p in parts:
                # Kiểm tra xem phần này có chứa số, dấu gạch chéo/ngang, hoặc là mã chữ hợp lệ
                if re.search(r'[0-9\/\-]', p) or p.isupper() or p.lower() in ['qđ', 'ubnd', 'nđ', 'cp', 'tt', 'ct', 'kh', 'stp', 'ths', 'ts']:
                    valid_parts.append(p)
                    consecutive_invalid = 0
                else:
                    # Nếu không hợp lệ, tăng bộ đếm
                    consecutive_invalid += 1
                    # Nếu 2 từ liên tiếp không hợp lệ, dừng (có thể là thành phố)
                    if consecutive_invalid >= 2:
                        break
            
            if valid_parts:
                number_str = " ".join(valid_parts)
                # Loại bỏ khoảng trắng xung quanh /, -
                number_str = re.sub(r'\s*([/\-])\s*', r'\1', number_str)
                # Thay khoảng trắng còn lại bằng / (để kết hợp các phần)
                number_str = re.sub(r'\s+', '/', number_str)
                number_str = number_str.strip('/-.,')
                
                # Đảm bảo có ít nhất một con số hoặc định dạng hợp lệ
                if number_str and len(number_str) > 1 and (re.search(r'\d', number_str) or '/' in number_str):
                    return number_str
        
        return "Không xác định"

    @staticmethod
    def detect_document_type(text: str) -> str:
        """
        Xác định loại văn bản hành chính dựa trên nội dung OCR.

        Thứ tự ưu tiên:
        1. Công văn
        2. Quyết định
        3. Kế hoạch
        4. Báo cáo
        5. Thông báo
        6. Tờ trình
        7. Giấy mời
        """

        if not text:
            return "Không xác định"

        t = text.lower()

        has_kinh_gui = re.search(r'kính\s*gửi', t)
        has_vv = re.search(r'v\s*/?\s*v', t)
        has_ve_viec = re.search(r'về\s+việc', t)

        if has_kinh_gui and (has_vv or has_ve_viec):
            return "Công Văn"

        if re.search(r'^\s*quyết\s+định', t, re.MULTILINE):
            return "Quyết Định"

        if re.search(r'^\s*kế\s+hoạch', t, re.MULTILINE):
            return "Kế Hoạch"

        if re.search(r'^\s*báo\s+cáo', t, re.MULTILINE):
            return "Báo Cáo"

        if re.search(r'^\s*thông\s+báo', t, re.MULTILINE):
            return "Thông Báo"

        if re.search(r'^\s*tờ\s+trình', t, re.MULTILINE):
            return "Tờ Trình"

        if re.search(r'^\s*(giấy\s+mời|thư\s+mời)', t, re.MULTILINE):
            return "Giấy Mời"

        return "Không xác định"

    @staticmethod
    def extract_title(text: str) -> str:
        """
        Trích xuất tiêu đề văn bản.
        Ưu tiên: 1) Dòng bắt đầu với V/v, Về, Chuyên đề, Ban hành (ở đầu dòng)
                 2) Dòng tiếp theo sau loại văn bản (công văn, quyết định, giấy mời, v.v.)
        """
        lines = text.strip().split('\n')
        
        # Cách 1: Tìm dòng **bắt đầu với** V/v, Về, Chuyên đề, Ban hành (ở đầu, không phải giữa câu)
        for line in lines:
            # Match ở đầu dòng (sau whitespace nếu có)
            match = re.search(r'^\s*(?:V/v|Về|Chuyên đề|Ban hành)\s*[:–-]?\s*(.+)', line, re.IGNORECASE)
            if match:
                title = re.sub(r'^0\s+', '', line[match.start():]).strip()
                if title:
                    return title
        
        # Cách 2: Nếu không có V/v, lấy dòng tiếp theo sau loại văn bản (công văn, quyết định, giấy mời, etc.)
        doc_type_idx = -1
        for i, line in enumerate(lines):
            if re.search(r'(công văn|quyết định|thông báo|giấy mời|tờ trình|báo cáo|kế hoạch|giấy mời họp|thư mời)', 
                        line, re.IGNORECASE):
                doc_type_idx = i
                break
        
        if doc_type_idx >= 0:
            # Tìm dòng không rỗng tiếp theo
            for i in range(doc_type_idx + 1, len(lines)):
                title = lines[i].strip()
                # Bỏ số 0 ở đầu nếu có
                title = re.sub(r'^0\s+', '', title)
                
                # Không lấy nếu là dòng chứa "Kính gửi", "Gửi", "Thực hiện" (phần nội dung)
                if title and not re.match(r'^(Kính\s*gửi|Gửi|Thực hiện)', title, re.IGNORECASE):
                    return title
        
        return "Tiêu đề không rõ"

    @staticmethod
    def extract_summary(text: str) -> str:
        """
        Trích xuất trích yếu.
        Cập nhật: Phân biệt "V/v", "Về việc" ngay cả khi bị gộp dòng OCR.
        Giữ lại chữ "Về việc" hoặc "V/v" trong kết quả.
        Cắt bỏ các chức danh lãnh đạo nếu bị dính trên cùng 1 dòng.
        Thiết lập "chốt chặn": Dừng ngay khi bắt gặp phần "Căn cứ", "Kính gửi" để tránh bắt nhầm.
        """
        lines = [l.strip() for l in text.split('\n')[:30] if l.strip()]

        # Các cụm từ báo hiệu đã hết phần trích yếu, bắt đầu vào thân văn bản
        stop_pattern = r'^(C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+|Theo\b|Điều\b|Kính gửi|Gửi\b|1\.|Thực hiện\b|GIÁM\s+ĐỐC|GIÁM\s+ĐÓC|GIẨM\s+ĐỘC|CHỦ\s+TỊCH|TM\.|KT\.|UBND|ỦY\s+BAN)'
        # Mẫu để cắt đuôi nếu chức danh bị dính chung trên 1 dòng
        cut_tail_pattern = r'\b(GIÁM\s+ĐỐC|GIÁM\s+ĐÓC|GIẨM\s+ĐỘC|CHỦ\s+TỊCH|TM\.|KT\.|C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+)\b'

        # ── ƯU TIÊN 1: Tìm cụm "V/v", "Về việc" ──
        for i, line in enumerate(lines):
            # CHỐT CHẶN: Nếu đã vào phần "Căn cứ" hoặc chức danh lãnh đạo đứng đầu dòng -> ngưng tìm Ưu tiên 1
            if re.match(r'^(C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+|Theo\b|GIÁM\s+ĐỐC|GIÁM\s+ĐÓC|CHỦ\s+TỊCH|Kính gửi)', line, re.IGNORECASE):
                break
                
            # Bắt "V/v" và "Về việc" ở bất kỳ đâu trong dòng
            m = re.search(r'\b(V[/\\]v|Về việc)\s*[:–\-]?\s*(.+)', line, re.IGNORECASE)
            
            # "Về", "Ban hành", "Chuyên đề" thì bắt khắt khe hơn
            if not m:
                m = re.search(r'(?:^|(?:QUYẾT ĐỊNH|THÔNG BÁO|TỜ TRÌNH|BÁO CÁO|KẾ HOẠCH|GIẤY MỜI|CÔNG VĂN)\s+)(Về|Chuyên đề|Ban hành)\s*[:–\-]?\s*(.+)', line, re.IGNORECASE)
                
            if m:
                # Lấy lại chữ "Về việc"/"V/v" (m.group(1)) ghép với nội dung đằng sau (m.group(2))
                summary_text = f"{m.group(1)} {m.group(2)}".strip()
                
                # Kiểm tra xem có bị dính chữ "GIÁM ĐỐC" ở cuối dòng không (trị lỗi file 170)
                tail_match = re.search(cut_tail_pattern, summary_text, re.IGNORECASE)
                if tail_match:
                    summary_text = summary_text[:tail_match.start()].strip()
                
                summary_lines = [summary_text]
                
                # Quét tiếp các dòng liền kề sau đó để gom phần còn lại của trích yếu
                for j in range(i + 1, min(i + 7, len(lines))):
                    next_line = lines[j]
                    
                    if re.match(stop_pattern, next_line, re.IGNORECASE):
                        break
                        
                    if re.search(r'(SAO Y|CỘNG HÒA|CỘNG HOÀ|ĐỘC LẬP|Hạnh phúc|CÔNG BẢO)', next_line, re.IGNORECASE):
                        continue
                        
                    if len(next_line) > 2:
                         summary_lines.append(next_line)
                
                return " ".join(summary_lines)

        # ── ƯU TIÊN 2: Nằm sau chữ "QUYẾT ĐỊNH", "THÔNG BÁO"... ──
        doc_type_pattern = r'^(QUYẾT ĐỊNH|THÔNG BÁO|BÁO CÁO|TỜ TRÌNH|KẾ HOẠCH|CHỈ THỊ|GIẤY MỜI|THƯ MỜI)'
        for i, line in enumerate(lines):
            # CHỐT CHẶN tương tự
            if re.match(r'^(C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+|Theo\b|GIÁM\s+ĐỐC|CHỦ\s+TỊCH|Kính gửi)', line, re.IGNORECASE):
                break
                
            match = re.search(doc_type_pattern, line, re.IGNORECASE)
            if match:
                summary_lines = []
                remainder = line[match.end():].strip()
                remainder = re.sub(r'^[:\-\s]+', '', remainder)
                
                if remainder:
                    # Lọc nhiễu chức danh dính trên cùng dòng
                    tail_match = re.search(cut_tail_pattern, remainder, re.IGNORECASE)
                    if tail_match:
                        remainder = remainder[:tail_match.start()].strip()
                    summary_lines.append(remainder)
                
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if len(next_line) < 100 and not re.match(stop_pattern, next_line, re.IGNORECASE):
                        if len(next_line) > 5 and not re.search(r'(SAO Y|CỘNG HÒA|ĐỘC LẬP)', next_line, re.IGNORECASE):
                            summary_lines.append(next_line)
                
                if summary_lines:
                    return " ".join(summary_lines)

        # ── ƯU TIÊN 3: Fallback (Quét vớt) ──
        for line in lines:
            if re.search(r'(SAO Y|CỘNG HÒA|CỘNG HOÀ|ĐỘC LẬP|Hạnh phúc|CÔNG BẢO|THỦ TƯỚNG|BỘ TƯ PHÁP|Số:|tháng|ngày|năm)', line, re.IGNORECASE):
                continue
            if re.match(r'^(C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+|Theo\b|Điều\b|Kính gửi|Thực hiện|GIÁM\s+ĐỐC|GIÁM\s+ĐÓC|GIẨM\s+ĐỘC|CHỦ\s+TỊCH)', line, re.IGNORECASE):
                break 
            if len(line) > 30:
                # Lọc nhiễu chức danh
                tail_match = re.search(cut_tail_pattern, line, re.IGNORECASE)
                if tail_match:
                    return line[:tail_match.start()].strip()
                return line.strip()

        return "Trích yếu không rõ"

    
    @staticmethod
    def extract_main_content(text: str) -> str:
        """
        Trích xuất nội dung chính.
        Ưu tiên: Kính gửi → Mục 1. → Thực hiện → từ dòng 6
        """
        lines = text.strip().split('\n')
        content_start = 0
        
        # Cách 1: Từ "Kính gửi"
        for i, line in enumerate(lines):
            if re.match(r'^Kính\s+gửi', line.strip(), re.IGNORECASE):
                content_start = i
                break
        
        # Cách 2: Từ mục "1."
        if content_start == 0:
            for i, line in enumerate(lines):
                if re.match(r'^\s*1[\.\)]\s+', line.strip()):
                    content_start = i
                    break
        
        # Cách 3: Từ "Thực hiện"
        if content_start == 0:
            for i, line in enumerate(lines):
                if re.match(r'^Thực hiện', line.strip(), re.IGNORECASE):
                    content_start = i
                    break
        
        # Cách 4: Fallback — dòng 6
        if content_start == 0:
            content_start = min(6, len(lines))
        
        # Tìm điểm kết thúc (ký tên/footer)
        content_end = len(lines)
        for i in range(len(lines) - 1, max(content_start, 0), -1):
            line_lower = lines[i].lower().strip()
            # Phát hiện các dòng signature/footer: TM., ký, chủ tịch, giám đốc, nơi nhận, lưu, v.v.
            if re.match(r'^(tm\s|ký\s|chủ tịch|giám đốc|giám ĐÓc|giẩm|trưởng|phó|người ký|ủy quyền|nơi nhận|lưu|tl\.|fax|điện thoại|giam \w|scanned)', line_lower):
                content_end = i
                break
            # Cũng cắt nếu gặp "Căn cứ:" ở đầu dòng (đó là phần lý do, không phải nội dung chính)
            if re.match(r'^(C[ăaâắằảãạấầẩẫậ]+n\s+c[ứuưửữự]+)', line_lower, re.IGNORECASE):
                if i > content_start + 1:
                    content_end = i
                    break
        
        # Lấy nội dung
        content_lines = []
        for i in range(content_start, content_end):
            line = lines[i].strip()
            if line:
                content_lines.append(line)
        
        content = "\n".join(content_lines).strip()
        
        # Loại bỏ header thừa
        content = re.sub(r'^Số\s*[:=]?[^\n]*\n+', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^(CÔNG VĂN|QUYẾT ĐỊNH|THÔNG BÁO|GIẤY MỜI|TỜ TRÌNH|BÁO CÁO|KỂ HOẠCH)[^\n]*\n+', '', content, flags=re.IGNORECASE)
        
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        return content.strip() if content.strip() else "Nội dung không rõ"

    @staticmethod
    def extract_city(text: str) -> str:
        """
        Trích xuất thành phố/nơi ban hành từ văn bản.
        Pattern: "Số: ... Hà Nội, ngày ..." hoặc "Quận X, ngày ..." hoặc "Hà Nội, ngày ..."
        """
        # Danh sách thành phố/tỉnh chính ở Việt Nam
        cities = [
            "Hà Nội", "Hồ Chí Minh", "TP HCM", "Sài Gòn",
            "Đà Nẵng", "Hải Phòng", "Cần Thơ", "Bình Dương",
            "Đồng Nai", "Long An", "Tiền Giang", "Bến Tre",
            "Vĩnh Long", "An Giang", "Kiên Giang", "Cà Mau",
            "Thái Nguyên", "Bắc Kạn", "Cao Bằng", "Lạng Sơn",
            "Tuyên Quang", "Yên Bái", "Sơn La", "Điện Biên",
            "Lai Châu", "Hà Giang", "Phú Thọ", "Vĩnh Phúc",
            "Bắc Ninh", "Bắc Giang", "Hưng Yên", "Hải Dương",
            "Thái Bình", "Nam Định", "Ninh Bình", "Thanh Hóa",
            "Nghệ An", "Hà Tĩnh", "Quảng Bình", "Quảng Trị",
            "Thừa Thiên Huế", "Quảng Nam", "Quảng Ngãi", "Bình Định",
            "Phú Yên", "Khánh Hòa", "Ninh Thuận", "Bình Thuận",
            "Đắk Nông", "Đắk Lắk", "Lâm Đồng", "Tây Ninh",
            "Bình Phước", "Đồng Tháp", "Vũng Tàu", "Bà Rịa",
            "Hậu Giang", "Sóc Trăng", "Bạc Liêu", "Trà Vinh"
        ]
        
        # Tìm dòng chứa "Số:" hoặc dòng có ngày
        lines = text.split('\n')
        for line in lines:
            # Pattern 1: "Số: ... Thành phố/Tỉnh, ngày ..."
            for city in cities:
                if re.search(rf'\b{re.escape(city)}\s*,\s*ngày', line, re.IGNORECASE):
                    return city
                # Hoặc chỉ tìm thành phố trong dòng có "Số:"
                if "Số:" in line and re.search(rf'\b{re.escape(city)}\b', line, re.IGNORECASE):
                    return city
        
        # Pattern 2: Tìm "Quận X, ngày" hoặc "Phường X, ngày"
        for line in lines:
            m = re.search(r'(Quận|Phường)\s+([0-9]+|[A-Z][a-zà-ỿ\s]+)\s*,\s*ngày', line, re.IGNORECASE)
            if m:
                return f"{m.group(1)} {m.group(2)}"
        
        # Pattern 3: Nếu không tìm được từ "Số:", tìm ở bất kỳ đâu trước "ngày"
        for line in lines:
            for city in cities:
                if re.search(rf'{re.escape(city)}\s*,\s*ngày', line, re.IGNORECASE):
                    return city
        
        return "Không xác định"

    @staticmethod
    def extract_all_info(text: str) -> Dict[str, str]:
        """
        Trích xuất tất cả thông tin từ văn bản OCR.
        """
        return {
            "ngay_thang_nam": DocumentInfoExtractor.extract_date(text),
            "loai_van_ban": DocumentInfoExtractor.detect_document_type(text),
            "so_hieu": DocumentInfoExtractor.extract_document_number(text),
            "tieu_de": DocumentInfoExtractor.extract_title(text),
            "trich_yeu": DocumentInfoExtractor.extract_summary(text),
            "noi_dung": DocumentInfoExtractor.extract_main_content(text),
            "thanh_pho": DocumentInfoExtractor.extract_city(text)
        }


# Khởi tạo extractor
info_extractor = DocumentInfoExtractor()