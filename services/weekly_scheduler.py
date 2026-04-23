"""
주간 스케줄러 서비스 (v2)
주간 전환 로직(미완료 태스크 스킵 처리, 새 주간 계획 생성 등)을 관리합니다.
"""
import logging
from sqlalchemy.orm import Session
from models import SMALLSTEP_WEEKLY_PLANS, SMALLSTEP_TASKS
from services.task_state_machine import TaskStateMachine
from services.ai.weekly_planner import generate_weekly_plan

logger = logging.getLogger(__name__)

class WeeklySchedulerService:
    def __init__(self, db: Session):
        self.db = db
        self.state_machine = TaskStateMachine(db)

    def process_week_end(self, weekly_plan_id: int) -> int:
        """
        주 종료 시 호출: 미완료(AVAILABLE/LOCKED) 태스크를 SKIPPED 처리
        """
        skipped_count = self.state_machine.skip_remaining_tasks(weekly_plan_id)
        logger.info(f"Week ended for plan {weekly_plan_id}. Skipped {skipped_count} tasks.")
        return skipped_count

    def start_new_week(self, goal_id: int, phase_id: int) -> SMALLSTEP_WEEKLY_PLANS:
        """
        새로운 주의 시작: AI를 호출하여 새로운 주간 계획 생성
        """
        logger.info(f"Starting new week for goal {goal_id}, phase {phase_id}")
        new_plan = generate_weekly_plan(goal_id=goal_id, phase_id=phase_id, db=self.db)
        return new_plan

    def check_phase_completion(self, phase_id: int) -> bool:
        """
        현재 Phase가 완료 조건(예: 예상 주수 도달 및 주요 태스크 완료)을
        충족했는지 검사 (MVP에서는 수동 전환 또는 단순 체크용)
        """
        # MVP에서는 복잡한 자동 전환 로직 생략
        return False
