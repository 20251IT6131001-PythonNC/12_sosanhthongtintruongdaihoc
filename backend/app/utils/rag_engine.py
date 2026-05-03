"""
RAG Engine — ChromaDB vector store for supplementary university text retrieval.

Data source  : university_texts table (about, scholarships, rankings_and_ratings,
               university_information)
Embeddings   : sentence-transformers/all-MiniLM-L6-v2  (local, no API quota)
Vector store : ChromaDB PersistentClient  →  backend/chroma_db/

Usage (inside ChatbotEngine):
    from app.utils.rag_engine import RagEngine
    rag = RagEngine()
    # rag.build_index()  ← run once to populate (see CLI below)
    ctx = rag.format_rag_context(query, university_ids=[1, 2, 3])

CLI — rebuild the index:
    cd backend
    python -m app.utils.rag_engine
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

# ChromaDB storage: backend/chroma_db/  (one level above this utils folder)
_CHROMA_PATH = str(Path(__file__).resolve().parent.parent.parent / "chroma_db")
_COLLECTION_NAME = "university_texts"
_EMBED_MODEL = "all-MiniLM-L6-v2"  # ~80 MB, 384-dim, fast & accurate


class RagEngine:
    """Retrieval-Augmented Generation engine backed by ChromaDB."""

    def __init__(self, gemini_key: Optional[str] = None):  # gemini_key kept for API compat
        self._st_model = None   # SentenceTransformer instance (lazy loaded)
        self._chroma_client = None
        self._collection = None
        self._ready = False
        self._init()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init(self) -> None:
        try:
            import chromadb
            self._chroma_client = chromadb.PersistentClient(path=_CHROMA_PATH)
            self._collection = self._chroma_client.get_or_create_collection(
                name=_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            count = self._collection.count()
            if count > 0:
                self._ready = True
            print(f"[RAG] ChromaDB ready. {count} documents indexed.")
        except ImportError as exc:
            print(f"[RAG] Missing dependency: {exc}. Run: pip install chromadb")
        except Exception as exc:
            print(f"[RAG] Init error: {exc}")

    # ------------------------------------------------------------------
    # Embedding helper  (sentence-transformers, runs 100% locally)
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> List[float]:
        if self._st_model is None:
            from sentence_transformers import SentenceTransformer
            print(f"[RAG] Loading embedding model '{_EMBED_MODEL}' (first time may download ~80 MB)...")
            self._st_model = SentenceTransformer(_EMBED_MODEL)
            print("[RAG] Embedding model ready.")
        return self._st_model.encode(text, normalize_embeddings=True).tolist()

    # ------------------------------------------------------------------
    # Index builder
    # ------------------------------------------------------------------

    def build_index(self) -> int:
        """
        Fetch university text data from MySQL and build/update the ChromaDB index.
        Returns the number of documents indexed.
        """
        if not self._collection:
            print("[RAG] Not initialised — cannot build index.")
            return 0

        from app.database import execute_query

        rows = execute_query(
            """
            SELECT u.id, u.name, c.name AS country,
                   ut.about, ut.scholarships,
                   ut.rankings_and_ratings, ut.university_information
            FROM universities u
            LEFT JOIN countries c ON c.id = u.country_id
            LEFT JOIN university_texts ut ON ut.university_id = u.id
            WHERE ut.about IS NOT NULL
               OR ut.scholarships IS NOT NULL
               OR ut.rankings_and_ratings IS NOT NULL
               OR ut.university_information IS NOT NULL
            """,
            fetch=True,
        ) or []

        if not rows:
            print("[RAG] No text data found in university_texts table.")
            return 0

        ids: List[str] = []
        embeddings: List[List[float]] = []
        documents: List[str] = []
        metadatas: List[dict] = []

        for row in rows:
            uid = row["id"]
            parts = [
                f"University: {row['name']}",
                f"Country: {row['country'] or 'Unknown'}",
            ]
            if row.get("about"):
                parts.append(f"About: {str(row['about'])[:600]}")
            if row.get("scholarships"):
                parts.append(f"Scholarships: {str(row['scholarships'])[:400]}")
            if row.get("rankings_and_ratings"):
                parts.append(f"Rankings: {str(row['rankings_and_ratings'])[:300]}")
            if row.get("university_information"):
                parts.append(f"Info: {str(row['university_information'])[:300]}")

            text = "\n".join(parts)
            try:
                emb = self._embed(text)
            except Exception as exc:
                print(f"[RAG] Embedding error for university {uid}: {exc}")
                continue

            ids.append(str(uid))
            embeddings.append(emb)
            documents.append(text)
            metadatas.append(
                {
                    "university_id": uid,
                    "name": str(row["name"]),
                    "country": str(row["country"] or ""),
                }
            )

        if ids:
            self._collection.upsert(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
            )
            self._ready = True
            print(f"[RAG] Indexed {len(ids)} universities.")

        return len(ids)

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def format_rag_context(
        self,
        query: str,
        university_ids: Optional[List[int]] = None,
        top_k: int = 3,
    ) -> str:
        """
        Retrieve relevant text chunks from ChromaDB and return a formatted
        context string to append to the AI prompt.

        Args:
            query          : User's natural language question.
            university_ids : If provided, restrict results to these university IDs
                             (the ones already found by Text-to-SQL).
            top_k          : Max number of documents to retrieve.
        """
        if not self._ready or not self._collection or not self._genai_client:
            return ""

        try:
            query_emb = self._embed(query)
            n = min(top_k, self._collection.count())
            if n == 0:
                return ""

            kwargs: dict = {
                "query_embeddings": [query_emb],
                "n_results": n,
                "include": ["documents", "metadatas"],
            }
            # Filter to specific universities when IDs are available
            if university_ids:
                kwargs["where"] = {"university_id": {"$in": university_ids}}

            results = self._collection.query(**kwargs)
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]

            if not docs:
                return ""

            lines = ["\n4. SUPPLEMENTARY TEXT (from university knowledge base):"]
            for doc, meta in zip(docs, metas):
                name = meta.get("name", "University")
                lines.append(f"  [{name}]: {doc[:500]}")

            return "\n".join(lines) + "\n"

        except Exception as exc:
            print(f"[RAG] Query error: {exc}")
            return ""


# ---------------------------------------------------------------------------
# CLI: python -m app.utils.rag_engine
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        from app.config import settings
        gemini_key = getattr(settings, "GEMINI_KEY", None)
    except Exception:
        gemini_key = None

    if not gemini_key:
        print("WARNING: GEMINI_KEY not set, but embedding is local — proceeding anyway.")

    rag = RagEngine()
    count = rag.build_index()
    print(f"Done. {count} documents indexed to {_CHROMA_PATH}")
