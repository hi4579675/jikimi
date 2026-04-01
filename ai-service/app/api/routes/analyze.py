# ─────────────────────────────────────────────────────────────
# Spring의 @RestController 역할
# @RequestMapping("/api/v1") + @PostMapping("/analyze") 와 동일
# ─────────────────────────────────────────────────────────────

import uuid

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.schemas import AnalyzeResponse
from app.services.llm_service import LlmService
from app.services.ocr_service import OcrService
from app.services.rag_service import RagService

router = APIRouter()

# 서비스 인스턴스 생성
# (추후 Depends() 로 의존성 주입 방식으로 전환 가능)
ocr_service = OcrService()
rag_service = RagService()
llm_service = LlmService()


# ── POST /api/v1/analyze ───────────────────────────────────────
@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_contract(file: UploadFile = File(...)) -> AnalyzeResponse:
    """
    계약서 PDF를 받아서 독소 조항 분석 결과를 반환합니다.

    파이프라인:
    1. OCR       → PDF에서 텍스트 추출
    2. 전처리    → 노이즈 제거 + 별지 분리 + 조항 파싱
    3. RAG       → 관련 법령 검색
    4. LLM       → GPT-4o로 위험 조항 판단 및 리포트 생성
    """
    try:
        # ── STEP 1. OCR: PDF → 원본 텍스트 추출 ──────────────────
        # pdfplumber로 텍스트 레이어 추출 (PoC 1단계)
        # 텍스트 레이어 없으면 Clova OCR 호출 (2단계 예정)
        raw_text: str = await ocr_service.extract_text(file)

        if not raw_text:
            raise HTTPException(status_code=422, detail="계약서에서 텍스트를 추출할 수 없습니다.")

        # ── STEP 2. 전처리: 노이즈 제거 + 별지 분리 ──────────────
        # 반드시 parse_articles() 전에 호출해야 함
        # clean 안 된 텍스트로 파싱하면 서명란/별지가 마지막 조항에 붙어버림
        # Spring으로 치면 서비스 레이어에서 전처리 후 다음 단계로 넘기는 것과 동일
        contract_text, annex_text = ocr_service.clean_text(raw_text)

        # ── STEP 3. 조항 파싱: 텍스트 → 조항 리스트 ──────────────
        # 줄 시작 "제N조(제목)" 패턴만 실제 조항으로 인식
        # 법령 참조문(본문 중간의 제10조의4 등) 오탐 방지
        articles: list[dict] = ocr_service.parse_articles(contract_text)

        if not articles:
            raise HTTPException(status_code=422, detail="계약서 조항을 찾을 수 없습니다. 계약서 형식을 확인해주세요.")

        # ── STEP 4. RAG: 관련 법령 검색 ───────────────────────────
        # 정제된 contract_text 기준으로 검색
        # annex_text(별지)는 추후 RAG 지식베이스에 추가 예정
        legal_contexts = await rag_service.search_legal_context(contract_text)

        # ── STEP 5. LLM: GPT-4o 위험도 분석 ──────────────────────
        # 조항 리스트 + 관련 법령을 GPT-4o에 넣고 위험도 판단 요청
        # 응답을 AnalyzeResponse 스키마로 파싱
        analysis_result: AnalyzeResponse = await llm_service.analyze(articles, legal_contexts)

        return analysis_result

    except HTTPException:
        raise  # 위에서 명시적으로 던진 HTTPException은 그대로 전달
    except NotImplementedError as e:
        # 미구현 서비스 호출 시 → 501 Not Implemented
        raise HTTPException(status_code=501, detail=f"미구현: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── GET /api/v1/analyze/health ─────────────────────────────────
# 파이프라인 개별 컴포넌트 상태 확인용 (개발 중 디버깅 편의)
@router.get("/analyze/health")
async def analyze_health() -> dict:
    return {
        "ocr": "ready",    # TODO: Clova OCR 연결 상태 확인
        "rag": "ready",    # TODO: pgvector 연결 상태 확인
        "llm": "ready",    # TODO: OpenAI API 키 유효성 확인
    }