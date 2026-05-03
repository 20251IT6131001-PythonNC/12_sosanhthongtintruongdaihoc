"""
Chatbot Engine — full 1-1 port of /chatbot with English prompts.
Adapted for MySQL + google.genai SDK.

Architecture (identical to /chatbot flow):
  1. _IntentRouter       — keyword classification: DOMAIN vs CHITCHAT
  2. _TextToSQLEngine    — Gemini generates MySQL SQL from natural language + schema + history
  3. execute_query       — safe MySQL execution (SELECT-only guard)
  4. _check_data_quality — detect NULL-heavy results -> is_data_poor flag
  5. 2-branch prompt     — BRANCH 1: Info Retrieval | BRANCH 2: Profile Validation (Strict)
  6. process()           — sync entry point (returns full string)
  7. process_stream()    — generator yielding SSE text chunks + optional <<ONLINE_SEARCH|query>> signal
"""

from __future__ import annotations

import json
import re
import time
from typing import Dict, Generator, List, Optional, Tuple

from app.database import execute_query
from app.utils.prompts import (
    CHITCHAT_PROMPT    as _CHITCHAT_PROMPT,
    DOMAIN_PROMPT_POOR as _DOMAIN_PROMPT_POOR,
    DOMAIN_PROMPT_RICH as _DOMAIN_PROMPT_RICH,
    SCHEMA_CONTEXT     as _SCHEMA_CONTEXT,
    SQL_EXAMPLES       as _SQL_EXAMPLES,
    SQL_RULES          as _SQL_RULES,
)

# ---------------------------------------------------------------------------
# Intent Router (port of /chatbot/engine/router.py — extended)
# ---------------------------------------------------------------------------

class _IntentRouter:
    _DOMAIN_KEYWORDS = [
        # Vietnamese without diacritics
        'truong', 'dai hoc', 'du hoc', 'hoc phi', 'hoc bong',
        'nganh', 'gpa', 'ielts', 'toefl', 'sat', 'gre', 'gmat',
        'quoc gia', 'my', 'anh', 'uc', 'canada', 'nhat', 'han',
        'top', 'xep hang', 'dieu kien', 'ho so',
        're nhat', 'dat nhat', 'so sanh', 'tim', 'gioi thieu',
        'chau', 'chi phi', 'sinh vien', 'nhap hoc',
        'goi y', 'de xuat', 'phu hop', 'phu hợp', 'profile',
        # Vietnamese with diacritics
        'trường', 'đại học', 'du học', 'học phí', 'học bổng',
        'ngành', 'quốc gia', 'mỹ', 'úc', 'nhật', 'hàn',
        'xếp hạng', 'điều kiện', 'hồ sơ',
        'rẻ nhất', 'đắt nhất', 'so sánh', 'tìm', 'giới thiệu',
        'châu', 'chi phí', 'sinh viên', 'nhập học',
        'gợi ý', 'đề xuất', 'phù hợp', 'hồ sơ của tôi',
        # English
        'university', 'universities', 'college', 'tuition', 'scholarship',
        'fee', 'requirement', 'admission', 'apply', 'campus', 'degree',
        'compare', 'best', 'cheapest', 'major', 'program', 'ranking',
        'study abroad', 'international', 'enroll', 'graduate',
        'undergraduate', 'postgraduate', 'master', 'bachelor',
        'accredit', 'eligible', 'certificate', 'accept',
        'suggest', 'recommend', 'suitable', 'match', 'fit my',
        'my profile', 'my score', 'my gpa', 'my ielts', 'my sat',
    ]

    def classify(self, text: str) -> str:
        import re as _re
        tl = text.lower()
        for kw in self._DOMAIN_KEYWORDS:
            if len(kw) <= 3:
                # Short keywords (country codes like 'my', 'uc', 'han', 'anh')
                # must match as whole words to avoid false positives
                # e.g. 'han' in 'thank' should NOT trigger DOMAIN
                if _re.search(r'\b' + _re.escape(kw) + r'\b', tl):
                    return 'DOMAIN'
            else:
                if kw in tl:
                    return 'DOMAIN'
        if len(text.split()) <= 3:
            return 'CHITCHAT'
        return 'CHITCHAT'


# ---------------------------------------------------------------------------
# Text-to-SQL Engine (port of /chatbot/engine/text_to_sql.py)
# ---------------------------------------------------------------------------

