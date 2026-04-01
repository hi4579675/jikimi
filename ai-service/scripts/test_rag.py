"""
RAG 서비스 통합 테스트
Usage: python scripts/test_rag.py
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.rag_service import RagService

QUERIES = [
    "보증금 반환 의무",
    "계약 갱신 요구권",
    "임대료 인상 한도",
    "권리금 회수 방해",
]

OUTPUT_DIR = Path(__file__).parent / "output"


async def main():
    svc = RagService()
    lines = []

    for query in QUERIES:
        header = f"\n{'='*60}\n쿼리: {query}\n{'='*60}"
        print(header)
        lines.append(header)

        results = await svc.search_legal_context(query, top_k=3)

        for i, r in enumerate(results, 1):
            row = (
                f"\n[{i}] {r['law']} {r['article_id']} {r['title'] or ''}\n"
                f"    유사도: {r['similarity']:.4f}\n"
                f"    내용: {r['content'][:120].strip()}..."
            )
            print(row)
            lines.append(row)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"rag_test_{timestamp}.txt"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[저장] {out_path}")


if __name__ == "__main__":
    asyncio.run(main())
