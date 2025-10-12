"""
캐시된 계획 관리 서비스
SS_CACHED_PLANS 테이블 관련 비즈니스 로직
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from models import SS_CACHED_PLANS
from services.search.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class CachedPlanService:
    """캐시된 계획 관리 서비스"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        logger.info("CachedPlanService 초기화 완료")
    
    def save_cached_plan(self, 
                        goal: str, 
                        duration_weeks: Optional[int], 
                        weekly_frequency: Optional[int],
                        roadmap: list, 
                        schedule: list, 
                        db: Session) -> Optional[str]:
        """
        AI 생성 계획을 SS_CACHED_PLANS에 저장
        
        Args:
            goal: 목표 텍스트
            duration_weeks: 계획된 주수
            weekly_frequency: 주간 빈도
            roadmap: 로드맵 데이터
            schedule: 스케줄 데이터
            db: 데이터베이스 세션
            
        Returns:
            str: 저장된 계획의 UUID (실패 시 None)
        """
        try:
            logger.info(f"캐시된 계획 저장 시작: {goal}")
            
            # 1. 벡터 임베딩 생성
            hybrid_embedding = self.embedding_service.create_hybrid_embedding(goal)
            logger.info(f"하이브리드 임베딩 생성 완료: {len(hybrid_embedding['dense_vector'])}차원")
            
            # 2. UUID 생성
            plan_id = str(uuid.uuid4())
            logger.info(f"계획 ID 생성: {plan_id}")
            
            # 3. PLAN_DATA JSON 구성 (DB 컬럼 제외)
            plan_data = {
                "goal": goal,
                "roadmap": roadmap,
                "schedule": schedule
            }
            
            # 4. SS_CACHED_PLANS에 저장 (DB 컬럼 포함)
            cached_plan = SS_CACHED_PLANS(
                ID=plan_id,
                PLAN_VECTOR=hybrid_embedding["dense_vector"],
                PLAN_SPARSE_VECTOR=json.dumps(hybrid_embedding["sparse_data"], ensure_ascii=False),
                PLAN_DATA=json.dumps(plan_data, ensure_ascii=False),
                SPARSE_KEYWORDS=hybrid_embedding["sparse_data"].get("keywords", ""),
                DURATION_WEEKS=duration_weeks,  # DB 컬럼에 저장
                WEEKLY_FREQUENCY=weekly_frequency,  # DB 컬럼에 저장
            )
            
            db.add(cached_plan)
            db.commit()
            
            logger.info(f"✅ 캐시된 계획 저장 완료: {plan_id}")
            return plan_id
            
        except Exception as e:
            logger.error(f"❌ 캐시된 계획 저장 실패: {e}")
            db.rollback()
            return None
    
    def get_cached_plan(self, plan_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """
        저장된 계획 조회
        
        Args:
            plan_id: 계획 UUID
            db: 데이터베이스 세션
            
        Returns:
            Dict: 계획 데이터 (없으면 None)
        """
        try:
            cached_plan = db.query(SS_CACHED_PLANS).filter(SS_CACHED_PLANS.ID == plan_id).first()
            
            if not cached_plan:
                logger.warning(f"계획을 찾을 수 없음: {plan_id}")
                return None
            
            # JSON 데이터 파싱
            plan_data = json.loads(cached_plan.PLAN_DATA)
            
            return {
                "id": cached_plan.ID,
                "plan_data": plan_data,
                "created_at": cached_plan.CREATED_AT,
                "vector_dimension": len(cached_plan.PLAN_VECTOR) if cached_plan.PLAN_VECTOR else 0
            }
            
        except Exception as e:
            logger.error(f"계획 조회 실패: {e}")
            return None
    
    def get_all_cached_plans(self, db: Session, limit: int = 100) -> list:
        """
        모든 캐시된 계획 조회
        
        Args:
            db: 데이터베이스 세션
            limit: 조회 제한 수
            
        Returns:
            list: 계획 목록
        """
        try:
            cached_plans = db.query(SS_CACHED_PLANS).limit(limit).all()
            
            result = []
            for plan in cached_plans:
                plan_data = json.loads(plan.PLAN_DATA)
                result.append({
                    "id": plan.ID,
                    "goal": plan_data.get("goal", ""),
                    "created_at": plan.CREATED_AT,
                    "vector_dimension": len(plan.PLAN_VECTOR) if plan.PLAN_VECTOR else 0
                })
            
            logger.info(f"캐시된 계획 {len(result)}개 조회 완료")
            return result
            
        except Exception as e:
            logger.error(f"계획 목록 조회 실패: {e}")
            return []
    
    def delete_cached_plan(self, plan_id: str, db: Session) -> bool:
        """
        캐시된 계획 삭제
        
        Args:
            plan_id: 계획 UUID
            db: 데이터베이스 세션
            
        Returns:
            bool: 삭제 성공 여부
        """
        try:
            cached_plan = db.query(SS_CACHED_PLANS).filter(SS_CACHED_PLANS.ID == plan_id).first()
            
            if not cached_plan:
                logger.warning(f"삭제할 계획을 찾을 수 없음: {plan_id}")
                return False
            
            db.delete(cached_plan)
            db.commit()
            
            logger.info(f"✅ 캐시된 계획 삭제 완료: {plan_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 캐시된 계획 삭제 실패: {e}")
            db.rollback()
            return False
