"""
태스크 상태 머신 (v2)
태스크의 상태 전환(LOCKED → AVAILABLE → COMPLETED/SKIPPED)을 관리합니다.
"""
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from models import SMALLSTEP_TASKS

logger = logging.getLogger(__name__)

class TaskStateMachine:
    def __init__(self, db: Session):
        self.db = db

    def complete_task(self, task_id: int) -> SMALLSTEP_TASKS:
        """
        태스크를 완료 처리하고 다음 태스크를 활성화
        LOCKED 상태나 이미 완료된 상태면 에러 발생
        """
        task = self.db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.ID == task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found")
            
        if task.STATUS != 'AVAILABLE':
            raise ValueError(f"Cannot complete task {task_id} with status {task.STATUS}")

        # 1. 상태 변경
        task.STATUS = 'COMPLETED'
        task.COMPLETED_AT = datetime.now()

        # 2. 다음 태스크 활성화
        self._activate_next_task(task)
        
        self.db.commit()
        self.db.refresh(task)
        return task

    def skip_remaining_tasks(self, weekly_plan_id: int) -> int:
        """
        특정 주간 계획 내의 처리되지 않은 태스크들을 스킵 처리
        주간 전환 시 호출됨
        """
        tasks_to_skip = (
            self.db.query(SMALLSTEP_TASKS)
            .filter(
                SMALLSTEP_TASKS.WEEKLY_PLAN_ID == weekly_plan_id,
                SMALLSTEP_TASKS.STATUS.in_(['AVAILABLE', 'LOCKED'])
            )
            .all()
        )
        
        count = 0
        for task in tasks_to_skip:
            task.STATUS = 'SKIPPED'
            count += 1
            
        self.db.commit()
        return count

    def _activate_next_task(self, current_task: SMALLSTEP_TASKS):
        """현재 태스크 다음 순서의 태스크를 찾아 활성화"""
        next_task = (
            self.db.query(SMALLSTEP_TASKS)
            .filter(
                SMALLSTEP_TASKS.WEEKLY_PLAN_ID == current_task.WEEKLY_PLAN_ID,
                SMALLSTEP_TASKS.TASK_ORDER > current_task.TASK_ORDER
            )
            .order_by(SMALLSTEP_TASKS.TASK_ORDER)
            .first()
        )
        
        if next_task and next_task.STATUS == 'LOCKED':
            next_task.STATUS = 'AVAILABLE'
