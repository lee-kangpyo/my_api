# SmallStep 라우터 패키지
from fastapi import APIRouter
from . import activities, goals, users, game_data, llm, system

# 통합 라우터 생성
router = APIRouter()

# 각 라우터의 라우터들을 통합 라우터에 포함
router.include_router(activities.router)
router.include_router(goals.router)
router.include_router(users.router)
router.include_router(game_data.router)
router.include_router(llm.router)
router.include_router(system.router) 