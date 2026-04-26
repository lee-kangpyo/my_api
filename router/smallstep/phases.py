from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SMALLSTEP_PHASES, SMALLSTEP_GOALS
from schemas.smallstep.phases import PhaseResponse
from typing import List
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - Phase 관리"]
)

@router.get("/goals/{goal_id}/phases", response_model=List[PhaseResponse],
            summary="목표의 Phase 목록 조회")
def get_goal_phases(goal_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 목표의 전체 Phase 목록을 순서대로 조회합니다."""
    # 목표 존재 여부 확인
    goal = db.query(SMALLSTEP_GOALS).filter(SMALLSTEP_GOALS.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="목표를 찾을 수 없습니다.")

    phases = (
        db.query(SMALLSTEP_PHASES)
        .filter(SMALLSTEP_PHASES.goal_id == goal_id)
        .order_by(SMALLSTEP_PHASES.phase_order)
        .all()
    )
    
    from models import SMALLSTEP_WEEKLY_PLANS
    
    result = []
    for phase in phases:
        try:
            weekly_plans = (
                db.query(SMALLSTEP_WEEKLY_PLANS)
                .filter(SMALLSTEP_WEEKLY_PLANS.phase_id == phase.id)
                .order_by(SMALLSTEP_WEEKLY_PLANS.week_start_date)
                .all()
            )
            
            phase_dict = {
                'id': phase.id,
                'goal_id': phase.goal_id,
                'phase_order': phase.phase_order,
                'phase_title': phase.phase_title,
                'phase_description': phase.phase_description,
                'estimated_weeks': phase.estimated_weeks,
                'status': phase.status,
                'started_at': phase.started_at,
                'completed_at': phase.completed_at,
                'created_at': phase.created_at,
                'weekly_plans': [
                    {
                        'id': plan.id,
                        'goal_id': plan.goal_id,
                        'phase_id': plan.phase_id,
                        'week_start_date': plan.week_start_date,
                        'week_end_date': plan.week_end_date,
                        'created_at': plan.created_at
                    }
                    for plan in weekly_plans
                ]
            }
            result.append(PhaseResponse(**phase_dict))
        except Exception as e:
            logger.error(f"Phase {phase.id} 처리 중 오류: {e}")
            raise HTTPException(status_code=500, detail=f"Phase 처리 중 오류: {str(e)}")
    
    return result

@router.get("/phases/{phase_id}", response_model=PhaseResponse,
            summary="Phase 상세 조회")
def get_phase(phase_id: int, db: Session = Depends(get_smallstep_db)):
    """특정 Phase의 상세 정보를 조회합니다. (주간 계획 목록 포함)"""
    from models import SMALLSTEP_WEEKLY_PLANS
    
    phase = db.query(SMALLSTEP_PHASES).filter(SMALLSTEP_PHASES.id == phase_id).first()
    if not phase:
        raise HTTPException(status_code=404, detail="Phase를 찾을 수 없습니다.")
    
    try:
        weekly_plans = (
            db.query(SMALLSTEP_WEEKLY_PLANS)
            .filter(SMALLSTEP_WEEKLY_PLANS.phase_id == phase_id)
            .order_by(SMALLSTEP_WEEKLY_PLANS.week_start_date)
            .all()
        )
        
        phase_dict = {
            'id': phase.id,
            'goal_id': phase.goal_id,
            'phase_order': phase.phase_order,
            'phase_title': phase.phase_title,
            'phase_description': phase.phase_description,
            'estimated_weeks': phase.estimated_weeks,
            'status': phase.status,
            'started_at': phase.started_at,
            'completed_at': phase.completed_at,
            'created_at': phase.created_at,
            'weekly_plans': [
                {
                    'id': plan.id,
                    'goal_id': plan.goal_id,
                    'phase_id': plan.phase_id,
                    'week_start_date': plan.week_start_date,
                    'week_end_date': plan.week_end_date,
                    'created_at': plan.created_at
                }
                for plan in weekly_plans
            ]
        }
        
        return PhaseResponse(**phase_dict)
    except Exception as e:
        logger.error(f"Phase {phase_id} 상세 조회 중 오류: {e}")
        raise HTTPException(status_code=500, detail=f"Phase 상세 조회 중 오류: {str(e)}")
