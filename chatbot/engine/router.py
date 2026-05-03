# engine/router.py
import re

class IntentRouter:
    """Phân loại ý định người dùng: DOMAIN (Du học) hay CHITCHAT (Xã giao)"""
    
    def __init__(self):
        self.domain_keywords = [
            'trường', 'đại học', 'du học', 'học phí', 'học bổng', 
            'ngành', 'gpa', 'ielts', 'toefl', 'sat', 'quốc gia', 
            'mỹ', 'anh', 'úc', 'canada', 'top', 'xếp hạng', 
            'điều kiện', 'hồ sơ', 'visa', 'bang', 'tỉnh',
            'rẻ nhất', 'đắt nhất', 'so sánh', 'tìm'
        ]
        
    def classify(self, text):
        """
        Trả về: 'DOMAIN' hoặc 'CHITCHAT'
        """
        text_lower = text.lower()
        
        for kw in self.domain_keywords:
            if kw in text_lower:
                return 'DOMAIN'
        
        if len(text.split()) <= 2 and "trường" not in text_lower:
            return 'CHITCHAT'
            
        return 'CHITCHAT'