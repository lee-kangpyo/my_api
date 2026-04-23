from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_USERS, SMALLSTEP_GOALS, SMALLSTEP_TASKS, SMALLSTEP_WEEKLY_PLANS, SMALLSTEP_ACTIVITY_LOG
from schemas.smallstep.stats import StatsOverview, WeeklyStats, StreakInfo
from typing import List
import logging
from sqlalchemy import func
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 통계 관리"]
)

@router.get("/stats/overview", response_model=StatsOverview,
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

@router.get("/stats/weekly", response_model=List[WeeklyStats],
            summary="주간 통계 조회")
def get_weekly_stats(user_id: int, db: Session = Depends(get_smallstep_db)):
    """최근 4주의 주간 통계(완료, 스킵, 완료율 등)를 반환합니다."""
    # 간단히 가장 최근 4개의 주간 계획 정보를 집계합니다.
    recent_plans = (
        db.query(SMALLSTEP_WEEKLY_PLANS)
        .join(SMALLSTEP_GOALS)
        .filter(SMALLSTEP_GOALS.USER_ID == user_id)
        .order_by(SMALLSTEP_WEEKLY_PLANS.WEEK_START_DATE.desc())
        .limit(4)
        .all()
    )
    
    result = []
    for plan in recent_plans:
        tasks = db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.WEEKLY_PLAN_ID == plan.ID).all()
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.STATUS == 'COMPLETED')
        skipped = sum(1 for t in tasks if t.STATUS == 'SKIPPED')
        
        completion_rate = int((completed / total_tasks * 100) if total_tasks > 0 else 0)
        
        # XP Earned in this week: from ACTIVITY_LOG
        xp_earned = db.query(func.sum(SMALLSTEP_ACTIVITY_LOG.XP_EARNED)).filter(
            SMALLSTEP_ACTIVITY_LOG.USER_ID == user_id,
            SMALLSTEP_ACTIVITY_LOG.CREATED_AT >= plan.WEEK_START_DATE,
            SMALLSTEP_ACTIVITY_LOG.CREATED_AT <= plan.WEEK_END_DATE
        ).scalar() or 0
        
        result.append(WeeklyStats(
            week_start_date=plan.WEEK_START_DATE,
            week_end_date=plan.WEEK_END_DATE,
            tasks_completed=completed,
            tasks_skipped=skipped,
            completion_rate=completion_rate,
            xp_earned=xp_earned
        ))
    return result

@router.get("/stats/streak", response_model=StreakInfo,
            summary="스트릭 정보 조회")
def get_streak_info(user_id: int, db: Session = Depends(get_smallstep_db)):
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    
    # 오늘 스트릭 활성화 여부
    is_streak_active_today = db.query(SMALLSTEP_ACTIVITY_LOG).filter(
        SMALLSTEP_ACTIVITY_LOG.USER_ID == user_id,
        SMALLSTEP_ACTIVITY_LOG.ACTION == 'COMPLETED',
        SMALLSTEP_ACTIVITY_LOG.CREATED_AT >= today_start
    ).count() > 0
    
    # 마지막 활동 일자
    last_log = db.query(SMALLSTEP_ACTIVITY_LOG).filter(
        SMALLSTEP_ACTIVITY_LOG.USER_ID == user_id,
        SMALLSTEP_ACTIVITY_LOG.ACTION == 'COMPLETED'
    ).order_by(SMALLSTEP_ACTIVITY_LOG.CREATED_AT.desc()).first()
    
    return StreakInfo(
        current_streak=user.CURRENT_STREAK or 0,
        longest_streak=user.LONGEST_STREAK or 0,
        is_streak_active_today=is_streak_active_today,
        last_activity_date=last_log.CREATED_AT if last_log else None
    )
