from pydantic import BaseModel

from typing import Optional
 
 
# ── 분석 요청 DTO ──────────────────────────────────────────────
class AnalyzeRequest(BaseModel):
    # S3에 저장된 파일 키 (Spring Boot가 S3 업로드 후 FastAPI로 전달하는 값)
    s3_key: str
    # 요청한 사용자 ID (Spring Boot가 JWT에서 추출해서 같이 넘겨줌)
    user_id: str
 
 
# ── 조항 단위 분석 결과 ────────────────────────────────────────
# 계약서 한 조항(제3조, 제4조...)을 파싱한 결과 구조체
class ArticleAnalysis(BaseModel):
    article_id: str            # 조항 번호 (예: "제3조")
    title: str                 # 조항 제목 (예: "임대료")
    content: str               # 조항 내용 원문
    risk_level: str            # 위험도: "HIGH" | "MEDIUM" | "LOW" | "SAFE"
    risk_reason: Optional[str] # 위험한 이유 (GPT-4o가 생성)
    legal_ref: Optional[str]   # 관련 법령 (예: "상가건물 임대차보호법 제11조")
    suggestion: Optional[str]  # 수정 제안 (GPT-4o가 생성)
 
 
# ── 전체 분석 응답 DTO ─────────────────────────────────────────
class AnalyzeResponse(BaseModel):
    contract_id: str                    # 계약서 식별자
    total_articles: int                 # 전체 조항 수
    high_risk_count: int                # 고위험 조항 수
    articles: list[ArticleAnalysis]     # 조항별 분석 결과 목록
    summary: str                        # 전체 요약 (GPT-4o가 생성)
 
 
# ── 에러 응답 DTO ──────────────────────────────────────────────
class ErrorResponse(BaseModel):
    error_code: str    # 예: "OCR_FAILED", "LLM_TIMEOUT"
    message: str       # 사용자에게 보여줄 메시지
 