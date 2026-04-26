from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_WEEKLY_PLANS, SMALLSTEP_PHASES
from schemas.smallstep.weekly_plans import WeeklyPlanResponse
from services.ai.weekly_planner import generate_weekly_plan
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 주간 계획 관리"]
)

@router.post("/weekly-plans/generate", response_model=WeeklyPlanResponse, status_code=status.HTTP_201_CREATED,
             summary="주간 계획 생성")
def create_weekly_plan(goal_id: int, phase_id: int, db: Session = Depends(get_smallstep_db)):
    """AI를 호출하여 현재 Phase에 대한 새로운 주간 계획을 생성합니다.
    
    새 주간 계획 생성 전, 이전 주간 계획의 미완료 태스크를 자동으로 SKIPPED 처리합니다.
    """
    try:
        # 이전 주간 계획의 미완료 태스크 처리 (주간 전환)
        from services.weekly_scheduler import WeeklySchedulerService
        scheduler = WeeklySchedulerService(db)
        
        last_plan = (
            db.query(SMALLSTEP_WEEKLY_PLANS)
            .filter(
                SMALLSTEP_WEEKLY_PLANS.goal_id == goal_id,
                SMALLSTEP_WEEKLY_PLANS.phase_id == phase_id
            )
            .order_by(SMALLSTEP_WEEKLY_PLANS.week_start_date.desc())
            .first()
        )
        if last_plan:
            scheduler.process_week_end(last_plan.id)
        
        plan = generate_weekly_plan(goal_id=goal_id, phase_id=phase_id, db=db)
        return plan
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Weekly plan generation failed: {e}")
        raise HTTPException(status_code=500, detail="주간 계획 생성 중 오류가 발생했습니다.")

@router.get("/weekly-plans/current", response_model=WeeklyPlanResponse,
            summary="현재 주간 계획 조회")
def get_current_weekly_plan(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 목표의 현재(가장 최근) 주간 계획을 조회합니다."""
    plan = (
        db.query(SMALLSTEP_WEEKLY_PLANS)
        .filter(SMALLSTEP_WEEKLY_PLANS.goal_id == goal_id)
        .order_by(SMALLSTEP_WEEKLY_PLANS.week_start_date.desc())
        .first()
    )
    if not plan:
        raise HTTPException(status_code=404, detail="현재 주간 계획이 없습니다.")
    return plan

@router.get("/weekly-plans/{plan_id}", response_model=WeeklyPlanResponse,
            summary="특정 주간 계획 상세 조회")
def get_weekly_plan(plan_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 주간 계획을 조회합니다."""
    plan = db.query(SMALLSTEP_WEEKLY_PLANS).filter(SMALLSTEP_WEEKLY_PLANS.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="주간 계획을 찾을 수 없습니다.")
    return plan
