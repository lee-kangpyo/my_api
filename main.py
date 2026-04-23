# uvicorn main:app --reload
# uvicorn main:app --reload --host=0.0.0.0 --port=8000
import logging
from fastapi.logger import logger as fastapi_logger

from dotenv import load_dotenv
import os
from typing import Union
from fastapi import FastAPI

from router.lotto import lotto
from router.smallstep import smallstep


load_dotenv()
mode = os.getenv("MODE")

app = FastAPI(
    title="API Server",
    description="""
# 🚀 SmallStep & Lotto API 서버
이 서버는 두 개의 앱을 지원합니다:

## 📱 SmallStep 앱
목표 달성을 위한 게이미피케이션 앱

### 주요 기능:
- 🎯 **목표 관리**: 사용자별 목표 설정 및 추적
- 📊 **활동 관리**: 주차별, 일별 활동 스케줄링
- 🎮 **게이미피케이션**: 레벨, 경험치, 연속 성공일 시스템
- 👤 **사용자 관리**: 개인화된 진행 상황 추적

### API 엔드포인트 (v2 아키텍처):
- `/api/smallstep/users` - 사용자 통계 및 프로필 관리
- `/api/smallstep/goals` - 목표 설정 및 Phase 자동 생성
- `/api/smallstep/phases` - 목표 달성을 위한 단계(Phase) 관리
- `/api/smallstep/weekly-plans` - AI 기반 적응형 주간 계획 생성
- `/api/smallstep/tasks` - 오늘 할 일 및 완료 처리
- `/api/smallstep/stats` - 진행률, XP, 스트릭 통계
- `/api/smallstep/search` - AI 검색 서비스 (벡터/키워드/하이브리드)

## 🎰 Lotto 앱
로또 번호 추천 및 버그 신고 시스템

### 주요 기능:
- 🎲 **로또 추천**: 사용자 제안 시스템
- 🐛 **버그 신고**: 문제점 신고 및 이미지 업로드
- 📝 **피드백 관리**: 사용자 의견 수집

### API 엔드포인트:
- `/api/lotto/suggestion` - 기능 제안
- `/api/lotto/bug` - 버그 신고

## 🔧 기술 스택
- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: MySQL (로또 앱), MySQL (SmallStep 앱)
- **Server**: Uvicorn, Gunicorn
- **Documentation**: Swagger UI

## 📚 사용 방법
- 각 앱의 API 엔드포인트를 통해 데이터 관리
- Swagger UI에서 실시간 API 테스트 가능
- 데이터베이스에 자동 저장 및 조회

## 🔗 API 문서
- **Swagger UI**: `/api/docs`
- **OpenAPI JSON**: `/api/openapi.json`
- **버전 정보**: `/api/version`
    """,
    version="1.0.3",
    contact={
        "name": "AKMDZ",
        "email": "akmdz@naver.com"
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    docs_url="/api/docs", 
    openapi_url="/api/openapi.json", 
    redoc_url=None
)

if mode == "PROD":
    gunicorn_error_logger = logging.getLogger("gunicorn.error")
    gunicorn_logger = logging.getLogger("gunicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.handlers = gunicorn_error_logger.handlers
    fastapi_logger.handlers = gunicorn_error_logger.handlers
if mode == "PROD":
    fastapi_logger.setLevel(gunicorn_logger.level)
elif mode == "DEV":
    fastapi_logger.setLevel(logging.DEBUG)

@app.get("/api/version", description="API 서버 버전 정보", tags=["시스템"])
async def root():
    return [
        {"version": "1.0.3", "detail":"SmallStep API 추가", "date": "2025-08-05"},
        {"version": "1.0.2", "detail":"swagger 엔드포인트 수정"},
        {"version": "1.0.1", "detail":"로또 리포트 및 버그신고 기능 추가 및 nginx 내부 아이피 로깅 되는 이슈 픽스"},
        {"version": "1.0.0.0", "detail":"fastApi 시작"},
    ]


app.include_router(lotto.router)
app.include_router(smallstep)
