# ─────────────────────────────────────────────────────────────
# 법령 JSON → Gemini 임베딩 → SQL 파일 생성
# 실행: python scripts/embed_laws.py
# 생성: scripts/output/law_embeddings.sql
# 적재: docker exec -i jikimi_postgres psql -U jikimi -d jikimi < ai-service/scripts/output/law_embeddings.sql
# ─────────────────────────────────────────────────────────────

import json
import sys
 
from pathlib import Path

from google import genai
from google.genai import types
 

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

EMBEDDING_MODEL = "gemini-embedding-001"
ALL_LAWS_PATH = Path(__file__).parent / "output" / "laws" / "all_laws.json"
OUTPUT_SQL_PATH = Path(__file__).parent / "output" / "law_embeddings.sql"


def get_embedding(client: genai.Client, text: str) -> list[float]:
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text.replace("\n", " "),
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return result.embeddings[0].values


def escape_sql(text: str) -> str:
    return text.replace("'", "''")


def main():
    with open(ALL_LAWS_PATH, encoding="utf-8") as f:
        chunks = json.load(f)

    print(f"[embed] 총 {len(chunks)}개 조문 임베딩 시작...")

    gemini_client = genai.Client(api_key=settings.gemini_api_key)

    lines = ["TRUNCATE TABLE vector.law_chunks RESTART IDENTITY;"]

    for i, chunk in enumerate(chunks, 1):
        text = f"{chunk['title']}\n{chunk['content']}"
        embedding = get_embedding(gemini_client, text)
        vector_str = "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"

        law     = escape_sql(chunk["law"])
        art_id  = escape_sql(chunk["article_id"])
        title   = escape_sql(chunk["title"])
        content = escape_sql(chunk["content"])

        lines.append(
            f"INSERT INTO vector.law_chunks (law, article_id, title, content, embedding) "
            f"VALUES ('{law}', '{art_id}', '{title}', '{content}', '{vector_str}');"
        )
        print(f"  [{i}/{len(chunks)}] {chunk['law']} {chunk['article_id']} {chunk['title']}")

    OUTPUT_SQL_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_SQL_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n[완료] SQL 파일 생성: {OUTPUT_SQL_PATH}")
    print(f"[다음] 아래 명령어로 적재:")
    print(f"  cd d:/jikimi")
    print(f"  docker exec -i jikimi_postgres psql -U jikimi -d jikimi < ai-service/scripts/output/law_embeddings.sql")


if __name__ == "__main__":
    main()
