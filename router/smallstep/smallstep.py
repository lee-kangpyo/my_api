from fastapi import APIRouter

# 분리된 라우터들 import
from router.smallstep.users import router as users_router
from router.smallstep.goals import router as goals_router
from router.smallstep.activities import router as activities_router
from router.smallstep.game_data import router as game_data_router
from router.smallstep.system import router as system_router
from router.smallstep.llm import router as llm_router
from router.smallstep.search import router as search_router

# 메인 라우터 생성
router = APIRouter()

# 모든 서브 라우터 포함
router.include_router(users_router)
router.include_router(goals_router)
router.include_router(activities_router)
router.include_router(game_data_router)
router.include_router(system_router)
router.include_router(llm_router)
router.include_router(search_router) 