class _TextToSQLEngine:
    def __init__(self, gemini_caller):
        self._call = gemini_caller

    def generate(
        self,
        question: str,
        history: List[Dict],
        user_profile: Optional[Dict] = None,
        history_summary: str = "",
    ) -> Tuple[bool, str]:
        """Returns (success: bool, sql: str)."""
        history_str = ""
        # When a summary is available, prepend it and only use last 5 messages
        if history_summary:
            history_str = f"[Earlier conversation summary]: {history_summary}\n"
        limit = 5 if history_summary else 10
        for msg in history[-limit:]:
            role = "User" if msg.get("role") == "user" else "AI"
            history_str += f"{role}: {msg.get('content', '')[:200]}\n"

        profile_hint = ""
        if user_profile:
            parts = []
            for col in ("ielts", "toefl", "gpa", "sat", "gre", "gmat", "act"):
                val = user_profile.get(col)
                if val is not None:
                    parts.append(f"{col.upper()}={val}")
            if parts:
                profile_hint = f"\nUSER PROFILE: {', '.join(parts)}\n"

        prompt = (
            "You are a MySQL expert writing queries for a university study-abroad advisory system.\n"
            + _SCHEMA_CONTEXT
            + _SQL_RULES
            + _SQL_EXAMPLES
            + profile_hint
            + f"\nCONVERSATION HISTORY (context):\n{history_str}\n"
            + f'CURRENT QUESTION: "{question}"\n'
            + 'Return ONLY valid JSON, NO markdown:\n'
        )

        raw = self._call(prompt)
        if not raw:
            return False, ""

        raw = re.sub(r"```(?:json|sql)?\s*|\s*```", "", raw).strip()

        try:
            data = json.loads(raw)
            sql = data.get("sql", "").strip()
            if sql:
                return True, sql
        except (json.JSONDecodeError, AttributeError):
            m = re.search(r'"sql"\s*:\s*"(.*?)"(?:\s*,|\s*})', raw, re.DOTALL)
            if m:
                return True, m.group(1).replace('\\"', '"')

        return False, ""


# ---------------------------------------------------------------------------
# Main ChatbotEngine
# ---------------------------------------------------------------------------

