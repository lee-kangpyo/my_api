# SmallStep 라우터 패키지
from fastapi import APIRouter

# 분리된 라우터들 import
from . import activities, goals, users, game_data, llm, system, keywords, onboarding

# 통합 라우터 생성
router = APIRouter()

# 각 라우터의 라우터들을 통합 라우터에 포함
router.include_router(activities.router)
router.include_router(goals.router)
router.include_router(users.router)
router.include_router(game_data.router)
router.include_router(llm.router)
router.include_router(system.router)
router.include_router(keywords.router)
router.include_router(onboarding.router)

# main.py에서 사용할 수 있도록 별칭 추가
smallstep = router