import sqlite3
import json


class DatabaseHelper:
    """Helper class để làm việc với SQLite database"""
   
    def __init__(self, db_path="universities_db.db"):
        """
        Khởi tạo DatabaseHelper
       
        Args:
            db_path: Đường dẫn đến file database
        """
        self.db_path = db_path
        self._init_chat_tables() 

    def _init_chat_tables(self):
        """Tạo bảng lưu lịch sử chat nếu chưa có"""
        sql_sessions = """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            session_id TEXT PRIMARY KEY,
            user_id INTEGER,
            title TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        sql_messages = """
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE
        )
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql_sessions)
            cursor.execute(sql_messages)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Init DB Error: {e}")


    def save_session(self, session_id, user_id, title):
        """Lưu hoặc cập nhật thông tin session"""
        sql = "INSERT OR REPLACE INTO chat_sessions (session_id, user_id, title) VALUES (?, ?, ?)"
        self._execute_non_query(sql, (session_id, user_id, title))

    def save_message(self, session_id, role, content):
        """Lưu tin nhắn mới"""
        sql = "INSERT INTO chat_messages (session_id, role, content) VALUES (?, ?, ?)"
        self._execute_non_query(sql, (session_id, role, content))

    def get_user_sessions(self, user_id):
        """Lấy danh sách các đoạn chat của user"""
        sql = "SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC"
        success, data = self.execute_query(sql, (user_id,))
        return data if success else []

    def get_session_history(self, session_id):
        """Lấy toàn bộ tin nhắn của một session"""
        sql = "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC"
        success, data = self.execute_query(sql, (session_id,))
        return data if success else []

    def delete_session(self, session_id):
        """Xóa session và tin nhắn liên quan"""
        sql = "DELETE FROM chat_sessions WHERE session_id = ?"
        self._execute_non_query(sql, (session_id,))

    def _execute_non_query(self, sql, params=()):
        """Hàm nội bộ để thực thi INSERT, UPDATE, DELETE"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"DB Error: {e}")
            return False

    def get_schema_info(self):
        """
        Lấy thông tin schema của database với mô tả chi tiết
        """
        schema_description = """
# DATABASE SCHEMA - HỆ THỐNG QUẢN LÝ TRƯỜNG ĐẠI HỌC

### 1. DATABASE SCHEMA (SQLite):

**Table: countries** (Danh mục quốc gia)
- `id` (INTEGER, PK): ID quốc gia
- `code` (TEXT): Mã quốc gia (VD: 'US', 'VN', 'FR', 'DE')
- `name` (TEXT): Tên tiếng Anh (VD: 'United States', 'Vietnam', 'France', 'Germany')
- `flag_url` (TEXT): Link ảnh cờ

**Table: universities** (Danh sách trường đại học)
- `id` (INTEGER, PK): ID trường
- `name` (TEXT): Tên trường
- `country_id` (INTEGER, FK): Liên kết với `countries.id`
- `state` (TEXT): Bang hoặc Tỉnh
- `domain` (TEXT): Lĩnh vực đào tạo chính hoặc danh sách ngành (VD: 'Engineering, Business, Arts')
- `website` (TEXT): Trang web chính thức
- `num_majors` (INTEGER): Số lượng ngành đào tạo
- `tuition_fee_avg` (REAL): Học phí trung bình (USD/năm). (Lưu ý: Có thể là NULL hoặc 0 nếu dữ liệu thiếu).
- `entry_requirements` (TEXT): **CẤU TRÚC JSON PHỨC TẠP**.
   - Chứa thông tin về IELTS, GPA, SAT, Essay...
   - Ví dụ: `[{"category": "language", "key": "ielts", "value": "6.5"}, {"category": "academic", "key": "gpa", "value": "8.0"}]`
   - **QUAN TRỌNG:** KHÔNG filter cột này trong SQL (WHERE). Chỉ SELECT nó ra để xử lý sau.

**Table: scholarships** (Học bổng)
- `id` (INTEGER, PK)
- `name` (TEXT): Tên học bổng
- `university_id` (INTEGER, FK): Liên kết với `universities.id`
- `value` (REAL): Giá trị học bổng (USD)
- `duration` (TEXT): Thời hạn (VD: '4 years', '1 semester')
- `criteria` (TEXT): Điều kiện đạt học bổng

**Table: user** (Người dùng hệ thống)
- `uid` (INTEGER, PK): User ID
- `full_name` (TEXT), `email` (TEXT)
- `address` (TEXT), `phone` (TEXT)

**Table: user_favorites** (Danh sách trường yêu thích của User)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK): Liên kết với `user.uid`
- `university_id` (INTEGER, FK): Liên kết với `universities.id`
- `created_at` (TIMESTAMP)

### MỐI QUAN HỆ (RELATIONSHIPS):
1. **Tìm trường theo quốc gia:**
   `JOIN countries c ON u.country_id = c.id`
   
2. **Tìm học bổng của trường:**
   `JOIN scholarships s ON s.university_id = u.id`

3. **Tìm trường yêu thích của User:**
   `JOIN user_favorites uf ON u.id = uf.university_id WHERE uf.user_id = [CURRENT_USER_ID]`


## QUAN HỆ GIỮA CÁC BẢNG:
- universities.country_id → countries.id (Many-to-One)
- scholarships.university_id → universities.id (Many-to-One)
- user_favorites.user_id → user.uid (Many-to-One)
- user_favorites.university_id → universities.id (Many-to-One)




## LƯU Ý KHI TRUY VẤN:
- Để lấy tên quốc gia: JOIN universities với countries
- Để lấy học bổng: JOIN scholarships với universities
- Học phí (tuition_fee_avg) tính theo USD/năm
- entry_requirements chứa text mô tả yêu cầu (có thể dùng LIKE để tìm kiếm)

"""
        return schema_description
   
    def execute_query(self, sql_query, params=()):
        """
        Thực thi câu truy vấn SQL (Cho phép truyền params)
       
        Args:
            sql_query: Câu lệnh SQL
            params: Tuple chứa các tham số (để tránh SQL Injection)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Để trả về kết quả dạng dict
            cursor = conn.cursor()
        
            if not params:
                sql_normalized = sql_query.strip().upper()
                if not sql_normalized.startswith('SELECT'):
                    return False, "⚠️ Chỉ được phép thực hiện câu lệnh SELECT"
           
            cursor.execute(sql_query, params)
            rows = cursor.fetchall()
           
            results = []
            for row in rows:
                results.append(dict(row))
           
            conn.close()
            return True, results
           
        except sqlite3.Error as e:
            return False, f"SQL Error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
   
    def get_sample_data(self, table_name, limit=3):
        """Lấy dữ liệu mẫu từ một bảng"""
        success, data = self.execute_query(f"SELECT * FROM {table_name} LIMIT {limit}")
        if success:
            return data
        return []
   
    def get_statistics(self):
        """Lấy thống kê tổng quan về database"""
        stats = {}
        tables = ['countries', 'universities', 'scholarships', 'user']
        for table in tables:
            success, result = self.execute_query(f"SELECT COUNT(*) as count FROM {table}")
            if success and result:
                stats[table] = result[0]['count']
       
        return stats
    
    def get_all_country_names(self):
        """Lấy danh sách tên tất cả quốc gia đang có trong DB để đưa vào Prompt"""
        sql = "SELECT DISTINCT name FROM countries"
        success, data = self.execute_query(sql)
        if success and data:
            names = [row['name'] for row in data]
            return ", ".join(names)
        return "United States, United Kingdom, Vietnam"