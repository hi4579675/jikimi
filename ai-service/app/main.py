from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import analyze
from app.models.schemas import HealthResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    # TODO: DB 커넥션 풀, Redis 클라이언트 초기화
    yield
    # TODO: 리소스 정리

# FastAPI 인스턴스 생성
# 여기서 만든 app 객체를 uvicorn이 받아서 서버를 띄움
app = FastAPI(
    title="계약지킴이 AI Service",
    description="상가 임대차 계약서 분석 API",
    version="0.1.0",
    lifespan=lifespan,
)

# 라우터 등록
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])

# Health Check 엔드포인트, 서버 살아 있는지
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")
