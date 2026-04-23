from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_TASKS
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
        .filter(SMALLSTEP_TASKS.GOAL_ID == goal_id, SMALLSTEP_TASKS.STATUS == 'AVAILABLE')
        .order_by(SMALLSTEP_TASKS.TASK_ORDER)
        .all()
    )
    return tasks

@router.put("/tasks/{task_id}/complete", response_model=TaskResponse,
            summary="태스크 완료 처리")
def complete_task(task_id: int, db: Session = Depends(get_smallstep_db)):
    """태스크를 완료 처리하고 다음 태스크를 AVAILABLE로 변경합니다. (MVP 수준 상태 머신)"""
    task = db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.ID == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="태스크를 찾을 수 없습니다.")
    
    if task.STATUS != 'AVAILABLE':
        raise HTTPException(status_code=400, detail=f"현재 태스크 상태({task.STATUS})에서는 완료 처리할 수 없습니다.")
    
    # 1. 완료 상태로 변경
    task.STATUS = 'COMPLETED'
    task.COMPLETED_AT = datetime.now()
    
    # 2. 다음 태스크 찾기
    next_task = (
        db.query(SMALLSTEP_TASKS)
        .filter(
            SMALLSTEP_TASKS.WEEKLY_PLAN_ID == task.WEEKLY_PLAN_ID,
            SMALLSTEP_TASKS.TASK_ORDER > task.TASK_ORDER
        )
        .order_by(SMALLSTEP_TASKS.TASK_ORDER)
        .first()
    )
    
    # 3. 다음 태스크 상태 변경
    if next_task and next_task.STATUS == 'LOCKED':
        next_task.STATUS = 'AVAILABLE'
        
    db.commit()
    db.refresh(task)
    return task
