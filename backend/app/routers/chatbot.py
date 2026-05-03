"""
Chatbot API router.

Endpoints:
  POST   /api/chatbot/chat                           — send a message, get AI reply
  GET    /api/chatbot/sessions                       — list sessions for a user
  GET    /api/chatbot/sessions/{session_id}/messages — load message history
  DELETE /api/chatbot/sessions/{session_id}          — delete a session
"""

import asyncio
import json
import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.database import execute_query
from app.dependencies import get_current_user
from app.utils.chatbot_engine import ChatbotEngine

router = APIRouter()

# ---------------------------------------------------------------------------
# Lazy singleton engine — initialized on first request to avoid import-time
# failures if the Gemini key is not yet configured.
# ---------------------------------------------------------------------------
_engine: Optional[ChatbotEngine] = None


def _get_engine() -> ChatbotEngine:
    global _engine
    if _engine is None:
        try:
            from app.config import settings
            gemini_key  = getattr(settings, "GEMINI_KEY",      None)
            tavily_key  = getattr(settings, "TAVILY_API_KEY",  None)
        except Exception:
            gemini_key = None
            tavily_key = None
        _engine = ChatbotEngine(gemini_key=gemini_key, tavily_key=tavily_key)
    return _engine


# ---------------------------------------------------------------------------
# DB helpers — create tables once at module load (idempotent)
# ---------------------------------------------------------------------------

