# SmallStep 라우터 패키지 (v2 아키텍처)
from fastapi import APIRouter

# 분리된 라우터들 import
from . import goals, users, llm, system, phases, weekly_plans, tasks, stats

# 통합 라우터 생성
router = APIRouter()

# 각 라우터의 라우터들을 통합 라우터에 포함
router.include_router(goals.router)
router.include_router(users.router)
router.include_router(llm.router)
router.include_router(system.router)
router.include_router(phases.router)
router.include_router(weekly_plans.router)
router.include_router(tasks.router)
router.include_router(stats.router)

# main.py에서 사용할 수 있도록 별칭 추가
smallstep = router