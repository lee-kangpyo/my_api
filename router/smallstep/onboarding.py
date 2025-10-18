from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SS_GOAL_TEMPLATES, SS_CACHED_PLANS
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 온보딩"]
)

@router.get("/onboarding/templates",
           summary="온보딩 템플릿 조회",
           description="신규 사용자 온보딩용 템플릿 목록을 카테고리별로 조회합니다.")
def get_onboarding_templates(db: Session = Depends(get_smallstep_db)):
    """온보딩용 템플릿 목록 조회"""
    try:
        # 1. SS_GOAL_TEMPLATES에서 템플릿 메타데이터 조회
        templates = db.query(SS_GOAL_TEMPLATES).order_by(SS_GOAL_TEMPLATES.DISPLAY_ORDER).all()
        
        # 2. SS_GOAL_TEMPLATES와 SS_CACHED_PLANS 조인해서 조회
        # CACHED_PLAN_ID가 있는 템플릿만 조회
        templates_with_plans = db.query(SS_GOAL_TEMPLATES, SS_CACHED_PLANS)\
            .join(SS_CACHED_PLANS, SS_GOAL_TEMPLATES.CACHED_PLAN_ID == SS_CACHED_PLANS.ID)\
            .order_by(SS_GOAL_TEMPLATES.DISPLAY_ORDER)\
            .all()
        
        # 3. 템플릿과 캐시드 플랜 매핑
        plan_mapping = {}
        for template, plan in templates_with_plans:
            plan_mapping[template.ID] = plan
        
        # 4. 카테고리별로 그룹화
        categories = {}
        total_count = 0
        
        for template in templates:
            category = template.CATEGORY
            if category not in categories:
                categories[category] = []
            
            # 해당 템플릿의 캐시드 플랜 찾기
            cached_plan = plan_mapping.get(template.ID)
            
            template_data = {
                "id": str(template.ID),
                "goal_text": template.GOAL_TEXT,
                "category": template.CATEGORY,
                "display_order": template.DISPLAY_ORDER,
                "cached_plan_id": template.CACHED_PLAN_ID,  # CACHED_PLAN_ID 추가
                "preview_data": None
            }
            
            # 캐시드 플랜이 있으면 미리보기 데이터 추가
            if cached_plan:
                plan_data = json.loads(cached_plan.PLAN_DATA) if cached_plan.PLAN_DATA else {}
                template_data["preview_data"] = {
                    "plan_id": cached_plan.ID,
                    "goal": plan_data.get("goal", ""),
                    "status": plan_data.get("status", "skeleton"),
                    "needs_llm_completion": plan_data.get("needs_llm_completion", True),
                    "duration_weeks": getattr(cached_plan, 'DURATION_WEEKS', None),
                    "weekly_frequency": getattr(cached_plan, 'WEEKLY_FREQUENCY', None)
                }
            
            categories[category].append(template_data)
            total_count += 1
        
        return {
            "categories": categories,
            "total_count": total_count,
            "message": "온보딩용 템플릿 목록을 성공적으로 조회했습니다."
        }
        
    except Exception as e:
        logger.error(f"온보딩 템플릿 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="온보딩 템플릿 조회 중 오류가 발생했습니다.")

@router.get("/onboarding/templates/{template_id}/preview",
           summary="템플릿 상세 정보",
           description="특정 템플릿의 완전한 상세 정보를 조회합니다. 사용자가 확정하기 전에 모든 내용을 확인할 수 있습니다.")
def get_template_preview(template_id: str, db: Session = Depends(get_smallstep_db)):
    """템플릿 상세 정보 조회"""
    try:
        # 템플릿과 캐시드 플랜을 조인해서 조회
        result = db.query(SS_GOAL_TEMPLATES, SS_CACHED_PLANS)\
            .join(SS_CACHED_PLANS, SS_GOAL_TEMPLATES.CACHED_PLAN_ID == SS_CACHED_PLANS.ID)\
            .filter(SS_GOAL_TEMPLATES.ID == template_id)\
            .first()
        
        if not result:
            raise HTTPException(status_code=404, detail="템플릿 또는 캐시드 플랜을 찾을 수 없습니다.")
        
        template, cached_plan = result

        print(cached_plan.PLAN_DATA)
        
        # 미리보기 데이터 구성
        plan_data = json.loads(cached_plan.PLAN_DATA) if cached_plan.PLAN_DATA else {}
        
        return {
            "template_id": template_id,
            "goal_text": template.GOAL_TEXT,
            "category": template.CATEGORY,
            "cached_plan_id": template.CACHED_PLAN_ID,
            "detail": {
                "plan_id": cached_plan.ID,
                "goal": plan_data.get("goal", ""),
                "duration_weeks": getattr(cached_plan, 'DURATION_WEEKS', None),
                "weekly_frequency": getattr(cached_plan, 'WEEKLY_FREQUENCY', None),
                "plan_data": plan_data
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"템플릿 상세 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="템플릿 상세 정보 조회 중 오류가 발생했습니다.")
