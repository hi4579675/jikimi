# ─────────────────────────────────────────────────────────────
# Spring의 @Service OcrService.java 역할
# PoC 단계: pdfplumber로 PDF 텍스트 추출 + 조항 파싱
# 이후 Clova OCR 연동 예정
# ─────────────────────────────────────────────────────────────

from fastapi import UploadFile, HTTPException
import pdfplumber
import io
import re


class OcrService:
    """
    Spring의 @Service 클래스와 동일한 개념
    OCR 관련 비즈니스 로직을 담당
    """

    async def extract_text(self, file: UploadFile) -> str:
        """
        PDF에서 텍스트를 추출합니다.
        Spring의 서비스 메서드와 동일하게 비즈니스 로직만 담당.

        PoC 1단계: pdfplumber (텍스트 레이어 있는 PDF)
        PoC 2단계: Clova OCR (스캔 PDF, 핸드폰 촬영 이미지)
        """

        # ── PDF 파일 검증 ──────────────────────────────────────
        # Spring의 if (!file.getContentType().equals("application/pdf")) throw new ...
        if file.content_type not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(
                status_code=400,
                detail=f"PDF 파일만 업로드 가능합니다. 현재 파일 타입: {file.content_type}"
            )

        # ── 파일 바이트 읽기 ───────────────────────────────────
        # Spring의 file.getBytes() 와 동일
        file_bytes = await file.read()

        if not file_bytes:
            raise HTTPException(status_code=400, detail="빈 파일입니다.")

        # ── pdfplumber로 텍스트 추출 ───────────────────────────
        # pdfplumber.open()은 파일 경로 또는 BytesIO 모두 받음
        # BytesIO = 바이트를 파일처럼 다루는 메모리 스트림
        # Spring의 new ByteArrayInputStream(bytes) 와 같은 개념
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                pages_text = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text)
                    else:
                        # 텍스트 레이어 없는 페이지 감지 (스캔본일 가능성)
                        print(f"[OcrService] {i+1}페이지 텍스트 없음 — 스캔 PDF일 수 있음")

            extracted = "\n".join(pages_text).strip()

        except Exception as e:
            raise HTTPException(status_code=422, detail=f"PDF 파싱 실패: {str(e)}")

        # ── 텍스트 추출 결과 검증 ──────────────────────────────
        if not extracted:
            # 텍스트 레이어가 아예 없으면 스캔 PDF
            # TODO (2단계): Clova OCR API 호출로 대체
            raise HTTPException(
                status_code=422,
                detail="텍스트를 추출할 수 없습니다. 스캔 PDF는 아직 지원하지 않습니다. (2단계 예정)"
            )

        contract_text, _ = self.clean_text(extracted)
        return contract_text

    def clean_text(self, text: str) -> tuple[str, str]:
        """
        추출된 원본 텍스트에서 노이즈를 제거하고 별지를 분리합니다.
        반환값: (계약서 본문, 별지 텍스트)

        [제거 대상]
        - 페이지 번호 ("- 1 / 3 -")
        - 체크박스 잔해 ("q 전세 q 월세")
        - 서명란 ("본 계약을 증명하기 위하여" 이후)

        [분리 대상]
        - 별지 (줄 시작의 "별지)" 이후) → RAG 지식베이스 활용
        """

        # ── 기본 노이즈 제거 ───────────────────────────────────
        cleaned = re.sub(r'-\s*\d+\s*/\s*\d+\s*-', '', text)       # 페이지 번호
        cleaned = re.sub(r'q\s*(있는 월세|전세|월세)\s*', '', cleaned)  # 체크박스
        cleaned = re.sub(r'\n{2,}', '\n\n', cleaned).strip()

        # ── 별지 분리 ──────────────────────────────────────────
        # "별지)"가 두 곳 존재:
        #   1. 본문 참조: "【중요확인사항】(별지)을" → 제거 대상 아님
        #   2. 실제 별지 시작: 줄 시작의 "\n별지)" → 여기서 분리
        annex_match = re.search(r'\n별지\)', cleaned)
        if annex_match:
            contract_part = cleaned[:annex_match.start()].strip()
            annex_part = cleaned[annex_match.end():].strip()
        else:
            contract_part = cleaned
            annex_part = ""

        # 3. 특약사항 분리 (서명란 제거 전에)
        special_match = re.search(r'\n\[특약사항\]', contract_part)
        if special_match:
            contract_part = contract_part[:special_match.start()].strip()
            
        # ── 서명란 제거 ────────────────────────────────────────
        # "본 계약을 증명하기 위하여" 이후는 서명란 → 분석 불필요
        sig_match = re.search(r'\n본 계약을 증명하기 위하여', contract_part)
        if sig_match:
            contract_part = contract_part[:sig_match.start()].strip()

        return contract_part, annex_part

    def parse_articles(self, text: str) -> list[dict]:
        """
        계약서 본문 텍스트를 조항(제1조, 제2조...) 단위로 파싱합니다.
        PoC 핵심 로직 — 이게 잘 돼야 RAG, LLM 단계가 의미 있음.

        [핵심 설계 결정]
        줄 시작(^) + 제N조 + 괄호 제목 패턴만 실제 조항으로 인식.
        본문 중간의 법령 참조문("상가건물임대차보호법 제10조의4제1항")은
        줄 시작이 아니므로 걸러짐.

        반환 예시:
        [
            {"article_id": "제1조", "title": "보증금과 차임", "content": "제1조(보증금과 차임) ..."},
            {"article_id": "제2조", "title": "임대차기간",    "content": "제2조(임대차기간) ..."},
        ]
        """

        # ── 줄 시작 조항 패턴만 매칭 ──────────────────────────
        # (?m) = MULTILINE: ^가 각 줄의 시작을 의미 (Java의 Pattern.MULTILINE 과 동일)
        # [（(]  = 전각/반각 여는 괄호 모두 허용
        # 매칭 예: "제1조(보증금과 차임)" →  
        # 비매칭 예: "...보호법 제10조의4제1항..." →  (줄 시작 아님)
        # (?m)   = MULTILINE 모드
        # [ \t]* = 줄 앞 공백/탭 허용 (pdfplumber가 들여쓰기 추가하는 경우 대응)
        # 예: "제1조(" O "  제1조(" x "본문 중 제1조"  (줄 시작 아님)
        pattern = r'(?m)^[ \t]*(제\d+조(?:의\d+)?)\s*[（(]'
        matches = list(re.finditer(pattern, text))

        articles = []
        for i, match in enumerate(matches):
            article_id = match.group(1)

            # 현재 조항 시작 ~ 다음 조항 시작 직전까지가 이 조항의 전체 내용
            # Java의 substring(start, end) 와 동일
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            content = text[start:end].strip()

            # 제목 추출: "제N조(제목)" 에서 괄호 안 텍스트
            title_match = re.match(r'제\d+조(?:의\d+)?\s*[（(](.+?)[）)]', content)
            title = title_match.group(1) if title_match else article_id

            articles.append({
                "article_id": article_id,
                "title": title,
                "content": content,
            })

        return articles

    # ── 2단계 예정: Clova OCR 연동 ────────────────────────────
    # async def _call_clova_ocr(self, file_bytes: bytes) -> str:
    #     """
    #     Naver Clova OCR API 호출
    #     스캔 PDF, 핸드폰 촬영 이미지 처리용
    #     Free 플랜: 월 100건 무료
    #     """
    #     raise NotImplementedError("Clova OCR — 2단계에서 구현 예정")