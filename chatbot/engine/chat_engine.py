import g4f
import json
import tkinter as tk
from .database_helper import DatabaseHelper
from .text_to_sql import TextToSQLEngine
from .router import IntentRouter          
from .local_chitchat import LocalChitchatEngine 
from .search_tool import OnlineSearchEngine

class ChatEngine:
    """Engine điều phối chính: Router -> Local LLM (Chitchat) hoặc Online LLM (DB)"""
    
    def __init__(self, system_prompt, db_path="universities_db.db", local_engine=None):
        self.system_prompt = system_prompt
        self.chat_history = [{"role": "system", "content": system_prompt}]
        
        self.local_engine = local_engine
        
        self.db_helper = DatabaseHelper(db_path)
        self.text_to_sql = TextToSQLEngine(self.db_helper, self.local_engine)
        
        self.router = IntentRouter()
        
        self.search_engine = OnlineSearchEngine(local_engine)   
        if not self.local_engine:
            print("⚠️ Cảnh báo: Chitchat Engine chưa được truyền vào hoặc khởi tạo thất bại.")

    def _needs_database_query(self, user_text):
        return True 

    def ask_stream(self, user_text, output_widget, on_response_start, status_callback, stop_event):
        try:
            intent = self.router.classify(user_text)
            print(f"[ROUTER] User Input: '{user_text}' -> Intent: {intent}")

            # =================================================================
            # TRƯỜNG HỢP 1: CHITCHAT
            # =================================================================
            if intent == 'CHITCHAT':
                output_widget.after(0, on_response_start)
                if self.local_engine:
                    for chunk in self.local_engine.generate_response_stream(user_text):
                        if stop_event.is_set():
                            self._handle_cancel(output_widget, status_callback)
                            return
                        output_widget.config(state="normal")
                        output_widget.insert(tk.END, chunk, "assistant_msg")
                        output_widget.config(state="disabled")
                        output_widget.see("end")
                else:
                    output_widget.config(state="normal")
                    output_widget.insert(tk.END, "Hệ thống đang khởi động...", "assistant_msg")
                    output_widget.config(state="disabled")
                
                self._finalize_ui(output_widget, status_callback)
                return

            # =================================================================
            # TRƯỜNG HỢP 2: DOMAIN (BROAD SEARCH + LLM FILTER)
            # =================================================================
            
            self.chat_history.append({"role": "user", "content": user_text})
            
            db_data = None
            
            history_context = self.chat_history[:-1]
            success, sql_result = self.text_to_sql.generate_sql(user_text, history_context)
            
            if stop_event.is_set(): 
                self._handle_cancel(output_widget, status_callback)
                return 
            status_callback(True)
            if success:
                sql_query = sql_result['sql']
                success_db, query_result = self.db_helper.execute_query(sql_query)
                
                if success_db:
                    db_data = query_result
                    print(f"[DEBUG] SQL Broad Search Executed: {sql_query}")
                    print(f"[DEBUG] Found {len(db_data)} candidates.")
            
            if stop_event.is_set(): 
                self._handle_cancel(output_widget, status_callback)
                return

            is_data_poor = False
            missing_info_msg = ""
            target_website = None
            
            if db_data and len(db_data) > 0:
                top_records = db_data[:5]
                null_count = 0
                
                first_row = top_records[0]
                is_scholarship_query = 'criteria' in first_row or 'value' in first_row
                
                for r in top_records:
                    if not target_website:
                        target_website = r.get('website') or r.get('url') or r.get('link')

                    if is_scholarship_query:
                        if not r.get('criteria') and not r.get('value'):
                            null_count += 1
                    else:
                        if not r.get('entry_requirements') or not r.get('tuition_fee_avg'):
                            null_count += 1
                
                if null_count >= len(top_records) / 2:
                    is_data_poor = True
            else:
                is_data_poor = True
                missing_info_msg = "\n\n⚠️ Không tìm thấy dữ liệu trong Database."

            if is_data_poor:
                found_schools_context = ""
                if db_data:
                    names = [r['name'] for r in db_data[:3]] 
                    found_schools_context = f"Các trường đang được thảo luận: {', '.join(names)}"
                
                final_prompt = f"""
TÌNH HUỐNG: User hỏi "{user_text}".
Hệ thống Database KHÔNG CÓ dữ liệu chi tiết (Học bổng/Học phí bị NULL) cho câu hỏi này.

DỮ LIỆU HIỆN CÓ:
{found_schools_context}

NHIỆM VỤ:
1. Thành thật xin lỗi user vì database nội bộ chưa cập nhật thông tin chi tiết về vấn đề họ hỏi.
2. **TUYỆT ĐỐI KHÔNG** bịa ra các placeholder như "[Tên trường 1]", "[Website]". Nếu không biết tên trường, đừng liệt kê.
3. Nếu có tên trường trong "DỮ LIỆU HIỆN CÓ", hãy nhắc lại tên các trường đó và nói rằng thông tin học bổng của chúng chưa có.
4. Mời user bấm nút "Tìm kiếm Online" bên dưới để tra cứu.
"""
            else:
                final_prompt = f"""
NHIỆM VỤ: Bạn là Chuyên gia Tư vấn Du học. Hãy xử lý dựa trên MỤC ĐÍCH CÂU HỎI.

1. YÊU CẦU CỦA NGƯỜI DÙNG: "{user_text}"
   (Lưu ý các từ khóa: không có tiếng anh, sức khỏe, GPA thấp...)

2. CẤU TRÚC DỮ LIỆU JSON (Cột entry_requirements):
   Dữ liệu là danh sách các object: `[{{"category": "...", "key": "...", "value": "..."}}]`
   - **Tiếng Anh**: Tìm object có `key` chứa "IELTS", "TOEFL".
   - **Học thuật**: Tìm object có `key` chứa "GPA", "SAT".
   - **Khác**: Tìm `key` chứa "Health", "Interview".
   
3. QUY TẮC XỬ LÝ (LOGIC RẼ NHÁNH):
🔹 **NHÁNH 1: TRA CỨU THÔNG TIN (Info Retrieval)**
   - Dấu hiệu: User hỏi "Học phí là bao nhiêu?", "Trường có học bổng không?", "Yêu cầu là gì?".
   - **HÀNH ĐỘNG:**
     + Đọc JSON và TRÍCH XUẤT thông tin chính xác.
     + **TUYỆT ĐỐI KHÔNG LOẠI BỎ** trường chỉ vì yêu cầu cao. (VD: Trường cần IELTS 7.0, cứ báo là cần 7.0, đừng tự ý nói user không đủ điều kiện nếu user chưa khai hồ sơ).
     + Trình bày rõ: Học phí ($...), Yêu cầu (IELTS..., GPA...), Học bổng (nếu có).

   🔹 **NHÁNH 2: TƯ VẤN HỒ SƠ (Strict Validator)**
   - Dấu hiệu: User khai "Tôi không có tiếng Anh", "GPA thấp", "Tôi có đủ điều kiện không?".
   - **HÀNH ĐỘNG:**
     + Lúc này mới áp dụng **LUẬT LOẠI TRỪ**: So sánh hồ sơ user với JSON.
     + Nếu User "không có tiếng Anh" mà JSON đòi IELTS -> **LOẠI** (Hoặc cảnh báo đỏ).
     QUY TẮC SÀNG LỌC KHẮC KHIỆT (BẮT BUỘC TUÂN THỦ):

   🛑 **LUẬT LOẠI TRỪ VỀ TIẾNG ANH (NGHIÊM CẤM VI PHẠM):**
   - Hãy quét cột `entry_requirements` (JSON) của từng trường.
   - Nếu tìm thấy các từ khóa: `IELTS`, `TOEFL`, `TOEIC`, `CEFR`, `Level`, `B1`, `B2`, `C1`, `English test`.
   - **SO SÁNH:**
     + Nếu JSON yêu cầu: "C1", "B2", "IELTS 6.0", "TOEIC"...
     + VÀ User: "Không có chứng chỉ".
     + **KẾT LUẬN:** -> **LOẠI NGAY LẬP TỨC**. Không được recommend với lý do "có thể nợ" hay "học tiếng sau".
     + **NGOẠI LỆ DUY NHẤT:** Chỉ giữ lại nếu JSON ghi rõ: "No certificate required", "ESL available", "Placement test included" (Có bài thi xếp lớp nội bộ).

   🛑 **LUẬT VỀ DỮ LIỆU:**
   - Chỉ trả lời dựa trên thông tin có trong JSON. Không được đoán.


4. DANH SÁCH ỨNG VIÊN (Dữ liệu thô):
{self._format_db_data(db_data)}

5. HƯỚNG DẪN ĐỌC JSON & SUY LUẬN (QUAN TRỌNG):
   - **Xử lý mâu thuẫn Tiếng Anh:**
     + Nếu JSON có key `ielts`/`toefl`/`level` (VD: "B2", "6.5") -> Đây là **TRÌNH ĐỘ BẮT BUỘC**.
     + Nếu JSON đồng thời có `application_steps` chứa từ khóa "test", "exam", "kiểm tra" -> Có nghĩa là: **"Yêu cầu trình độ [Level] và sẽ được kiểm tra qua bài test đầu vào"**.
     + **Hành động:** Đừng nói là "Không cần chứng chỉ" một cách quá đơn giản. Hãy nói: "Yêu cầu trình độ tương đương [Level] (VD: B2), nhưng trường có tổ chức thi kiểm tra đầu vào thay thế chứng chỉ."
   
   - **Xử lý GPA/Học lực:**
     + Nếu JSON ghi "xét học bạ", "phỏng vấn động lực" -> Cơ hội tốt cho GPA không quá cao.
     + Nếu JSON ghi "concours", "competitive exam", "xuất sắc" -> Cảnh báo user đây là trường khó vào.

6. HƯỚNG DẪN XỬ LÝ LOGIC (STEP-BY-STEP):
   - **Bước 1**: Với mỗi trường, đọc kỹ JSON `entry_requirements`.
   - **Bước 2 (Match)**: 
     - Nếu User nói "Không có IELTS": Kiểm tra xem trường có yêu cầu IELTS bắt buộc không? Hay có ghi "No IELTS required" / "ESL available"? -> Nếu bắt buộc IELTS cao thì LOẠI.
     - Nếu User nói "Thể lực yếu": Kiểm tra xem có yêu cầu "Health Check" hay "Physical Test" khắt khe không? (Thường các trường quân đội/thể thao mới cần).
   - **Bước 3**: Chọn ra các trường phù hợp nhất.

7. ĐẦU RA:
   - Chỉ liệt kê trường phù hợp.
   - Format đẹp, dùng emoji.
   - Nếu User không có chứng chỉ, hãy ưu tiên các trường có "test/exam" hoặc "phỏng vấn" trong quy trình.
   - Dùng emoji ✅ ⚠️ để đánh dấu điểm thuận lợi/bất lợi.
   - Giải thích rõ ràng: "Dù trường cho nộp hồ sơ, bạn vẫn cần năng lực tiếng Anh mức [Level] để vượt qua bài test."
"""

            stream = self.local_engine.generate_filter_stream(final_prompt)                
            full_reply = ""
            first_chunk = True
            
            for chunk_text in stream:
                if stop_event.is_set():
                    self._handle_cancel(output_widget, status_callback)
                    return

                if first_chunk:
                    output_widget.after(0, on_response_start)
                    first_chunk = False
                
                full_reply += chunk_text
                output_widget.config(state="normal")
                output_widget.insert(tk.END, chunk_text, "assistant_msg")
                output_widget.config(state="disabled")
                output_widget.see("end")

            # Cập nhật câu trả lời vào history
            self.chat_history.append({"role": "assistant", "content": full_reply})
            self._finalize_ui(output_widget, status_callback)
            if is_data_poor:
                signal = "<<SHOW_WEB_SEARCH_BUTTON>>"
                if target_website:
                    signal = f"<<SHOW_WEB_SEARCH_BUTTON|{target_website}>>"
                
                output_widget.config(state="normal")
                output_widget.insert(tk.END, signal) 
                output_widget.config(state="disabled")
                
        except Exception as e:
            if not stop_event.is_set():
                output_widget.config(state="normal")
                output_widget.insert("end", f"\n❌ Lỗi: {e}\n\n", "error")
                output_widget.config(state="disabled")
            status_callback(False)
            
    def perform_online_search(self, user_text, output_widget, stop_event, specific_website=None):
        search_query = user_text
        
        if specific_website:
            search_query = "Tuition fees, admission requirements, master programs"
            
            output_widget.config(state="normal")
            output_widget.insert(tk.END, f"\n🎯 Đang quét trực tiếp website trường: {specific_website}...\n", "status_msg")
            output_widget.config(state="disabled")
        else:
            search_query = user_text
            output_widget.config(state="normal")
            output_widget.insert(tk.END, "\n🔍 Đang tìm kiếm trên Google/Tavily...\n", "status_msg")
            output_widget.config(state="disabled")

        output_widget.see("end")

        try:
            for chunk in self.search_engine.search_and_answer(
                user_query=search_query, 
                context_info=f"Website: {specific_website}",
                target_url=specific_website  
            ):
                if stop_event.is_set(): break
                yield chunk
        except Exception as e:
            yield f"\n❌ Lỗi: {e}"

    def _finalize_ui(self, output_widget, status_callback):
        output_widget.config(state="normal")
        output_widget.insert(tk.END, "\n\n")
        output_widget.config(state="disabled")
        status_callback(False)

    def _handle_cancel(self, output_widget, status_callback):
        output_widget.config(state="normal")
        output_widget.insert(tk.END, "\n⛔ [Đã dừng bởi người dùng]\n\n", "error")
        output_widget.config(state="disabled")
        output_widget.see("end")
        status_callback(False)

    def _format_db_data(self, data):
        """Format dữ liệu dạng JSON string để AI dễ đọc cấu trúc"""
        if not data:
            return "Không có dữ liệu"
        
        max_records = 7
        limited_data = data[:max_records]
        
        result = []
        for i, record in enumerate(limited_data, 1):
            row_str = json.dumps(record, ensure_ascii=False)
            result.append(f"Candidate #{i}: {row_str}")
        
        return "\n".join(result)

    def clear_history(self, system_prompt):
        self.chat_history = [{"role": "system", "content": system_prompt}]