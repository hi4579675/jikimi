# ─────────────────────────────────────────────────────────────
# OCR 서비스 로컬 테스트 스크립트
# FastAPI 서버 없이 pdfplumber 추출 + 조항 파싱 결과 확인용
# 실행: python scripts/test_ocr.py <PDF경로>
# ─────────────────────────────────────────────────────────────

import asyncio
import sys
from pathlib import Path

# ai-service 루트를 경로에 추가 (app 모듈 import용)
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ocr_service import OcrService


class MockUploadFile:
    """
    FastAPI UploadFile을 흉내내는 Mock 객체
    실제 UploadFile 없이 로컬 파일로 테스트할 때 사용
    Spring의 MockMultipartFile 과 동일한 개념
    """
    def __init__(self, file_bytes: bytes, content_type: str = "application/pdf"):
        self._bytes = file_bytes
        self.content_type = content_type

    async def read(self) -> bytes:
        return self._bytes


async def main(pdf_path: str):
    # ── PDF 파일 읽기 ──────────────────────────────────────────
    path = Path(pdf_path)
    if not path.exists():
        print(f"[ERROR] 파일 없음: {pdf_path}")
        sys.exit(1)

    file_bytes = path.read_bytes()
    print(f"[파일] {path.name} ({len(file_bytes) / 1024:.1f} KB)\n")

    ocr = OcrService()
    mock_file = MockUploadFile(file_bytes)

    # ── STEP 1: 텍스트 추출 ────────────────────────────────────
    print("=" * 60)
    print("STEP 1. 텍스트 추출 (pdfplumber)")
    print("=" * 60)
    raw_text = await ocr.extract_text(mock_file)
    print(f"[추출된 텍스트 앞 300자]\n{raw_text[:300]}")
    print(f"\n[전체 텍스트 길이] {len(raw_text)}자\n")

    # ── STEP 2: 노이즈 제거 + 별지 분리 ──────────────────────
    # parse_articles() 전에 반드시 호출해야 함
    # 안 하면 서명란/별지가 마지막 조항에 붙고, 페이지 번호가 조항 내용에 끼어들어감
    print("=" * 60)
    print("STEP 2. 노이즈 제거 + 별지 분리 (clean_text)")
    print("=" * 60)
    contract_text, annex_text = ocr.clean_text(raw_text)
    print(f"[계약서 본문] {len(contract_text)}자")
    print(f"[별지]        {len(annex_text)}자 (RAG 지식베이스 활용 예정)\n")

    # ── STEP 3: 조항 파싱 ─────────────────────────────────────
    # raw_text가 아니라 정제된 contract_text로 파싱
    print("=" * 60)
    print("STEP 3. 조항 파싱 (제N조 단위)")
    print("=" * 60)
    articles = ocr.parse_articles(contract_text)
    print(f"[파싱된 조항 수] {len(articles)}개\n")

    for article in articles:
        print(f"  {article['article_id']} - {article['title']}")
        print(f"    내용 앞 80자: {article['content'][:80].strip()}")
        print()

    # ── STEP 4: 결과 저장 ─────────────────────────────────────
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / (Path(pdf_path).stem + "_ocr_result.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("STEP 1. 추출된 전체 텍스트 (raw)\n")
        f.write("=" * 60 + "\n")
        f.write(raw_text + "\n\n")

        f.write("=" * 60 + "\n")
        f.write("STEP 2. 정제된 계약서 본문\n")
        f.write("=" * 60 + "\n")
        f.write(contract_text + "\n\n")

        f.write("=" * 60 + "\n")
        f.write("STEP 2-별지. 별지 내용 (RAG 지식베이스 예정)\n")
        f.write("=" * 60 + "\n")
        f.write(annex_text + "\n\n")

        f.write("=" * 60 + "\n")
        f.write(f"STEP 3. 파싱된 조항 ({len(articles)}개)\n")
        f.write("=" * 60 + "\n")
        for article in articles:
            f.write(f"\n[{article['article_id']}] {article['title']}\n")
            f.write(article['content'] + "\n")

    print(f"\n[저장 완료] {output_path}")


if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "../../상가건물임대차표준계약서.pdf"
    asyncio.run(main(pdf_path))