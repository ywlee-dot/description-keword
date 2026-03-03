# Handbook RAG Design

**Goal:** HWP/HWPX/DOCX/PDF 기반 평가편람을 정확한 출처(페이지 + 표 번호/절 경로)와 함께 질의응답할 수 있는 하이브리드 RAG 파이프라인을 설계한다.

**Scope:** 로컬 환경에서 시작하되, 향후 온프렘/클라우드 확장을 고려한 구조. 문서 누적량 50~500건, 배치 처리 중심, UI 포함.

## 핵심 원칙

1. **출처 형식 고정:** 모든 답변은 `페이지 + (표 번호/절 경로)`를 포함한다.
2. **표는 2트랙 저장:**
   - 구조 JSON: 정확성 검증(배점/기준값/기간)
   - 직렬화 텍스트: 검색/리트리벌
3. **페이지 앵커는 PDF 기준:** 텍스트/표는 HWPX/DOCX, 페이지/좌표는 PDF로 매핑.
4. **숫자 재검증 필수:** 답변 시 숫자는 표 JSON 또는 원문 블록으로 재확인.

## 입력/변환

- 입력: HWP/HWPX/DOCX/PDF 혼재.
- 변환 순서:
  1) 가능한 경우 HWP → HWPX 변환
  2) 동시에 PDF 생성
  3) HWPX 불가 시 DOCX + PDF 동시 확보
- 변환 결과는 `source_files`로 문서 메타에 기록.

## 파싱/블록 분해

- 블록 타입: `heading`, `paragraph`, `table`, `note/footnote`
- `section_path` 누적 예시: `2장 데이터기반행정 > 2.1 평가개요 > 2.1.3 산정기준`
- 표는 즉시 구조 JSON + 직렬화 텍스트로 분리 저장.

## 표 처리

(A) **구조 JSON**
- `table_no`, `title`, `headers`, `rows`, `merged_cells`, `notes/footnotes`
- 배점/기준값/기간 숫자 검증의 기준 데이터

(B) **직렬화 텍스트**
- `표 제목 + 열 정의 + 행 요약`을 문장으로 구성
- 벡터/키워드 검색에 최적화

## 페이지 매핑(PDF 기준)

- PDF를 페이지별 텍스트(라인 단위)로 추출
- 블록 텍스트 앞부분을 fuzzy match(n-gram/유사도)로 매핑
- 표는 `표 제목` 우선 매핑
- 결과: `page_start`, `page_end` 저장

## 정규화(클린업)

- 머리말/꼬리말/쪽번호 제거
- 숫자+단위 표현 보존(예: `15점 이상`, `90% 이상`)
- 목록 기호(`·`, `-`, `~`) 삭제 금지

## 청킹

- 문단 청크: `section_path` 기준으로 묶되 300~800 토큰 분할
- 표 청크: 1개 표 = 1청크
- `평가방법/산식/기준값/인정기간/마감일` 포함 문장은 분할 금지
- 메타데이터 필수: `doc_id`, `year`, `section_path`, `page_start/end`, `block_type`, `table_id?`

## 인덱싱

- **Vector index**: 의미 기반 검색
- **BM25 index**: 표 번호/지표명/숫자/기간 등 키워드 검색
- 최종 검색은 두 결과를 합쳐 rerank

## QA/서빙 로직

1. 하이브리드 검색 top-k
2. 표 청크 우선순위 상승
3. 답변 생성 전 숫자/기준/기간을 표 JSON/원문에서 재확인
4. 문장마다 출처 표기: `페이지 + (표 번호/절 경로)`

## 검증(테스트)

- 표 30개 랜덤: 배점/기준값/기간 숫자 diff (정합성 100% 목표)
- 청크 50개 랜덤: 표기된 페이지로 실제 존재 확인
- 골든 질문 30개: Recall@5, 숫자 정합성 100% 목표

## 운영/버전 전략

- 문서 버전 분리: `doc_id=handbook_2025`, `handbook_2026`
- 기본 검색은 최신 버전, 필요 시 연도 필터
- 골든 질문 회귀 테스트 유지

## 데이터 스키마(요약)

- `documents`: doc_id, year, title, source_files, ingested_at, version_tag
- `blocks`: block_id, doc_id, block_type, section_path, text, page_start/end, order_index, table_id?
- `tables`: table_id, doc_id, table_no, title, section_path, table_json, table_text, page_start/end
- `chunks`: chunk_id, doc_id, block_type, section_path, text, page_start/end, table_id?, metadata
- `embeddings`: chunk_id, vector
- `bm25`: tsvector or external index

## UI 범위(초기)

- 문서 업로드 + 상태(변환/파싱/인덱싱) 진행 표시
- 검색/질의 UI: 출처(페이지/표번호/절 경로) 표시
- 표 구조 JSON 보기(숫자 검증용)

## 확장 고려

- 로컬 -> 온프렘/클라우드 확장 가능하도록 파일 저장/DB/인덱싱 계층 분리
- 파이프라인 단계별 재처리(idempotent) 지원

