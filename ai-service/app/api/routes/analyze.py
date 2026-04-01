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


# 실제 경로: POST /api/v1/analyze
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
    1. OCR  → PDF에서 텍스트 추출
    2. RAG  → 관련 법령 검색
    3. LLM  → GPT-4o로 위험 조항 판단 및 리포트 생성
    """
    try:
        # ── STEP 1. OCR: PDF → 텍스트 추출 ───────────────────────
        # TODO: pdfplumber로 텍스트 레이어 추출 (PoC 1단계)
        # TODO: 텍스트 레이어 없으면 Clova OCR 호출 (2단계)
        raw_text: str = await ocr_service.extract_text(file)

        if not raw_text:
            raise HTTPException(status_code=422, detail="계약서에서 텍스트를 추출할 수 없습니다.")

        # ── STEP 2. RAG: 관련 법령 검색 ──────────────────────────
        # TODO: 텍스트를 조항 단위로 파싱 (제1조, 제2조...)
        # TODO: 각 조항에 대해 Hybrid RAG로 관련 법령 검색
        legal_contexts = await rag_service.search_legal_context(raw_text)

        # ── STEP 3. LLM: GPT-4o 위험도 분석 ─────────────────────
        # TODO: 조항 + 관련 법령을 GPT-4o에 넣고 위험도 판단 요청
        # TODO: 응답을 ArticleAnalysis 스키마로 파싱
        # TODO: contract_id, total_articles, high_risk_count 채우기
        analysis_result: AnalyzeResponse = await llm_service.analyze(raw_text, legal_contexts)

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
