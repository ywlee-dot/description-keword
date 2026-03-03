# 데이터셋 키워드 & 설명 생성 도구

엑셀(xlsx) 또는 CSV 데이터 정의서를 그룹 단위로 묶어 **키워드 8개**와 **설명문(250~350자 미만, 공백 미포함)**을 생성합니다.  
OpenAI 호환 Chat Completions API 또는 Google Gemini API를 사용할 수 있으며, 로컬 Web UI(FastAPI)도 제공합니다.

## 기능

1. **헤더 자동 탐지/병합** - 상단 30행을 스캔해 1~2행 헤더를 자동 선택
2. **그룹화** - 번호/연속 증가 숫자열/데이터셋명 등 기준으로 행 묶기
3. **프롬프트 생성** - `prompt.txt` 템플릿에 그룹 요약 정보 삽입
4. **LLM 호출** - 키워드 8개 + 설명문 JSON 응답 생성
5. **결과 출력** - JSON 배열로 저장(필드 선택 가능)

## 설치

```bash
pip install -r requirements.txt
```

## 필수 파일

1. **입력 파일** - `.xlsx` 또는 `.csv`
2. **prompt.txt** - 프롬프트 템플릿(기본 제공, 필요 시 수정)

## 환경 변수

```bash
export OPENAI_API_KEY="..."   # OpenAI용
# 또는
export GEMINI_API_KEY="..."   # Gemini용

# OpenAI용 (기본값)
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENAI_MODEL="gpt-4o-mini"

# Gemini용 (기본값)
export GEMINI_BASE_URL="https://generativelanguage.googleapis.com/v1beta"
export GEMINI_MODEL="gemini-2.5-flash"

export PROMPT_PATH="prompt.txt"
```

## 사용 방법 (CLI)

```bash
python generate_dataset_summary.py --input input.xlsx --output output.json
```

CSV도 지원합니다.

```bash
python generate_dataset_summary.py --input input.csv --output output.json
```

### CLI 옵션

- `--input PATH` 입력 파일 경로(.xlsx/.csv)
- `--output PATH` 출력 JSON 경로
- `--sheet SHEET_NAME` 시트명(xlsx만)
- `--header-start CELL` 헤더 시작 셀(예: A1)
- `--header-end CELL` 헤더 끝 셀(예: G2)
- `--group-key HEADER` 그룹 기준 헤더명(기본: 자동 탐색)
- `--org-name NAME` 프롬프트 템플릿의 기관명 치환 값
- `--sleep SECONDS` 요청 간 지연(초)
- `--include-row` 결과에 원본 행 포함
- `--debug` 헤더 탐지 디버그 정보 포함
- `--base-url URL` LLM API base URL
- `--model MODEL` LLM 모델명

## Local Web UI (FastAPI)

```bash
export OPENAI_API_KEY="..."   # 또는 GEMINI_API_KEY
uvicorn server:app --reload --port 8000
```

브라우저에서 `http://localhost:8000` 접속

### Mock Mode

API 비용 없이 테스트하려면:

```bash
export MOCK_MODE=1
uvicorn server:app --reload --port 8000
```

## 프롬프트 템플릿

`prompt.txt`를 수정하여 프롬프트 템플릿을 변경할 수 있습니다.

- `{row_text}`: 그룹화된 입력 텍스트
- `{기관명}`: 기관명 치환 값(`--org-name` 또는 UI 입력)
- `{개방 데이터셋명}`: 그룹에서 추출한 데이터셋명

기본 템플릿은 다음을 요구합니다:

- JSON만 출력: `{"keywords":[...], "description":"..."}`
- keywords: **정확히 8개**, 짧은 명사형
- description: **공백 미포함 250자 이상 350자 미만**
- 공공기관 톤("~니다/~습니다")

## 헤더 탐지 (Auto)

헤더 범위를 지정하지 않으면 상단 30행을 스캔해 1~2행 헤더를 점수화하여 선택합니다.

- 토큰 점수: `번호, 개방, 데이터셋, 정보시스템, 테이블, 컬럼, 영문, 한글, 비고, 개방시기`
- 행 품질: 채움 셀 수가 많을수록 가점, 숫자/긴 텍스트 위주는 감점
- 2행 헤더 판단: 2행이 데이터 같으면 1행으로 강제
- 컬럼 범위: 마지막 값이 있는 컬럼 기준
- 2행 헤더 병합: `상위 / 하위` 형식으로 병합 후 빈 헤더는 앞값으로 채움

## 그룹화 (Default)

`--group-key`를 지정하지 않으면 다음 우선순위로 자동 선택합니다.

1. `번호`
2. 상단 샘플에서 연속 증가하는 숫자열 컬럼
3. `데이터셋명`, `개방 데이터셋명`
4. 첫 번째 유효 헤더 컬럼

## 출력 구조

출력은 JSON 배열이며 각 항목은 다음 필드를 포함합니다.

- `row_index`: 1부터 시작하는 그룹 인덱스
- `group_key`: 그룹 키 값
- `common`: 공통 정보(번호/데이터셋명/테이블명 등)
- `columns`: 컬럼명 목록
- `keywords`: 키워드 8개
- `description`: 설명문
- `prompt`: 프롬프트(옵션)
- `rows`: 원본 행(옵션)
- `debug`: 헤더 탐지 정보(옵션)

## CSV 인코딩

CSV는 `utf-8-sig`, `utf-8`, `cp949` 순서로 디코딩을 시도합니다.

## 주요 특징

- **OpenAI/Gemini 동시 지원**
- **자동 헤더 탐지 + 2행 헤더 병합**
- **그룹 기준 자동 탐색**
- **Mock 모드 제공** (API 비용 없이 테스트)
