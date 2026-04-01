# API Contract: Analyze

- **File Path**: `docs/api/analyze-contract.md`
- **Version**: v1.0.0
- **Last Updated**: 2026-04-01
- **Status**: Draft

## 0. Revision History

| Version | Date | Author | Change Type | Summary |
|---------|------|--------|-------------|---------|
| v1.0.0 | 2026-04-01 | 본인 | Added | 초기 계약서 작성 |

---

## 1. 개요

계약서 PDF를 입력받아 조항별 위험도를 분석하는 `ai-server`(FastAPI) 핵심 API.  
`backend`(Spring Boot)에서 내부 호출한다.

- **Method**: `POST`
- **Path**: `/analyze`
- **Content-Type**: `multipart/form-data`
- **Caller**: `backend` only (internal)

---

## 2. Request

### 2.1 Header

| Header Name | Required | Description | Example |
|-------------|----------|-------------|---------|
| `X-Correlation-ID` | Yes | 분산 추적용 UUID v4 | `550e8400-e29b-41d4-a716-446655440000` |

### 2.2 Body (multipart/form-data)

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `file` | File | Yes | PDF, 최대 10MB | 계약서 파일 |
| `contract_id` | String | Yes | UUID | Spring Boot에서 발급한 계약 ID |

---

## 3. Response

### 3.1 Success (200 OK)

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | String | 요청의 contract_id 그대로 반환 |
| `analyzed_at` | String | 분석 완료 시각 (ISO 8601) |
| `articles` | Array[Article] | 조항별 분석 결과 |
| `summary` | Summary | 전체 위험도 요약 |
| `correlation_id` | String | 요청의 X-Correlation-ID 그대로 반환 |

#### Article

| Field | Type | Description |
|-------|------|-------------|
| `article_id` | String | 조항 번호 (예: 제3조) |
| `title` | String | 조항 제목 |
| `content` | String | 조항 원문 |
| `risk_level` | String | `HIGH / MEDIUM / LOW` |
| `risk_reason` | String | 위험 이유 설명 (한글) |
| `legal_ref` | String | 관련 법령 조항 |

#### Summary

| Field | Type | Description |
|-------|------|-------------|
| `total_articles` | Integer | 전체 조항 수 |
| `high_risk` | Integer | HIGH 건수 |
| `medium_risk` | Integer | MEDIUM 건수 |
| `low_risk` | Integer | LOW 건수 |

#### risk_level 정의

| 값 | 의미 |
|----|------|
| `HIGH` | 법령 위반 가능성 높음, 즉시 검토 필요 |
| `MEDIUM` | 불리한 조항이나 법령 위반은 아님 |
| `LOW` | 일반적인 수준 |

### 3.2 Error (4xx/5xx)

| Field | Type | Description |
|-------|------|-------------|
| `code` | String | 에러 코드 |
| `message` | String | 에러 상세 |
| `correlation_id` | String | 추적 ID |

#### Error Code

| Code | HTTP | 원인 |
|------|------|------|
| `INVALID_FILE_TYPE` | 400 | PDF 외 파일 |
| `FILE_TOO_LARGE` | 400 | 10MB 초과 |
| `OCR_FAILED` | 422 | 텍스트 추출 실패 |
| `PARSE_FAILED` | 422 | 계약서 구조 미인식 |
| `LLM_ERROR` | 500 | OpenAI API 오류 |
| `TIMEOUT` | 504 | 처리 시간 초과 |

---

## 4. JSON Samples

### 4.1 Request Example

```bash
curl -X POST http://localhost:8000/analyze \
  -H "X-Correlation-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -F "file=@contract.pdf" \
  -F "contract_id=abc-123"
```

### 4.2 Success Example (200)

```json
{
  "contract_id": "abc-123",
  "analyzed_at": "2026-04-01T12:00:00Z",
  "articles": [
    {
      "article_id": "제3조",
      "title": "임대료",
      "content": "임대료는 월 300만 원으로 하며 매년 10% 인상한다.",
      "risk_level": "HIGH",
      "risk_reason": "상가임대차보호법 제11조 차임 증액 상한(5%)을 초과합니다.",
      "legal_ref": "상가건물 임대차보호법 제11조"
    }
  ],
  "summary": {
    "total_articles": 10,
    "high_risk": 1,
    "medium_risk": 3,
    "low_risk": 6
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 4.3 Error Example (422)

```json
{
  "code": "OCR_FAILED",
  "message": "텍스트를 추출할 수 없습니다. 파일 품질을 확인해주세요.",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 5. Validation Rules

- `file`: PDF만 허용, 최대 10MB
- `contract_id`: 필수, UUID 형식
- `X-Correlation-ID` 누락 시 `422` 반환

---

## 6. Timeout Policy

| 단계 | 타임아웃 |
|------|----------|
| OCR 처리 | 30s |
| RAG 검색 | 10s |
| LLM 분석 | 60s |
| 전체 요청 | 120s |

---

## 7. Non-Goals (현재 버전)

- 핸드폰 촬영 이미지 지원 (Phase 2~)
- 이미지 PDF(스캔본) 지원 (Phase 2~)
- 실시간 판례 업데이트 반영