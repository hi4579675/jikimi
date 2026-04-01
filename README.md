# 계약지킴이 (Jikimi)

> 소상공인 임대차 계약서 AI 분석 서비스  
> 계약서 업로드 → 독소조항 자동 탐지 | OCR · RAG · LLM 파이프라인

## 프로젝트 목적

소상공인이 임대차 계약서(PDF/이미지)를 업로드하면, OCR → 구조화 → RAG 기반 법령 대조 → 독소 조항 리포트를 자동 생성하는 AI 서비스입니다.

변호사 검토 비용 부담으로 계약서를 제대로 확인하지 못하는 자영업자를 위해 만들었습니다.

---

## 시스템 아키텍처

```
[사용자]
   │ PDF 업로드
   ▼
[Spring Boot]
   ├─ 인증(JWT) / 계약 이력 CRUD / S3 저장 / 알림
   ├─ AIServiceClient (인터페이스 추상화)
   │    ├─ FastAPIAIServiceClient  ← 실제 AI 서버 호출
   │    ├─ CachedAIServiceClient   ← 캐시 Fallback
   │    └─ MockAIServiceClient     ← 테스트용
   └─ Circuit Breaker (Resilience4j) — AI 장애 시 자동 차단 + fallback
   │ 202 Accepted + job_id (비동기)
   ▼
[FastAPI AI 서버]
   └─ OCR → 조항 파싱 → Hybrid RAG → LLM 분석
```

**Spring AI 통합 설계 포인트**
- `AIServiceClient` 인터페이스로 AI 서비스 추상화 — 구현체 교체, 테스트 용이
- Resilience4j Circuit Breaker + TimeLimiter — FastAPI·LLM API 장애 격리 및 fallback
- 202 Accepted + polling 패턴 — 수십 초 걸리는 AI 분석을 비동기로 처리

### 기술 스택

| 영역 | 기술 |
|------|------|
| AI 서버 | FastAPI + Python |
| 백엔드 | Spring Boot + Resilience4j |
| LLM | GPT-4o API |
| RAG | pgvector Hybrid (BM25 + Vector, RRF 병합) |
| 벡터 DB | PostgreSQL + pgvector |
| OCR | pdfplumber → Naver Clova OCR (Phase 2~) |
| 캐시 | Redis (Phase 1~) |
| 파일 저장 | AWS S3 (Phase 3~) |

<br>

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java_17-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-FF4438?style=for-the-badge&logo=redis&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-FF9900?style=for-the-badge&logo=amazons3&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

---

## 개발 현황

| 단계 | 내용 | 상태 |
|---|---|---|
| Phase 0 | OCR + RAG PoC (기술 검증) | ✅ 완료 |
| Phase 1 | FastAPI LLM 분석 + 엔드투엔드 파이프라인 | 진행 중 |
| Phase 2 | Spring Boot 연동 (인증, AIServiceClient, Circuit Breaker) | 예정 |
| Phase 3 | React 프론트 + AWS 배포 | 예정 |

### Phase 0 PoC 결과

**OCR**: 표준계약서 2종, 12개 조항 100% 파싱 성공  
**RAG**: 4개 법령 검색 쿼리 모두 정확한 조문 1위 검색 (유사도 0.69~0.77)

---

## 로컬 실행 방법

### 1. 환경변수 설정

```bash
cp .env.example .env
# .env 파일에 API Key 입력
```

### 2. 인프라 실행

```bash
docker-compose up -d
# PostgreSQL(pgvector), Redis 실행
```

### 3. AI 서버 실행

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 4. 백엔드 서버 실행

```bash
cd backend
./gradlew bootRun
```

### 5. 동작 확인

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

---

## 문서

- [기획안](docs/기획안.md)
- [아키텍처 결정 기록](docs/decisions.md)
- [Phase 0 PoC 검증](docs/poc/poc-phase0.md)
- [API 명세](docs/analyze-contract.md)
- [테스트 로그](docs/testing-log.md)
- [변경 이력](docs/changelog.md)
