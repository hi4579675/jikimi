from __future__ import annotations

import asyncio
import psycopg2
from pgvector.psycopg2 import register_vector
from google import genai
from google.genai import types

from app.core.config import settings

EMBEDDING_MODEL = "gemini-embedding-001"
TOP_K = 5


class RagService:
    def __init__(self):
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def _embed(self, text: str) -> list[float]:
        result = self._client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return result.embeddings[0].values

    def _query_db(self, embedding: list[float], top_k: int) -> list[dict]:
        conn = psycopg2.connect(settings.database_url)
        register_vector(conn)
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT law, article_id, title, content,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM vector.law_chunks
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (embedding, embedding, top_k),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        return [
            {
                "law": row[0],
                "article_id": row[1],
                "title": row[2],
                "content": row[3],
                "similarity": float(row[4]),
            }
            for row in rows
        ]

    async def search_legal_context(self, text: str, top_k: int = TOP_K) -> list[dict]:
        embedding = await asyncio.to_thread(self._embed, text)
        return await asyncio.to_thread(self._query_db, embedding, top_k)