class ChatbotEngine:
    """
    Full 1-1 port of /chatbot with English prompts, adapted for MySQL + REST API.

    Public methods:
      process(message, history)        -> str  (sync, full response)
      process_stream(message, history) -> Generator[str]  (SSE chunks)
                                         Last chunk may be "<<ONLINE_SEARCH|query>>" signal.
    """

    def __init__(self, gemini_key: Optional[str] = None, tavily_key: Optional[str] = None):
        self._client = None
        self._model_name: Optional[str] = None
        self._model = False
        self._tavily_key = tavily_key
        self._rag = None  # RagEngine instance (None if chromadb not installed)

        self._router = _IntentRouter()
        self._sql_engine: Optional[_TextToSQLEngine] = None

        if gemini_key:
            self._init_gemini(gemini_key)

    # ------------------------------------------------------------------
    # Gemini setup
    # ------------------------------------------------------------------

    def _init_gemini(self, api_key: str) -> None:
        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            self._model_name = "models/gemini-2.5-flash"
            self._model = True
            self._sql_engine = _TextToSQLEngine(self._call_gemini)
            # Init RAG engine (graceful — won't crash if chromadb not installed)
            try:
                from app.utils.rag_engine import RagEngine
                self._rag = RagEngine(gemini_key=api_key)
            except Exception as rag_exc:
                print(f"[Chatbot] RAG init failed (non-fatal): {rag_exc}")
                self._rag = None
            print("[Chatbot] Gemini 2.5 Flash ready.")
        except Exception as exc:
            print(f"[Chatbot] Gemini init failed: {exc}")
            self._model = False

    def _call_gemini(self, prompt: str) -> Optional[str]:
        """Non-streaming Gemini call — used for SQL generation. Retries on 503."""
        if not self._model:
            return None
        from google.genai import types
        last_exc = None
        for attempt in range(3):
            try:
                resp = self._client.models.generate_content(
                    model=self._model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=2048),
                )
                return resp.text
            except Exception as exc:
                last_exc = exc
                if '503' in str(exc) or 'UNAVAILABLE' in str(exc).upper():
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"[Chatbot] Gemini 503 — retrying in {wait}s (attempt {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    break
        print(f"[Chatbot] Gemini call error: {last_exc}")
        return None

    # ------------------------------------------------------------------
    # History summarization
    # ------------------------------------------------------------------

    def _summarize_history(self, history: List[Dict]) -> str:
        """
        Use Gemini (non-streaming) to compress older chat messages into a brief
        3-5 sentence summary.  Called from chatbot.py after 10+ messages.
        """
        if not history or not self._model:
            return ""
        lines = []
        for msg in history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {msg.get('content', '')[:300]}")
        history_text = "\n".join(lines)
        prompt = (
            "Summarize the following study-abroad advisory conversation in 3-5 concise sentences. "
            "Focus on: universities and countries discussed, user scores/profile mentioned, "
            "key requirements or concerns raised, and any conclusions reached.\n\n"
            f"CONVERSATION:\n{history_text}\n\n"
            "SUMMARY (be concise, in the same language as the conversation):"
        )
        result = self._call_gemini(prompt)
        return result.strip() if result else ""

    def _stream_gemini(self, prompt: str) -> Generator[str, None, None]:
        """Streaming Gemini call — yields text chunks one by one. Retries on 503."""
        if not self._model:
            yield "⚠️ Gemini API is not configured. Please set GEMINI_KEY in .env"
            return
        from google.genai import types
        last_exc = None
        for attempt in range(3):
            try:
                stream = self._client.models.generate_content_stream(
                    model=self._model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=3000),
                )
                for chunk in stream:
                    if chunk.text:
                        yield chunk.text
                return  # success
            except Exception as exc:
                last_exc = exc
                if '503' in str(exc) or 'UNAVAILABLE' in str(exc).upper():
                    wait = 2 ** attempt  # 1s, 2s, 4s
                    print(f"[Chatbot] Gemini 503 — retrying in {wait}s (attempt {attempt + 1}/3)")
                    time.sleep(wait)
                else:
                    break
        print(f"[Chatbot] Gemini stream error: {last_exc}")
        yield f"\n❌ AI is temporarily unavailable (503). Please try again in a moment."

    # ------------------------------------------------------------------
    # Data quality check (port of is_data_poor logic)
    # ------------------------------------------------------------------

    def _check_data_quality(self, db_data: List[Dict]) -> Tuple[bool, str]:
        """
        Returns (is_data_poor: bool, found_schools_context: str).
        is_data_poor = True when >= 50% of top-5 rows lack both fee AND requirements.
        """
        if not db_data:
            return True, ""

        top_records = db_data[:5]
        null_count = 0
        for r in top_records:
            fee_missing = r.get("fee") is None
            # Any entry requirement counts as "has data"
            any_req = any(
                r.get(k) is not None
                for k in ("IELTS", "TOEFL", "GPA", "SAT", "GRE", "GMAT", "ACT")
            )
            # Poor data: no fee AND no entry requirement at all
            if fee_missing and not any_req:
                null_count += 1

        is_poor = null_count >= max(1, len(top_records) // 2)

        found_schools = ""
        names = [r.get("name", "") for r in db_data[:3] if r.get("name")]
        if names:
            found_schools = f"Universities found in database: {', '.join(names)}"

        return is_poor, found_schools

    def _format_db_data(self, data: List[Dict]) -> str:
        """Format DB rows as numbered JSON strings for AI readability."""
        if not data:
            return "No data available."
        rows = []
        for i, rec in enumerate(data[:7], 1):
            rows.append(f"Candidate #{i}: {json.dumps(rec, ensure_ascii=False, default=str)}")
        return "\n".join(rows)

    def _format_history(self, history: List[Dict], limit: int = 5, summary: str = "") -> str:
        lines = []
        if summary:
            lines.append(f"[Earlier conversation summary]: {summary}")
        if not history:
            return "\n".join(lines) if lines else "(No previous conversation)"
        recent = history[-limit:]
        for msg in recent:
            role = "User" if msg.get("role") == "user" else "Assistant"
            lines.append(f"{role}: {msg.get('content', '')[:300]}")
        return "\n".join(lines)

    def _format_user_profile(self, profile: Optional[Dict]) -> str:
        """Format user StudyBG into a readable block for AI prompts."""
        if not profile:
            return ""
        fields = [
            ("level",        "Level"),
            ("major",        "Major"),
            ("gpa",          "GPA"),
            ("ielts",        "IELTS"),
            ("toefl",        "TOEFL"),
            ("sat",          "SAT"),
            ("gre",          "GRE"),
            ("gmat",         "GMAT"),
            ("act",          "ACT"),
            ("inter_bac",    "IB Score"),
            ("cam_adv_test", "Cambridge Advanced"),
            ("graduate_year","Graduation Year"),
        ]
        lines = []
        for key, label in fields:
            val = profile.get(key)
            if val is not None:
                lines.append(f"  {label}: {val}")
        if not lines:
            return ""
        return "2. USER PROFILE (stored scores):\n" + "\n".join(lines) + "\n\n"

    # ------------------------------------------------------------------
    # Sync public API
    # ------------------------------------------------------------------

    def process(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> str:
        """Sync entry point — returns full response string."""
        intent = self._router.classify(message)
        print(f"[Chatbot Router] intent={intent!r} | msg={message[:60]!r}")

        if intent == "CHITCHAT":
            return self._handle_chitchat(message, history, user_profile, history_summary=history_summary)
        return self._handle_domain_sync(message, history, user_profile, history_summary=history_summary)

    # ------------------------------------------------------------------
    # Streaming public API
    # ------------------------------------------------------------------

    def process_stream(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> Generator[str, None, None]:
        """
        Streaming entry point — yields text chunks.
        May yield a final special signal: <<ONLINE_SEARCH|{query}>>
        when the internal DB data is insufficient.
        """
        intent = self._router.classify(message)
        print(f"[Chatbot Router] intent={intent!r} | msg={message[:60]!r}")

        if intent == "CHITCHAT":
            yield from self._stream_chitchat(message, history, user_profile, history_summary=history_summary)
        else:
            yield from self._stream_domain(message, history, user_profile, history_summary=history_summary)

    # ------------------------------------------------------------------
    # CHITCHAT branch
    # ------------------------------------------------------------------

    def _handle_chitchat(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> str:
        history_str = self._format_history(history, limit=5, summary=history_summary)
        profile_section = self._format_user_profile(user_profile)
        prompt = _CHITCHAT_PROMPT.format(
            history=history_str, message=message,
            profile_section=profile_section,
        )
        reply = self._call_gemini(prompt)
        if reply:
            return reply.strip()
        return (
            "Hello! I can help you with:\n"
            "- 🎓 Finding universities by country, ranking, or tuition\n"
            "- 📊 Comparing universities side by side\n"
            "- 📋 Entry requirements (IELTS, GPA, SAT...)\n"
            "- 🎯 Scholarship information\n\n"
            "Feel free to ask me anything!"
        )

    def _stream_chitchat(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> Generator[str, None, None]:
        history_str = self._format_history(history, limit=5, summary=history_summary)
        profile_section = self._format_user_profile(user_profile)
        prompt = _CHITCHAT_PROMPT.format(
            history=history_str, message=message,
            profile_section=profile_section,
        )
        yield from self._stream_gemini(prompt)

    # ------------------------------------------------------------------
    # DOMAIN branch — sync
    # ------------------------------------------------------------------

    def _handle_domain_sync(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> str:
        if not self._sql_engine:
            return "⚠️ Gemini API is not configured. Please set GEMINI_KEY in .env"

        ok, sql = self._sql_engine.generate(message, history, user_profile, history_summary=history_summary)
        if not ok or not sql:
            return (
                "Sorry, I couldn't process that question. "
                "Try rephrasing, e.g.:\n"
                '"Top 5 universities in Germany" or "Compare MIT and Stanford".'
            )

        if not sql.strip().upper().startswith("SELECT"):
            return "Invalid query generated."

        try:
            db_data = execute_query(sql.strip(), fetch=True) or []
        except Exception as exc:
            print(f"[Chatbot DB] Query error: {exc}")
            db_data = []

        is_poor, found_schools = self._check_data_quality(db_data)
        profile_section = self._format_user_profile(user_profile)

        # Inject RAG supplementary text (non-fatal if RAG unavailable)
        formatted_data = self._format_db_data(db_data)
        if self._rag:
            uni_ids = [r["id"] for r in db_data if r.get("id")]
            rag_ctx = self._rag.format_rag_context(message, university_ids=uni_ids or None)
            if rag_ctx:
                formatted_data += rag_ctx

        if is_poor:
            prompt = _DOMAIN_PROMPT_POOR.format(
                message=message,
                found_schools=found_schools or "No universities found in the database.",
            )
            reply = self._call_gemini(prompt) or ""
            return reply.strip() + f"\n\n<<ONLINE_SEARCH|{message}>>"
        else:
            prompt = _DOMAIN_PROMPT_RICH.format(
                message=message,
                formatted_data=formatted_data,
                profile_section=profile_section,
            )
            reply = self._call_gemini(prompt)
            return reply.strip() if reply else self._plain_fallback(db_data)

    # ------------------------------------------------------------------
    # DOMAIN branch — streaming
    # ------------------------------------------------------------------

    def _stream_domain(self, message: str, history: List[Dict], user_profile: Optional[Dict] = None, history_summary: str = "") -> Generator[str, None, None]:
        if not self._sql_engine:
            yield "⚠️ Gemini API is not configured. Please set GEMINI_KEY in .env"
            return

        # Step 1: Generate SQL (non-streaming — needed before we can stream the answer)
        ok, sql = self._sql_engine.generate(message, history, user_profile, history_summary=history_summary)
        if not ok or not sql:
            yield (
                "Sorry, I couldn't process that question. "
                "Try rephrasing, e.g.:\n"
                '"Top 5 universities in Germany" or "Compare MIT and Stanford".'
            )
            return

        if not sql.strip().upper().startswith("SELECT"):
            yield "Invalid query generated."
            return

        # Step 2: Execute SQL
        try:
            db_data = execute_query(sql.strip(), fetch=True) or []
            print(f"[Chatbot SQL] Executed. Found {len(db_data)} rows.")
        except Exception as exc:
            print(f"[Chatbot DB] Query error: {exc}")
            db_data = []

        # Step 3: Check data quality (is_data_poor)
        is_poor, found_schools = self._check_data_quality(db_data)
        profile_section = self._format_user_profile(user_profile)

        # Step 4: Build formatted data — inject RAG supplementary text
        formatted_data = self._format_db_data(db_data)
        if self._rag:
            uni_ids = [r["id"] for r in db_data if r.get("id")]
            rag_ctx = self._rag.format_rag_context(message, university_ids=uni_ids or None)
            if rag_ctx:
                formatted_data += rag_ctx

        # Step 5: Build prompt based on data quality
        if is_poor:
            prompt = _DOMAIN_PROMPT_POOR.format(
                message=message,
                found_schools=found_schools or "No universities found in the database.",
            )
        else:
            prompt = _DOMAIN_PROMPT_RICH.format(
                message=message,
                formatted_data=formatted_data,
                profile_section=profile_section,
            )

        # Step 5: Stream Gemini response
        yield from self._stream_gemini(prompt)

        # Step 6: Emit online search signal if data was poor (port of <<SHOW_WEB_SEARCH_BUTTON>>)
        if is_poor:
            yield f"\n\n<<ONLINE_SEARCH|{message}>>"

    # ------------------------------------------------------------------
    # Plain text fallback (no Gemini available)
    # ------------------------------------------------------------------

    def _plain_fallback(self, data: List[Dict]) -> str:
        if not data:
            return (
                "No universities found matching your criteria.\n\n"
                "💡 **Suggestions:**\n"
                "1. Broaden your search (try additional countries or regions)\n"
                "2. Adjust the tuition range or entry requirements\n"
                "3. Search by region: Asia, Europe, North America...\n\n"
                "Would you like to try a different search?"
            )
        lines = [f"Found **{len(data)}** result(s):\n"]
        for i, row in enumerate(data[:10], 1):
            name = row.get("name", "Unknown")
            rank = row.get("rank_int") or "N/A"
            country = row.get("country_name") or "N/A"
            fee = row.get("fee")
            fee_str = f"${fee:,.0f}/year" if fee else "Not available"
            ielts = row.get("IELTS") or "N/A"
            lines.append(
                f"**{i}. {name}** — Rank #{rank} | {country}\n"
                f"   💰 Tuition: {fee_str} | 📋 IELTS: {ielts}"
            )
        return "\n\n".join(lines)