def _ensure_tables() -> None:
    """Create chat_sessions and chat_messages tables if they don't exist yet."""
    try:
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id          VARCHAR(36)   NOT NULL PRIMARY KEY,
                user_id     INT           NULL,
                title       VARCHAR(255)  NOT NULL DEFAULT 'New Chat',
                created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
                                          ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_cs_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chat_messages (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                session_id  VARCHAR(36)         NOT NULL,
                role        ENUM('user','assistant') NOT NULL,
                content     TEXT                NOT NULL,
                created_at  TIMESTAMP           NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                INDEX idx_cm_session (session_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )
        execute_query(
            """
            CREATE TABLE IF NOT EXISTS chat_session_summaries (
                session_id        VARCHAR(36)  NOT NULL PRIMARY KEY,
                summary           TEXT         NOT NULL,
                updated_msg_count INT          NOT NULL DEFAULT 0,
                updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
                                               ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
        )
    except Exception as exc:
        # Non-fatal: tables might already exist or user lacks DDL rights
        print(f"[Chatbot] Table init warning: {exc}")


# Run once when the module is first imported
_ensure_tables()


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message:    str           = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id:    Optional[int] = None


class ChatResponse(BaseModel):
    response:   str
    session_id: str


class SessionItem(BaseModel):
    id:         str
    title:      str
    created_at: str


class MessageItem(BaseModel):
    id:         int
    role:       str
    content:    str
    created_at: str


# ---------------------------------------------------------------------------
# Route helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(session_id: Optional[str], user_id: Optional[int], title: str) -> str:
    if session_id:
        row = execute_query(
            "SELECT id FROM chat_sessions WHERE id = %s",
            (session_id,),
            fetch=True,
            fetch_one=True,
        )
        if row:
            return session_id

    # Create new session
    new_id = str(uuid.uuid4())
    safe_title = title[:255]
    execute_query(
        "INSERT INTO chat_sessions (id, user_id, title) VALUES (%s, %s, %s)",
        (new_id, user_id, safe_title),
    )
    return new_id


def _load_history(session_id: str, limit: int = 10) -> List[dict]:
    rows = execute_query(
        """
        SELECT role, content
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY id DESC
        LIMIT %s
        """,
        (session_id, limit),
        fetch=True,
    ) or []
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _load_user_profile(user_id: Optional[int]) -> Optional[dict]:
    """Load study background scores for a user (used as profile context for the AI)."""
    if not user_id:
        return None
    try:
        from app.models.study_bg import StudyBGModel
        profile = StudyBGModel.get_by_user_id(user_id)
        if not profile:
            return None
        # Return only the numeric score fields; omit nulls
        keys = ("ielts", "toefl", "gpa", "sat", "gre", "gmat", "act",
                "inter_bac", "cam_adv_test", "level", "major", "graduate_year")
        return {k: profile[k] for k in keys if profile.get(k) is not None}
    except Exception as exc:
        print(f"[Chatbot] Failed to load user profile for user_id={user_id}: {exc}")
        return None


def _save_messages(session_id: str, user_msg: str, bot_reply: str) -> None:
    execute_query(
        "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
        (session_id, "user", user_msg),
    )
    execute_query(
        "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
        (session_id, "assistant", bot_reply),
    )
    execute_query(
        "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
        (session_id,),
    )


def _load_summary(session_id: str) -> str:
    """Load the stored conversation summary for a session (empty string if none)."""
    row = execute_query(
        "SELECT summary FROM chat_session_summaries WHERE session_id = %s",
        (session_id,),
        fetch=True,
        fetch_one=True,
    )
    return row["summary"] if row else ""


def _maybe_update_summary(session_id: str, engine) -> None:
    """
    Summarize older messages and cache in chat_session_summaries when the
    session has >= 10 messages AND at least 10 new messages arrived since
    the last summary update.  Runs synchronously after the SSE done event.
    """
    try:
        count_row = execute_query(
            "SELECT COUNT(*) AS cnt FROM chat_messages WHERE session_id = %s",
            (session_id,),
            fetch=True,
            fetch_one=True,
        )
        count = count_row["cnt"] if count_row else 0
        if count < 10:
            return

        existing = execute_query(
            "SELECT updated_msg_count FROM chat_session_summaries WHERE session_id = %s",
            (session_id,),
            fetch=True,
            fetch_one=True,
        )
        last_count = existing["updated_msg_count"] if existing else 0
        if count - last_count < 10:
            return  # Not enough new messages to warrant an update

        # Summarise everything except the most recent 5 messages
        all_msgs = execute_query(
            "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY id ASC",
            (session_id,),
            fetch=True,
        ) or []
        older = all_msgs[:-5] if len(all_msgs) > 5 else all_msgs
        if not older:
            return

        summary_text = engine._summarize_history(older)
        if not summary_text:
            return

        execute_query(
            """
            INSERT INTO chat_session_summaries (session_id, summary, updated_msg_count)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE
                summary           = VALUES(summary),
                updated_msg_count = VALUES(updated_msg_count),
                updated_at        = CURRENT_TIMESTAMP
            """,
            (session_id, summary_text, count),
        )
        print(f"[Chatbot] Summary updated for session {session_id} ({count} messages).")
    except Exception as exc:
        print(f"[Chatbot] Summary update error: {exc}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Send a user message and receive an AI-generated reply grounded in the
    university database. Manages session creation and history automatically.
    """
    user_id    = current_user["id"]
    title      = (req.message[:60] + "…") if len(req.message) > 60 else req.message
    session_id = _get_or_create_session(req.session_id, user_id, title)

    history         = _load_history(session_id)
    history_summary = _load_summary(session_id)
    user_profile    = _load_user_profile(user_id)
    engine          = _get_engine()
    bot_reply       = engine.process(req.message, history, user_profile=user_profile, history_summary=history_summary)

    _save_messages(session_id, req.message, bot_reply)
    _maybe_update_summary(session_id, engine)

    return ChatResponse(response=bot_reply, session_id=session_id)


@router.get("/sessions", response_model=List[SessionItem])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    """List the 50 most recent chat sessions for the authenticated user."""
    user_id = current_user["id"]

    rows = execute_query(
        """
        SELECT id, title, created_at
        FROM chat_sessions
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT 50
        """,
        (user_id,),
        fetch=True,
    ) or []

    return [
        SessionItem(id=r["id"], title=r["title"], created_at=str(r["created_at"]))
        for r in rows
    ]


@router.get("/sessions/{session_id}/messages", response_model=List[MessageItem])
async def get_messages(session_id: str, current_user: dict = Depends(get_current_user)):
    """Return all messages in a chat session, ordered oldest → newest."""
    rows = execute_query(
        """
        SELECT id, role, content, created_at
        FROM chat_messages
        WHERE session_id = %s
        ORDER BY id ASC
        """,
        (session_id,),
        fetch=True,
    ) or []

    return [
        MessageItem(
            id=r["id"],
            role=r["role"],
            content=r["content"],
            created_at=str(r["created_at"]),
        )
        for r in rows
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a session and all its messages (cascades via FK)."""
    execute_query("DELETE FROM chat_sessions WHERE id = %s", (session_id,))


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

async def _sync_gen_to_sse(sync_gen) -> AsyncGenerator[str, None]:
    """
    Wraps a blocking sync generator into an async generator suitable for
    FastAPI StreamingResponse.  Each text chunk is emitted as an SSE
    'data:' line; the special <<ONLINE_SEARCH|query>> signal is emitted
    as a named 'online_search' SSE event.
    Port of the Tkinter chunk-writing loop in /chatbot/engine/chat_engine.py.
    """
    loop = asyncio.get_event_loop()
    while True:
        chunk = await loop.run_in_executor(None, lambda: next(sync_gen, None))
        if chunk is None:
            break
        if chunk.startswith("<<ONLINE_SEARCH|"):
            query = chunk[len("<<ONLINE_SEARCH|"):-2]  # strip << and >>
            yield f"event: online_search\ndata: {json.dumps({'query': query})}\n\n"
        else:
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"


# ---------------------------------------------------------------------------
# Streaming chat endpoint  (port of ask_stream from /chatbot/engine/chat_engine.py)
# ---------------------------------------------------------------------------

@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    SSE streaming endpoint — yields text chunks as they are generated.

    SSE event types:
      (default)      data: {"chunk": "..."}
      online_search  data: {"query": "..."}
      done           data: {"session_id": "..."}
    """
    title        = (req.message[:60] + "…") if len(req.message) > 60 else req.message
    session_id   = _get_or_create_session(req.session_id, req.user_id, title)
    history      = _load_history(session_id)
    history_summary = _load_summary(session_id)
    user_profile = _load_user_profile(req.user_id)
    engine       = _get_engine()

    async def generate() -> AsyncGenerator[str, None]:
        sync_gen     = engine.process_stream(req.message, history, user_profile=user_profile, history_summary=history_summary)
        full_reply   = []
        has_sent_done = False

        try:
            async for sse_line in _sync_gen_to_sse(sync_gen):
                # Accumulate plain text chunks for DB storage
                if sse_line.startswith("data: ") and '"chunk"' in sse_line:
                    try:
                        payload = json.loads(sse_line[6:])
                        full_reply.append(payload.get("chunk", ""))
                    except Exception:
                        pass
                yield sse_line
        except Exception as exc:
            err_chunk = '\u274c Error: ' + str(exc)
            yield 'data: ' + json.dumps({'chunk': err_chunk}) + '\n\n'
        finally:
            # Save conversation to DB
            reply_text = "".join(full_reply)
            if reply_text:
                _save_messages(session_id, req.message, reply_text)
            # Emit done event with session_id for the frontend to persist
            yield f"event: done\ndata: {json.dumps({'session_id': session_id})}\n\n"
            # Update summary after done event (runs after stream completes)
            _maybe_update_summary(session_id, engine)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ---------------------------------------------------------------------------
# Online search endpoint  (port of perform_online_search + search_tool.py)
# ---------------------------------------------------------------------------

class SearchOnlineRequest(BaseModel):
    message:     str           = Field(..., min_length=1, max_length=2000)
    session_id:  Optional[str] = None
    search_hint: str           = Field(default="", max_length=200)


@router.post("/chat/search-online")
async def search_online(req: SearchOnlineRequest):
    """
    Triggered when the user clicks the 'Search Online' button after the bot
    signals insufficient DB data (<<ONLINE_SEARCH|query>> signal).

    SSE event types:
      (default)  data: {"chunk": "..."}
      done       data: {}
    """
    from app.utils.online_search import OnlineSearchEngine
    try:
        from app.config import settings
        tavily_key = getattr(settings, "TAVILY_API_KEY", None)
    except Exception:
        tavily_key = None

    engine        = _get_engine()
    search_engine = OnlineSearchEngine(
        stream_gemini=engine._stream_gemini,
        tavily_key=tavily_key,
    )

    async def generate() -> AsyncGenerator[str, None]:
        sync_gen   = search_engine.search_and_stream(
            user_query=req.message,
            search_hint=req.search_hint,
        )
        full_reply = []

        try:
            async for sse_line in _sync_gen_to_sse(sync_gen):
                if sse_line.startswith("data: ") and '"chunk"' in sse_line:
                    try:
                        payload = json.loads(sse_line[6:])
                        full_reply.append(payload.get("chunk", ""))
                    except Exception:
                        pass
                yield sse_line
        except Exception as exc:
            err_chunk = '\u274c Search error: ' + str(exc)
            yield 'data: ' + json.dumps({'chunk': err_chunk}) + '\n\n'
        finally:
            # Optionally persist search result to session
            if req.session_id and full_reply:
                reply_text = "".join(full_reply)
                try:
                    execute_query(
                        "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
                        (req.session_id, "assistant", f"[Online Search]\n{reply_text}"),
                    )
                    execute_query(
                        "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (req.session_id,),
                    )
                except Exception:
                    pass
            yield f"event: done\ndata: {{}}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
