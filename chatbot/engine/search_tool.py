# engine/search_tool.py
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()

class OnlineSearchEngine:
    def __init__(self, local_engine):
        self.api_key = os.getenv("TAVILY_API_KEY") 
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self.local_engine = local_engine # Dùng Gemini để tóm tắt

    def search_and_answer(self, user_query, context_info="", target_url=None):
        """
        1. Search Tavily
        2. Đưa kết quả search cho Gemini tóm tắt
        """
        if not self.client:
            yield "❌ Chưa cấu hình Tavily API Key."
            return

        try:
            print(f"[Tavily] Searching: {user_query} | Site: {target_url}")
            
            search_params = {
                "query": user_query,
                "search_depth": "advanced",
                "max_results": 5,
                "include_answer": True
            }
            if target_url:
                search_params["query"] = f"{user_query} site:{target_url}"
            
            search_result = self.client.search(**search_params)
            
            context_text = search_result.get("answer", "")
            results = search_result.get("results", [])
            
            web_content = "\n".join([f"- [{r['title']}]({r['url']}): {r['content'][:300]}..." for r in results])
            
            if not results:
                web_content = "Không tìm thấy thông tin phù hợp trên web."
            
            prompt = f"""
NHIỆM VỤ: Bạn là chuyên gia tư vấn du học. Dữ liệu nội bộ thiếu, đây là thông tin TÌM KIẾM ONLINE từ website: {target_url if target_url else 'Google'}.

CÂU HỎI USER: "{user_query}"
BỐI CẢNH: {context_info}

KẾT QUẢ TÌM KIẾM:
{web_content}

YÊU CẦU:
- Trả lời câu hỏi dựa trên thông tin web vừa tìm được.
- Nếu tìm thấy học phí hoặc yêu cầu đầu vào, hãy ghi rõ.
- Cuối câu trả lời, hãy dẫn nguồn (URL) để user tham khảo.
"""
            for chunk in self.local_engine.generate_filter_stream(prompt):
                yield chunk

        except Exception as e:
            yield f"❌ Lỗi khi tìm kiếm online: {str(e)}"