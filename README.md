# SmallStep Backend (V2 Adaptive)

SmallStep 프로젝트의 백엔드 서버입니다. V2 아키텍처인 **주간 적응형 AI 코칭(Weekly Adaptive AI Coaching)** 시스템을 완벽히 지원하며, 고성능 패키지 관리와 타입 안전한 AI 파이프라인, 그리고 표준화된 코드 베이스를 구축했습니다.

## 🌟 V2 핵심 기능 

### 1. Modernized Infrastructure (uv & Snake Case)
- **uv Integration**: `pip` 대비 압도적인 속도의 패키지 설치 및 정교한 의존성 관리(`pyproject.toml`, `uv.lock`)를 지원합니다.
- **Full Snake Case Refactoring**: 데이터베이스 컬럼명부터 Pydantic 스키마, SQLAlchemy 모델, 라우터 및 서비스 레이어까지 모든 코드 베이스를 `snake_case`로 통일하여 가독성과 개발 생산성을 극대화했습니다.
- **Alembic Migration**: 스키마 변경 이력을 버전별로 관리하여 안전한 데이터베이스 마이그레이션이 가능합니다.

### 2. Adaptive AI Coaching Pipeline
- **LiteLLM + Instructor**: 다양한 LLM 모델(Gemini 등)을 유연하게 전환하며, Instructor를 통해 타입 안전한 구조화된 AI 응답을 처리합니다.
- **Phase & Weekly Planning**: 사용자의 목표를 단계별 Phase로 자동 분해하고, 매주 수행 데이터를 분석하여 최적화된 주간 계획을 생성합니다.

### 3. Sequential Task & Gamification
- **상태 머신 기반 태스크**: 태스크는 `LOCKED` → `AVAILABLE` → `COMPLETED` 시퀀스를 따르며, 단계별 성취감을 유도합니다.
- **XP & Leveling System**: 활동 결과에 따른 경험치 계산 및 레벨업 로직이 통합된 게임화 요소를 제공합니다.

## 🚀 기술 스택
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Infra**: [uv](https://github.com/astral-sh/uv), Alembic (Migration)
- **AI Engine**: LiteLLM, Instructor (Pydantic based extraction)
- **Database**: MySQL (SQLAlchemy ORM, Standard snake_case schema)
- **Vector Search**: BGE-M3 (GGUF) 기반 유사도 분석

## 🛠️ 개발 환경 구축

### 사전 요구 사항
- Python 3.11+
- [uv](https://github.com/astral-sh/uv) 설치 (`pip install uv`)

### 설치 및 실행
```bash
# 1. 의존성 설치 및 가상환경 동기화
uv sync

# 2. 데이터베이스 마이그레이션 (최신 스키마 적용)
uv run alembic upgrade head

# 3. 개발 서버 실행
uv run uvicorn main:app --reload --host=0.0.0.0 --port=8000
```

### 환경 변수 (.env)
```bash
# Database Connection
mysql=mysql+pymysql://user:password@host:port/database

# AI Configuration
GOOGLE_API_KEY=your_google_api_key
LITELLM_MODEL=gemini/gemini-1.5-flash
```

## 📂 API 구조 (V2)
- `/api/smallstep/goals`: 목표 생성 및 Phase 자동 연동
- `/api/smallstep/phases`: 페이즈별 상세 정보 및 진행도 조회
- `/api/smallstep/weekly-plans`: 주간 단위 적응형 계획 관리
- `/api/smallstep/tasks`: 일일 태스크 조회 및 완료 처리 (XP 연동)
- `/api/smallstep/stats`: 사용자 통계, XP, 레벨 정보

---
*SmallStep V2는 표준화된 코드와 AI 기술을 결합하여 최상의 사용자 경험을 제공합니다.*
