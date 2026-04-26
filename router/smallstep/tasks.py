from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_TASKS, SMALLSTEP_WEEKLY_PLANS
from schemas.smallstep.tasks import TaskResponse
from typing import List
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 태스크 관리"]
)

@router.get("/tasks/today", response_model=List[TaskResponse],
            summary="오늘 할 일 조회 (AVAILABLE 상태)")
def get_today_tasks(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """현재 AVAILABLE 상태인 태스크(오늘 해야 할 일)를 반환합니다."""
    tasks = (
        db.query(SMALLSTEP_TASKS)
        .filter(SMALLSTEP_TASKS.goal_id == goal_id, SMALLSTEP_TASKS.status == 'AVAILABLE')
        .order_by(SMALLSTEP_TASKS.task_order)
        .all()
    )
    return tasks

@router.put("/tasks/{task_id}/complete", response_model=TaskResponse,
            summary="태스크 완료 처리")
def complete_task(task_id: int, db: Session = Depends(get_smallstep_db)):
    """태스크를 완료 처리하고 다음 태스크를 AVAILABLE로 변경합니다. (MVP 수준 상태 머신)"""
    task = db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다.")
    
    if task.status != 'AVAILABLE':
        raise HTTPException(status_code=400, detail=f"현재 태스크 상태({task.status})에서는 완료 처리할 수 없습니다.")
    
    # 1. 완료 상태로 변경
    task.status = 'COMPLETED'
    task.completed_at = datetime.now()
    
    # 2. 다음 태스크 찾기
    next_task = (
        db.query(SMALLSTEP_TASKS)
        .filter(
            SMALLSTEP_TASKS.weekly_plan_id == task.weekly_plan_id,
            SMALLSTEP_TASKS.task_order > task.task_order
        )
        .order_by(SMALLSTEP_TASKS.task_order)
        .first()
    )
    
    # 3. 다음 태스크 상태 변경
    if next_task and next_task.status == 'LOCKED':
        next_task.status = 'AVAILABLE'
        
    # 4. 게이미피케이션 연동 (XP 부여 및 스트릭 업데이트)
    from models import SMALLSTEP_GOALS
    from services.gamification import GamificationService
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.id == task.goal_id).first()
    if goal:
        gamification_service = GamificationService(db)
        gamification_service.award_task_completion_xp(
            user_id=goal.user_id,
            task_id=task.id,
            goal_id=task.goal_id
        )
        
        # 5. 마지막 태스크 완료 체크 (주간 별도 XP + Phase 완료 검사)
        remaining_tasks = (
            db.query(SMALLSTEP_TASKS)
            .filter(
                SMALLSTEP_TASKS.weekly_plan_id == task.weekly_plan_id,
                SMALLSTEP_TASKS.status.in_(['AVAILABLE', 'LOCKED'])
            )
            .count()
        )
        if remaining_tasks == 0:
            # 주간 모든 태스크 완료 별도 XP
            gamification_service.award_weekly_completion_bonus(
                user_id=goal.user_id,
                goal_id=task.goal_id
            )
            # Phase 완료 검사 및 자동 전환
            from services.weekly_scheduler import WeeklySchedulerService
            weekly_plan = db.query(SMALLSTEP_WEEKLY_PLANS).filter(SMALLSTEP_WEEKLY_PLANS.id == task.weekly_plan_id).first()
            if weekly_plan:
                scheduler = WeeklySchedulerService(db)
                scheduler.check_phase_completion(weekly_plan.phase_id)
        
    db.commit()
    db.refresh(task)
    return task
