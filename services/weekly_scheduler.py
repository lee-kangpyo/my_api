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
        현재 Phase가 완료 조건(모든 주간 계획의 태스크 완료)을
        충족했는지 검사하고, 충족 시 다음 Phase를 활성화합니다.
        """
        from models import SMALLSTEP_PHASES
        
        phase = self.db.query(SMALLSTEP_PHASES).filter(SMALLSTEP_PHASES.ID == phase_id).first()
        if not phase or phase.STATUS == 'COMPLETED':
            return False
            
        plans = self.db.query(SMALLSTEP_WEEKLY_PLANS).filter(SMALLSTEP_WEEKLY_PLANS.PHASE_ID == phase_id).all()
        if not plans:
            return False
            
        # 모든 주간 계획의 태스크 상태 검사
        all_completed = True
        for plan in plans:
            tasks = self.db.query(SMALLSTEP_TASKS).filter(SMALLSTEP_TASKS.WEEKLY_PLAN_ID == plan.ID).all()
            if not tasks:
                all_completed = False
                break
            for task in tasks:
                if task.STATUS not in ['COMPLETED', 'SKIPPED']:
                    all_completed = False
                    break
            if not all_completed:
                break
                
        if all_completed:
            # 현재 Phase 완료 처리
            phase.STATUS = 'COMPLETED'
            phase.COMPLETED_AT = __import__('datetime').datetime.now()
            
            # 게이미피케이션 보너스 부여
            from services.gamification import GamificationService
            GamificationService(self.db).award_phase_completion_bonus(user_id=phase.goal.USER_ID, goal_id=phase.GOAL_ID)
            
            # 다음 Phase 활성화
            next_phase = (
                self.db.query(SMALLSTEP_PHASES)
                .filter(SMALLSTEP_PHASES.GOAL_ID == phase.GOAL_ID, SMALLSTEP_PHASES.PHASE_ORDER > phase.PHASE_ORDER)
                .order_by(SMALLSTEP_PHASES.PHASE_ORDER)
                .first()
            )
            if next_phase:
                next_phase.STATUS = 'ACTIVE'
                
            self.db.commit()
            logger.info(f"Phase {phase_id} completed. Next phase activated if exists.")
            return True
            
        return False
