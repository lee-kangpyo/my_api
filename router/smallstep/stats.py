from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_USERS, SMALLSTEP_GOALS, SMALLSTEP_PHASES, SMALLSTEP_TASKS, SMALLSTEP_WEEKLY_PLANS, SMALLSTEP_ACTIVITY_LOG
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
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    goals = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.user_id == user_id).all()
    total_goals = len(goals)
    completed_goals = sum(1 for g in goals if g.status == 'COMPLETED')
    
    # 조인으로 사용자별 완료된 태스크 수집
    completed_tasks_count = (
        db.query(SMALLSTEP_TASKS)
        .join(SMALLSTEP_GOALS)
        .filter(SMALLSTEP_GOALS.user_id == user_id, SMALLSTEP_TASKS.status == 'COMPLETED')
        .count()
    )
    
    # 완료된 Phase 수
    completed_phases_count = (
        db.query(SMALLSTEP_PHASES)
        .join(SMALLSTEP_GOALS)
        .filter(SMALLSTEP_GOALS.user_id == user_id, SMALLSTEP_PHASES.status == 'COMPLETED')
        .count()
    )
    
    # 다음 레벨까지 필요한 XP 계산
    current_level = user.level or 1
    current_xp = user.experience_points or 0
    next_level_xp = (current_level ** 2) * 100 - current_xp
    if next_level_xp < 0:
        next_level_xp = 0
    
    return StatsOverview(
        total_goals=total_goals,
        completed_goals=completed_goals,
        completed_phases_count=completed_phases_count,
        current_level=current_level,
        experience_points=current_xp,
        xp_to_next_level=next_level_xp,
        completed_tasks_count=completed_tasks_count,
        current_streak=user.current_streak or 0,
        longest_streak=user.longest_streak or 0
    )

@router.get("/stats/weekly", response_model=List[WeeklyStats],
            summary="주간 통계 조회")
def get_weekly_stats(user_id: int, db: Session = Depends(get_smallstep_db)):
    """최근 4주의 주간 통계(완료, 스킵, 완료율 등)를 반환합니다."""
    # 간단히 가장 최근 4개의 주간 계획 정보를 집계합니다.
    recent_plans = (
        db.query(SMALLSTEP_WEEKLY_PLANS)
        .join(SMALLSTEP_GOALS)
        .filter(SMALLSTEP_GOALS.user_id == user_id)
        .order_by(SMALLSTEP_WEEKLY_PLANS.week_start_date.desc())
        .limit(4)
        .all()
    )
    
    result = []
    for plan in recent_plans:
        tasks = db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.weekly_plan_id == plan.id).all()
        total_tasks = len(tasks)
        completed = sum(1 for t in tasks if t.status == 'COMPLETED')
        skipped = sum(1 for t in tasks if t.status == 'SKIPPED')
        
        completion_rate = int((completed / total_tasks * 100) if total_tasks > 0 else 0)
        
        # XP Earned in this week: from ACTIVITY_LOG
        xp_earned = db.query(func.sum(SMALLSTEP_ACTIVITY_LOG.xp_earned)).filter(
            SMALLSTEP_ACTIVITY_LOG.user_id == user_id,
            SMALLSTEP_ACTIVITY_LOG.completed_at >= plan.week_start_date,
            SMALLSTEP_ACTIVITY_LOG.completed_at <= plan.week_end_date
        ).scalar() or 0
        
        result.append(WeeklyStats(
            week_start_date=plan.week_start_date,
            week_end_date=plan.week_end_date,
            tasks_completed=completed,
            tasks_skipped=skipped,
            completion_rate=completion_rate,
            xp_earned=xp_earned
        ))
    return result

@router.get("/stats/streak", response_model=StreakInfo,
            summary="스트릭 정보 조회")
def get_streak_info(user_id: int, db: Session = Depends(get_smallstep_db)):
    user = db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        
    today_start = datetime.combine(datetime.now().date(), datetime.min.time())
    
    # 오늘 스트릭 활성화 여부
    is_streak_active_today = db.query(SMALLSTEP_ACTIVITY_LOG).filter(
        SMALLSTEP_ACTIVITY_LOG.user_id == user_id,
        SMALLSTEP_ACTIVITY_LOG.action == 'COMPLETED',
        SMALLSTEP_ACTIVITY_LOG.completed_at >= today_start
    ).count() > 0
    
    # 마지막 활동 일자
    last_log = db.query(SMALLSTEP_ACTIVITY_LOG).filter(
        SMALLSTEP_ACTIVITY_LOG.user_id == user_id,
        SMALLSTEP_ACTIVITY_LOG.action == 'COMPLETED'
    ).order_by(SMALLSTEP_ACTIVITY_LOG.completed_at.desc()).first()
    
    # 스트릭 시작일 계산
    streak_start_date = None
    current_streak = user.current_streak or 0
    if current_streak > 0:
        # ACTIVITY_LOG에서 역순으로 날짜별 활동 조회
        from sqlalchemy import distinct, cast, Date
        activity_dates = (
            db.query(distinct(cast(SMALLSTEP_ACTIVITY_LOG.completed_at, Date)))
            .filter(
                SMALLSTEP_ACTIVITY_LOG.user_id == user_id,
                SMALLSTEP_ACTIVITY_LOG.action == 'COMPLETED'
            )
            .order_by(cast(SMALLSTEP_ACTIVITY_LOG.completed_at, Date).desc())
            .limit(current_streak + 5)
            .all()
        )
        dates = [d[0] for d in activity_dates]
        
        # 오늘부터 역순으로 연속 날짜 체크
        today = datetime.now().date()
        streak_days = 0
        if is_streak_active_today:
            streak_days = 1
            check_date = today - timedelta(days=1)
        else:
            check_date = today - timedelta(days=1)
            # 어제 활동 여부 체크
            if check_date in dates:
                streak_days = 1
            check_date = today - timedelta(days=2)
        
        while check_date in dates:
            streak_days += 1
            check_date -= timedelta(days=1)
        
        # 스트릭 시작일 = 연속 활동 마지막 날짜
        if streak_days > 0:
            streak_start_date = today - timedelta(days=streak_days - 1) if is_streak_active_today else today - timedelta(days=streak_days)
    
    # 30일 히스토리 계산
    streak_history = []
    for i in range(29, -1, -1):
        check_day = (datetime.now() - timedelta(days=i)).date()
        completed = check_day in dates
        streak_history.append({
            "date": check_day.isoformat(),
            "completed": completed
        })

    return StreakInfo(
        current_streak=current_streak,
        longest_streak=user.longest_streak or 0,
        streak_start_date=streak_start_date,
        is_streak_active_today=is_streak_active_today,
        last_activity_date=last_log.completed_at if last_log else None,
        streak_history=streak_history
    )
