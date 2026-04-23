from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_USERS, SMALLSTEP_GOALS, SMALLSTEP_TASKS, SMALLSTEP_WEEKLY_PLANS
from schemas.smallstep.stats import StatsOverview, WeeklyStats, StreakInfo
from typing import List
import logging
from sqlalchemy import func

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 통계 관리"]
)

@router.get("/stats/overview/{user_id}", response_model=StatsOverview,
            summary="전체 통계 조회")
def get_stats_overview(user_id: int, db: Session = Depends(get_smallstep_db)):
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    goals = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.USER_ID == user_id).all()
    total_goals = len(goals)
    completed_goals = sum(1 for g in goals if g.STATUS == 'COMPLETED')
    
    # 조인으로 사용자별 완료된 태스크 수집
    completed_tasks_count = (
        db.query(SMALLSTEP_TASKS)
        .join(SMALLSTEP_GOALS)
        .filter(SMALLSTEP_GOALS.USER_ID == user_id, SMALLSTEP_TASKS.STATUS == 'COMPLETED')
        .count()
    )
    
    return StatsOverview(
        total_goals=total_goals,
        completed_goals=completed_goals,
        current_level=user.LEVEL or 1,
        experience_points=user.EXPERIENCE_POINTS or 0,
        total_tasks_completed=completed_tasks_count
    )

@router.get("/stats/streak/{user_id}", response_model=StreakInfo,
            summary="스트릭 정보 조회")
def get_streak_info(user_id: int, db: Session = Depends(get_smallstep_db)):
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    # 최근 활동 내역에서 가장 마지막 작업 완료일 조회 (구현 단순화를 위해 None 반환 가능)
    # Post-MVP: 활동 로그 테이블에서 조회 구현
    
    return StreakInfo(
        current_streak=user.CURRENT_STREAK or 0,
        longest_streak=user.LONGEST_STREAK or 0,
        is_streak_active_today=False, # MVP 임시값
        last_activity_date=None
    )
