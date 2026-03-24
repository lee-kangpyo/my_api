from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from database import get_smallstep_db
from models import SS_CACHED_PLANS
from sqlalchemy import text
import json
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstepp",
    tags=["SmallStep - 키워드 관리"]
)

def verify_keyword_api_key(api_key: str = Header(..., alias="X-API-Key")):
    """키워드 API 키 인증"""
    expected_key = os.getenv("KEYWORD_API_KEY")
    if not expected_key or api_key != expected_key:
        raise HTTPException(401, "Invalid API Key")
    return True

@router.get("/plans/{plan_id}/keywords",
           summary="키워드 조회",
           description="특정 계획의 키워드 정보를 조회합니다.")
def get_plan_keywords(plan_id: str, 
                     _: bool = Depends(verify_keyword_api_key),
                     db: Session = Depends(get_smallstep_db)):
    """계획의 키워드 정보 조회"""
    try:
        # 계획 조회
        plan = db.query(SS_CACHED_PLANS).filter(SS_CACHED_PLANS.ID == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="계획을 찾을 수 없습니다.")
        
        # PLAN_DATA에서 goal 추출
        plan_data = json.loads(plan.PLAN_DATA) if plan.PLAN_DATA else {}
        goal_text = plan_data.get("goal", "")
        
        # SPARSE_VECTOR에서 가중치 정보 추출
        sparse_vector = {}
        if plan.PLAN_SPARSE_VECTOR:
            try:
                sparse_vector = json.loads(plan.PLAN_SPARSE_VECTOR)
            except json.JSONDecodeError:
                sparse_vector = {}
        
        return {
            "plan_id": plan_id,
            "goal_text": goal_text,
            "sparse_keywords": plan.sparse_keywords,
            "weights": sparse_vector.get("weights", {}),
            "keyword_status": getattr(plan, 'KEYWORD_STATUS', 'I'),
            "extraction_method": sparse_vector.get("extraction_method", "auto")
        }
        
    except Exception as e:
        logger.error(f"키워드 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="키워드 조회 중 오류가 발생했습니다.")

@router.put("/plans/{plan_id}/keywords",
           summary="키워드 수정",
           description="계획의 키워드를 수정하고 상태를 업데이트합니다.")
def update_plan_keywords(plan_id: str, keywords: str, 
                        _: bool = Depends(verify_keyword_api_key),
                        db: Session = Depends(get_smallstep_db)):
    """키워드 수정"""
    try:
        # 계획 조회
        plan = db.query(SS_CACHED_PLANS).filter(SS_CACHED_PLANS.ID == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="계획을 찾을 수 없습니다.")
        
        # SPARSE_KEYWORDS 업데이트
        plan.SPARSE_KEYWORDS = keywords
        
        # 상태를 U로 변경 (수정됨)
        if hasattr(plan, 'KEYWORD_STATUS'):
            plan.KEYWORD_STATUS = 'U'
        
        db.commit()
        
        return {
            "plan_id": plan_id,
            "sparse_keywords": keywords,
            "keyword_status": "U",
            "message": "키워드가 수정되었습니다. 재계산이 필요합니다."
        }
        
    except Exception as e:
        logger.error(f"키워드 수정 실패: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="키워드 수정 중 오류가 발생했습니다.")

@router.post("/plans/{plan_id}/recalculate-keywords",
            summary="키워드 재계산",
            description="수정된 키워드로 가중치를 재계산하고 PLAN_SPARSE_VECTOR를 업데이트합니다.")
def recalculate_plan_keywords(plan_id: str, 
                             _: bool = Depends(verify_keyword_api_key),
                             db: Session = Depends(get_smallstep_db)):
    """키워드 재계산"""
    try:
        # 계획 조회
        plan = db.query(SS_CACHED_PLANS).filter(SS_CACHED_PLANS.ID == plan_id).first()
        if not plan:
            raise HTTPException(status_code=404, detail="계획을 찾을 수 없습니다.")
        
        # PLAN_DATA에서 goal 추출
        plan_data = json.loads(plan.PLAN_DATA) if plan.PLAN_DATA else {}
        goal_text = plan_data.get("goal", "")
        
        if not goal_text:
            raise HTTPException(status_code=400, detail="목표 텍스트를 찾을 수 없습니다.")
        
        # 가중치 재계산
        weights = calculate_keyword_weights(goal_text, plan.SPARSE_KEYWORDS)
        
        # PLAN_SPARSE_VECTOR 업데이트
        sparse_vector = {
            "keywords": plan.SPARSE_KEYWORDS,
            "weights": weights,
            "extraction_method": "manual_modified"
        }
        
        plan.PLAN_SPARSE_VECTOR = json.dumps(sparse_vector, ensure_ascii=False)
        
        # 상태를 C로 변경 (완료)
        if hasattr(plan, 'KEYWORD_STATUS'):
            plan.KEYWORD_STATUS = 'C'
        
        db.commit()
        
        return {
            "plan_id": plan_id,
            "sparse_keywords": plan.SPARSE_KEYWORDS,
            "weights": weights,
            "keyword_status": "C",
            "message": "키워드 재계산이 완료되었습니다."
        }
        
    except Exception as e:
        logger.error(f"키워드 재계산 실패: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="키워드 재계산 중 오류가 발생했습니다.")

def calculate_keyword_weights(goal_text: str, keywords: str) -> dict:
    """키워드 가중치 계산"""
    if not keywords:
        return {}
    
    # 키워드 리스트로 변환
    keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]
    
    # 각 키워드의 빈도 계산
    weights = {}
    total_count = 0
    
    for keyword in keyword_list:
        count = goal_text.count(keyword)
        weights[keyword] = count
        total_count += count
    
    # 정규화 (빈도 / 전체 빈도)
    if total_count > 0:
        for keyword in weights:
            weights[keyword] = weights[keyword] / total_count
    
    return weights

@router.get("/plans/keywords/status/{status}",
           summary="상태별 계획 조회",
           description="특정 상태의 계획들을 조회합니다.")
def get_plans_by_keyword_status(status: str, 
                               _: bool = Depends(verify_keyword_api_key),
                               db: Session = Depends(get_smallstep_db)):
    """상태별 계획 조회"""
    try:
        # 상태별 계획 조회
        plans = db.query(SS_CACHED_PLANS).filter(
            getattr(SS_CACHED_PLANS, 'KEYWORD_STATUS', None) == status
        ).all()
        
        result = []
        for plan in plans:
            plan_data = json.loads(plan.PLAN_DATA) if plan.PLAN_DATA else {}
            result.append({
                "plan_id": plan.ID,
                "goal_text": plan_data.get("goal", ""),
                "sparse_keywords": plan.SPARSE_KEYWORDS,
                "keyword_status": getattr(plan, 'KEYWORD_STATUS', 'I'),
                "created_at": plan.CREATED_AT
            })
        
        return {
            "status": status,
            "count": len(result),
            "plans": result
        }
        
    except Exception as e:
        logger.error(f"상태별 계획 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="상태별 계획 조회 중 오류가 발생했습니다.")
