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
   │ PDF / 이미지 업로드
   ▼
[Spring Boot]  ─── 인증(JWT) / 계약 이력 CRUD / S3 저장 / 알림
   │ 내부 REST API
   ▼
[FastAPI]  ──────── OCR → 조항 파싱(AST) → Hybrid RAG → LLM 분석
   │
   ▼
[분석 리포트 JSON 반환]
```

### 기술 스택

| 영역 | 기술 |
|------|------|
| AI 서버 | FastAPI + Python |
| 백엔드 | Spring Boot |
| LLM | GPT-4o API |
| RAG | LangChain (BM25 + pgvector Hybrid) |
| 벡터 DB | PostgreSQL + pgvector |
| OCR | pdfplumber → Naver Clova OCR (Phase 2~) |
| 캐시 | Redis |
| 파일 저장 | AWS S3 (Phase 3~) |

<br>

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Spring Boot](https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white)
![Java](https://img.shields.io/badge/Java_17-ED8B00?style=for-the-badge&logo=openjdk&logoColor=white)
![OpenAI](https://img.shields.io/badge/GPT--4o-412991?style=for-the-badge&logo=openai&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-FF4438?style=for-the-badge&logo=redis&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-FF9900?style=for-the-badge&logo=amazons3&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)

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
cd ai-server
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
curl -X POST http://localhost:8000/health
# {"status": "ok"}
```

---

## 문서

- [기획안](docs/기획안.md)
- [아키텍처 결정 기록](docs/decisions.md)
- [API 명세](docs/analyze-contract.md)
- [테스트 로그](docs/testing-log.md)
- [변경 이력](docs/changelog.md)
