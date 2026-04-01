# ─────────────────────────────────────────────────────────────
# 국가법령정보센터 API → 법령 조문 수집 스크립트
# 실행: python scripts/fetch_laws.py
# 결과: scripts/output/laws/상가건물임대차보호법.json
# ─────────────────────────────────────────────────────────────

import asyncio
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings

# ── 수집 대상 법령 ──────────────────────────────────────────
LAW_TARGETS = [
    {"name": "상가건물임대차보호법", "mst": "276285"},
    {"name": "민법_임대차",          "mst": "199385"},  # 민법 MST
]

BASE_URL = "https://www.law.go.kr/DRF/lawService.do"


async def fetch_law(client: httpx.AsyncClient, name: str, mst: str) -> list[dict]:
    """
    법령 MST로 전체 조문 목록을 가져옵니다.
    반환: [{"law": "상가건물임대차보호법", "article": "제1조", "title": "목적", "content": "..."}]
    """
    params = {
        "OC": settings.law_api_key,
        "target": "law",
        "MST": mst,
        "type": "JSON",
    }

    print(f"[fetch] {name} (MST={mst}) 요청 중...")
    response = await client.get(BASE_URL, params=params)
    response.raise_for_status()

    data = response.json()
    articles_raw = data.get("법령", {}).get("조문", {}).get("조문단위", [])

    chunks = []
    for article in articles_raw:
        if article.get("조문여부") != "조문":
            continue  # 별표, 서식 등 제외

        # 조문내용 + 항단위 내용 합치기
        content_parts = [article.get("조문내용", "").strip()]

        # API 응답에서 항이 1개면 딕셔너리로, 2개 이상이면 리스트로 오는걸 항상 리스트로 통일시키는 처리
        hang_list = article.get("항", [])
        if isinstance(hang_list, dict):
            hang_list = [hang_list]

        for hang in hang_list:
            hang_content = hang.get("항내용", "").strip()
            if hang_content:
                content_parts.append(hang_content)


        content = "\n".join(filter(None, content_parts))

        if not content:
            continue

        chunks.append({
            "law": name,
            "article_id": f"제{article['조문번호']}조",
            "title": article.get("조문제목", ""),
            "content": content,
        })

    print(f"  → {len(chunks)}개 조문 추출 완료")
    return chunks


async def main():
    output_dir = Path(__file__).parent / "output" / "laws"
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(timeout=30) as client:
        all_chunks = []
        
        for target in LAW_TARGETS:
            chunks = await fetch_law(client, target["name"], target["mst"])
            all_chunks.extend(chunks)

            # 법령별 개별 저장
            out_path = output_dir / f"{target['name']}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            print(f"  → 저장: {out_path}")

        # 전체 합본 저장
        all_path = output_dir / "all_laws.json"
        with open(all_path, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)

        print(f"\n[완료] 총 {len(all_chunks)}개 조문 → {all_path}")


if __name__ == "__main__":
    asyncio.run(main())
