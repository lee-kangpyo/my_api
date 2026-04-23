"""
주간 계획 생성 파이프라인 (v2)
Phase + 컨텍스트 기반 적응형 주간 계획 생성 및 DB 저장
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from models import (
    SMALLSTEP_GOALS,
    SMALLSTEP_PHASES,
    SMALLSTEP_WEEKLY_PLANS,
    SMALLSTEP_TASKS,
    SMALLSTEP_ACTIVITY_LOG,
)
from services.ai.client import call_ai
from services.ai.schemas import WeeklyPlanGenerationResponse
from services.ai.prompts import build_weekly_plan_messages

logger = logging.getLogger(__name__)


def generate_weekly_plan(
    goal_id: int,
    phase_id: int,
    db: Session,
) -> SMALLSTEP_WEEKLY_PLANS:
    """
    주간 계획을 AI로 생성하고 DB에 저장
    
    Args:
        goal_id: 목표 ID
        phase_id: 현재 Phase ID
        db: 데이터베이스 세션
    
    Returns:
        생성된 SMALLSTEP_WEEKLY_PLANS 레코드
    
    Raises:
        ValueError: 목표나 Phase를 찾을 수 없는 경우
        Exception: AI 호출 실패 시
    """
    # 목표 및 Phase 조회
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.ID == goal_id).first()
    if not goal:
        raise ValueError(f"목표를 찾을 수 없습니다: goal_id={goal_id}")
    
    phase = db.query(SMALLSTEP_PHASES).filter(SMALLSTEP_PHASES.ID == phase_id).first()
    if not phase:
        raise ValueError(f"Phase를 찾을 수 없습니다: phase_id={phase_id}")
    
    # 연관 사용자 정보
    user = goal.smallstep_users
    daily_available_time = user.DAILY_AVAILABLE_TIME if user else None
    user_id = user.ID if user else None
    
    # 이번 주 날짜 범위 계산 (월~일)
    today = datetime.now()
    days_since_monday = today.weekday()
    week_start = (today - timedelta(days=days_since_monday)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_end = (week_start + timedelta(days=6)).replace(
        hour=23, minute=59, second=59
    )
    
    # 현재 Phase의 이전 주간 계획 조회 (컨텍스트용)
    existing_plans = (
        db.query(SMALLSTEP_WEEKLY_PLANS)
        .filter(SMALLSTEP_WEEKLY_PLANS.PHASE_ID == phase_id)
        .order_by(SMALLSTEP_WEEKLY_PLANS.WEEK_START_DATE)
        .all()
    )
    week_number = len(existing_plans) + 1
    
    # 지난 주 컨텍스트 수집
    previous_week_summary = None
    completed_count = 0
    skipped_count = 0
    
    if existing_plans:
        last_plan = existing_plans[-1]
        last_tasks = (
            db.query(SMALLSTEP_TASKS)
            .filter(SMALLSTEP_TASKS.WEEKLY_PLAN_ID == last_plan.ID)
            .all()
        )
        completed_count = sum(1 for t in last_tasks if t.STATUS == 'COMPLETED')
        skipped_count = sum(1 for t in last_tasks if t.STATUS == 'SKIPPED')
        total = len(last_tasks)
        
        if total > 0:
            completion_rate = int((completed_count / total) * 100)
            previous_week_summary = f"총 {total}개 중 {completed_count}개 완료 ({completion_rate}%)"
    
    # 전체 Phase 수 조회
    total_phases = (
        db.query(SMALLSTEP_PHASES)
        .filter(SMALLSTEP_PHASES.GOAL_ID == goal_id)
        .count()
    )
    
    logger.info(f"주간 계획 생성 시작 - goal_id={goal_id}, phase_id={phase_id}, {week_number}주차")
    
    # 프롬프트 조립
    messages = build_weekly_plan_messages(
        goal_text=goal.GOAL_TEXT,
        phase_title=phase.PHASE_TITLE,
        phase_description=phase.PHASE_DESCRIPTION or "",
        phase_order=phase.PHASE_ORDER,
        total_phases=total_phases,
        daily_available_time=daily_available_time,
        week_number=week_number,
        previous_week_summary=previous_week_summary,
        completed_tasks_count=completed_count,
        skipped_tasks_count=skipped_count,
    )
    
    # AI 호출
    ai_response: WeeklyPlanGenerationResponse = call_ai(
        messages=messages,
        response_model=WeeklyPlanGenerationResponse,
    )
    
    logger.info(f"주간 계획 AI 응답 완료 - {len(ai_response.tasks)}개 태스크 생성됨")
    
    # AI 컨텍스트 및 응답 저장용 딕셔너리
    ai_context = {
        "week_number": week_number,
        "previous_completed": completed_count,
        "previous_skipped": skipped_count,
        "previous_summary": previous_week_summary,
    }
    ai_response_data = {
        "ai_message": ai_response.ai_message,
        "tasks_count": len(ai_response.tasks),
    }
    
    # 주간 계획 DB 저장
    db_weekly_plan = SMALLSTEP_WEEKLY_PLANS(
        GOAL_ID=goal_id,
        PHASE_ID=phase_id,
        WEEK_START_DATE=week_start,
        WEEK_END_DATE=week_end,
        AI_CONTEXT=ai_context,
        AI_RESPONSE=ai_response_data,
    )
    db.add(db_weekly_plan)
    db.flush()  # ID 확보
    
    # 태스크 DB 저장
    for i, task_item in enumerate(ai_response.tasks):
        db_task = SMALLSTEP_TASKS(
            WEEKLY_PLAN_ID=db_weekly_plan.ID,
            GOAL_ID=goal_id,
            TASK_ORDER=task_item.task_order,
            TASK_TITLE=task_item.task_title,
            TASK_DESCRIPTION=task_item.task_description,
            ESTIMATED_MINUTES=task_item.estimated_minutes,
            STATUS='LOCKED',
        )
        db.add(db_task)
    
    db.flush()
    
    # 첫 번째 태스크를 AVAILABLE로 설정
    first_task = (
        db.query(SMALLSTEP_TASKS)
        .filter(SMALLSTEP_TASKS.WEEKLY_PLAN_ID == db_weekly_plan.ID)
        .order_by(SMALLSTEP_TASKS.TASK_ORDER)
        .first()
    )
    if first_task:
        first_task.STATUS = 'AVAILABLE'
    
    db.commit()
    db.refresh(db_weekly_plan)
    
    logger.info(f"주간 계획 DB 저장 완료 - weekly_plan_id={db_weekly_plan.ID}")
    return db_weekly_plan
