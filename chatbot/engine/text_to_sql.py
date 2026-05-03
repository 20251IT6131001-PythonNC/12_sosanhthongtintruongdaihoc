import g4f
import json
import re

class TextToSQLEngine:
    """Engine chuyển đổi câu hỏi tự nhiên thành SQL query (Đã tối ưu Prompt cho Schema cụ thể + Ngữ cảnh)"""

    def __init__(self, db_helper, local_engine):
        self.db_helper = db_helper
        self.local_engine = local_engine

    def generate_sql(self, user_question, chat_history=[]):
        """
        Tạo câu SQL từ câu hỏi tự nhiên, có sử dụng lịch sử chat để hiểu ngữ cảnh.
        """
        
        valid_countries_str = self.db_helper.get_all_country_names()
        history_str = ""
        if chat_history:
            recent_msgs = chat_history[-30:]
            for msg in recent_msgs:
                role = "User" if msg['role'] == 'user' else "AI"
                content = msg['content']
                if msg['role'] != 'system':
                    history_str += f"{role}: {content}\n"

        # --- 2. ĐỊNH NGHĨA SCHEMA ---
        schema_context = """
### 1. DATABASE SCHEMA (SQLite):

Table: countries
- id (PK)
- code (TEXT): Mã quốc gia (VD: 'US', 'VN', 'UK')
- name (TEXT): Tên tiếng Anh (VD: 'United States', 'Vietnam')
- flag_url (TEXT)

Table: universities
- id (PK)
- name (TEXT): Tên trường
- country_id (FK): Link to countries.id
- state (TEXT): Bang/Tỉnh
- domain (TEXT), website (TEXT)
- num_majors (INTEGER): Số lượng ngành
- tuition_fee_avg (REAL): Học phí trung bình (USD/năm).
- entry_requirements (TEXT): JSON Format. Example: [{"category": "language", "key": "ielts", "value": "6.0"}, {"category": "academic", "key": "GPA", "value": "8.0"}]

Table: scholarships
- id (PK)
- name (TEXT): Tên học bổng
- university_id (FK): Link to universities.id
- value (REAL): Giá trị (USD)
- duration (TEXT), criteria (TEXT)

Table: user_favorites (Bảng phụ - Danh sách yêu thích)
- user_id, university_id

Table: user (Thông tin user)
- uid, email, full_name...
"""

        # --- 3. QUY TẮC NGHIỆP VỤ ---
        rules = """
### 2. QUY TẮC NGHIỆP VỤ & PHÂN TÁCH ĐIỀU KIỆN (BẮT BUỘC):

1. **QUY TẮC NGỮ CẢNH (CONTEXT OVERRIDE):**
   - Lịch sử chat có thể chứa các ràng buộc cũ (ví dụ: User từng hỏi về "Mỹ").
   - **BẮT BUỘC:** Nếu câu hỏi HIỆN TẠI nhắc đến một quốc gia/địa điểm mới (ví dụ: "Pháp", "Đức"), hãy **QUÊN NGAY** địa điểm cũ trong lịch sử. Chỉ query theo địa điểm MỚI.
   - Ví dụ: History="Mỹ", Current="Thế còn Pháp?" -> SQL phải tìm "France", KHÔNG được tìm "United States".
   
2. **QUY TẮC SELECT (QUAN TRỌNG NHẤT - TRÁNH LỖI NULL):**
   - **LUÔN LUÔN DÙNG `SELECT *` (hoặc `SELECT u.*`)**.
   - **TUYỆT ĐỐI KHÔNG** chỉ chọn mỗi cột tên trường (`SELECT name`). 
   - Lý do: Hệ thống cần lấy cả cột `entry_requirements`, `tuition_fee_avg`, `website`... để thực hiện bước Lọc (Filtering) phía sau. Nếu thiếu các cột này, AI sẽ báo lỗi "Dữ liệu null".

3. **TRICK SẮP XẾP ƯU TIÊN DỮ LIỆU ĐỦ (Weighted Sorting):**
   - User muốn các trường có dữ liệu đầy đủ (num_majors, tuition_fee_avg, entry_requirements) phải hiện lên TRƯỚC. Các trường NULL xuống SAU.
   - **CÔNG THỨC ORDER BY BẮT BUỘC:**
     Luôn bắt đầu mệnh đề `ORDER BY` bằng đoạn code sau:
     `CASE WHEN u.entry_requirements IS NOT NULL AND u.tuition_fee_avg IS NOT NULL AND u.num_majors IS NOT NULL THEN 0 ELSE 1 END`
   - Sau đó mới đến tiêu chí của user (VD: Giá rẻ -> `u.tuition_fee_avg ASC`).
   
   -> Ý nghĩa: Nhóm dữ liệu xịn (trả về 0) sẽ xếp trên nhóm thiếu dữ liệu (trả về 1).
4. **LỌC DỮ LIỆU RÁC (DATA CLEANING - QUAN TRỌNG):**
   - Database chứa nhiều dòng là cơ quan hành chính (Académie...) không có dữ liệu tuyển sinh.
   - **BẮT BUỘC:** Luôn thêm điều kiện này vào `WHERE` để chỉ lấy trường có dữ liệu:
     `u.entry_requirements IS NOT NULL AND u.entry_requirements != ''`
   - Nếu User tìm trường rẻ, hãy đảm bảo học phí hợp lệ (tránh các trường null = 0):
     `AND u.tuition_fee_avg IS NOT NULL AND u.tuition_fee_avg > 0`

5. **PHÂN LOẠI ĐIỀU KIỆN (Decompose):**
   - **Hard Filters (Dùng trong WHERE):** + Quốc gia (Mapping: Đức -> Germany, Mỹ -> United States...). Dùng `LIKE`.
     + Bang/Tỉnh.
     + Ngành học (Cột `domain`).
     + Giá/Học phí (Chỉ dùng để sắp xếp `ORDER BY`, hạn chế dùng `<`, `>` trong WHERE nếu không chắc chắn).
   - **Soft Filters (BỎ QUA trong WHERE - Chỉ SELECT * về):** + Tất cả yêu cầu về: Tiếng Anh (IELTS/TOEFL/No certificate), GPA, Sức khỏe, Hồ sơ, Bậc học (Thạc sĩ/Đại học).


6. **QUY TẮC KHÁC:**
   - **Ranking/Top:** Database KHÔNG có cột ranking. Xử lý bằng cách `ORDER BY tuition_fee_avg DESC` (giả định đắt là xịn) hoặc lấy ngẫu nhiên.
   - **Thạc sĩ:** Database không chia bậc học, mặc định coi như có.
   - **Giới hạn:** Luôn `LIMIT 20` để lấy đủ mẫu."""
        # --- 4. VÍ DỤ MẪU ---
        examples = """
**User:** "Tôi muốn học ở Đức, chưa có chứng chỉ tiếng anh, muốn trường rẻ"
**Thinking:**
   - Hard Filters: Quốc gia = 'Germany'.
   - Soft Filters: "Chưa có tiếng anh" -> Bỏ qua trong SQL, để Python lọc cột `entry_requirements`.
   - Ranking: "Trường rẻ" -> `ORDER BY tuition_fee_avg ASC`.
   - **QUAN TRỌNG:** Phải `SELECT *` để lấy dữ liệu requirements.
**SQL:**
```sql
SELECT u.*, c.name as country_name
FROM universities u
JOIN countries c ON u.country_id = c.id
WHERE c.name LIKE '%Germany%'
ORDER BY u.tuition_fee_avg ASC
LIMIT 20;
**User:** "Tìm trường ở Đức giá rẻ"
**Thinking:**
   - Quốc gia: Germany.
   - Giá rẻ: tuition ASC.
   - **Trick Sort:** Ưu tiên trường có đủ data lên trước.
**SQL:**
```sql
SELECT u.*, c.name as country_name
FROM universities u
JOIN countries c ON u.country_id = c.id
WHERE c.name LIKE '%Germany%'
ORDER BY 
  (CASE WHEN u.entry_requirements IS NOT NULL AND u.tuition_fee_avg IS NOT NULL THEN 0 ELSE 1 END) ASC,
  u.tuition_fee_avg ASC
LIMIT 10;
**User:** "Tìm trường ở Mỹ giá rẻ cho người không có IELTS và sức khỏe yếu"
**Thinking (Decompose):**
   - Hard Filters (SQL): Quốc gia = 'United States', Giá rẻ (Order by tuition ASC).
   - Soft Filters (Ignore in SQL): "Không có IELTS", "Sức khỏe yếu". -> Các trường này chứa trong cột `entry_requirements` JSON, SQL không lọc được.
   -> **Action:** Query tất cả trường Mỹ giá rẻ, lấy cột requirements về để Python lọc.
**SQL:**
```sql
SELECT u.name, u.tuition_fee_avg, u.entry_requirements, c.name as country_name
FROM universities u
JOIN countries c ON u.country_id = c.id
WHERE c.name LIKE '%United States%'
ORDER BY u.tuition_fee_avg ASC
LIMIT 20;
User: "Du học Úc ngành IT cần GPA bao nhiêu?" Thinking:

Hard Filters: Quốc gia = 'Australia', Ngành = 'IT' (domain column).

Soft Filters: "GPA bao nhiêu" -> Đây là câu hỏi về requirements. SQL:

SELECT u.name, u.domain, u.entry_requirements
FROM universities u
JOIN countries c ON u.country_id = c.id
WHERE c.name LIKE '%Australia%' AND u.domain LIKE '%IT%'
LIMIT 20;
"""
        # --- 5. GHÉP PROMPT ---
        full_prompt = f"""Bạn là chuyên gia SQL.
        {schema_context} {rules} {examples}
LỊCH SỬ CHAT (Context): {history_str}
CÂU HỎI HIỆN TẠI: "{user_question}"
Yêu cầu:

Phân tích Lịch sử chat để hiểu ngữ cảnh.

KHÔNG trả lời bằng lời văn.

Chỉ trả về JSON format: {{ "sql": "...", "explanation": "..." }}

JSON OUTPUT:"""
        try:
            if not self.local_engine:
                return False, "Gemini Engine chưa sẵn sàng."
            
            result_text = self.local_engine.generate_content(full_prompt)            
            # Clean JSON
            result_text = re.sub(r'```json\s*|\s*```', '', result_text).strip()
            result_text = re.sub(r'```sql\s*|\s*```', '', result_text).strip()
            
            # Fallback: Nếu AI trả về text không phải JSON nhưng có chứ SELECT
            if not result_text.strip().startswith("{") and "SELECT" in result_text.upper():
                sql_match = re.search(r'SELECT.*', result_text, re.DOTALL | re.IGNORECASE)
                if sql_match:
                    return True, {"sql": sql_match.group(0), "explanation": "Generated from raw text"}

            # Parse JSON
            result = json.loads(result_text)
            
            if "sql" not in result:
                return False, "AI không trả về key 'sql' trong JSON."
            
            # Validate an toàn
            sql = result['sql'].strip()
            if not sql.upper().startswith("SELECT"):
                return False, "Chỉ cho phép câu lệnh SELECT."
                
            return True, result

        except json.JSONDecodeError:
            print(f"[TextToSQL Error] Invalid JSON: {result_text}")
            return False, "Lỗi đọc dữ liệu JSON từ AI."
        except Exception as e:
            return False, f"Lỗi: {str(e)}"
