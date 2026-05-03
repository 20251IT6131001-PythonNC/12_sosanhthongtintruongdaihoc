"""
Online Search Engine — port of /chatbot/engine/search_tool.py

Uses Tavily API to search the web, then Gemini to summarize the results.
Triggered when the internal DB has insufficient data (is_data_poor == True).
"""

from __future__ import annotations

from typing import Callable, Generator, Optional


class OnlineSearchEngine:
    """
    Port of /chatbot/engine/search_tool.py with:
    - English prompts
    - New google.genai streaming callable
    - No Tkinter dependencies
    """

    def __init__(
        self,
        stream_gemini: Callable[[str], Generator[str, None, None]],
        tavily_key: Optional[str] = None,
    ):
        """
        Args:
            stream_gemini: Callable that takes a prompt str and yields text chunks.
                           Should be ChatbotEngine._stream_gemini.
            tavily_key:    Tavily API key (from settings.TAVILY_API_KEY).
        """
        self._stream_gemini = stream_gemini
        self._client = None

        if tavily_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=tavily_key)
                print("[OnlineSearch] Tavily client ready.")
            except Exception as exc:
                print(f"[OnlineSearch] Tavily init failed: {exc}")

    def search_and_stream(
        self,
        user_query: str,
        search_hint: str = "",
    ) -> Generator[str, None, None]:
        """
        Port of search_tool.search_and_answer():
        1. Search Tavily (with optional search_hint to narrow the query)
        2. Feed results into Gemini streaming prompt
        3. Yield text chunks

        Args:
            user_query:   The original user question.
            search_hint:  Extra context (e.g. a university name) to sharpen the search.
        """
        if not self._client:
            yield (
                "❌ Online search is not available. "
                "Please set `TAVILY_API_KEY` in the backend `.env` file."
            )
            return

        try:
            # Build enriched query (mirrors old chatbot's search_query enrichment)
            query = user_query
            if search_hint:
                query = f"{user_query} {search_hint} tuition fees admission requirements"

            print(f"[Tavily] Searching: {query[:120]}")

            result = self._client.search(
                query=query,
                search_depth="advanced",
                max_results=5,
                include_answer=True,
            )

            tavily_answer = result.get("answer") or ""
            results = result.get("results") or []

            if not results:
                yield (
                    "I couldn't find relevant information online for this query.\n"
                    "Please try visiting the university's official website directly."
                )
                return

            # Format web content (mirrors old chatbot's web_content building)
            web_content = "\n".join([
                f"- [{r['title']}]({r['url']}): {r['content'][:400]}..."
                for r in results
            ])

            if tavily_answer:
                web_content = (
                    f"**Quick Answer from Search:** {tavily_answer}\n\n"
                    f"**Detailed Sources:**\n{web_content}"
                )

            # Build summarization prompt (English translation of old chatbot's Tavily prompt)
            prompt = f"""
TASK: You are a study abroad expert consultant. Our internal database lacks sufficient data,
so here are LIVE ONLINE SEARCH RESULTS retrieved from the web.

USER QUESTION: "{user_query}"

SEARCH RESULTS:
{web_content}

REQUIREMENTS:
- Answer the user's question directly based on the search results above.
- If tuition fees or entry requirements are found, state them clearly with exact figures.
- Structure the response with clear headers and bullet points.
- At the end, cite the source URLs so the user can verify the information themselves.
- Use emoji to highlight key information (💰 📋 🎓 ✅ ⚠️).
- Respond in English.
- Do NOT invent or guess any information not present in the search results.
"""
            yield from self._stream_gemini(prompt)

        except Exception as exc:
            print(f"[OnlineSearch] Error: {exc}")
            yield f"❌ Online search failed: {str(exc)}"
