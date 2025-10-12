"""
목표 검증 통합 서비스
3단계 필터링 시스템을 통합 관리
"""

import logging
from typing import Tuple, Dict, Any
from services.filtering import SafetyAPIService, InputValidationService, LLMAnalysisService

logger = logging.getLogger(__name__)

class GoalValidationService:
    """목표 검증 통합 서비스"""
    
    def __init__(self):
        self.safety_service = SafetyAPIService()
        self.validation_service = InputValidationService()
        self.llm_analysis_service = LLMAnalysisService()
        logger.info("GoalValidationService 초기화 완료")
    
    async def validate_goal(self, goal: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        목표 검증 통합 처리 (3단계 필터링)
        
        Args:
            goal: 검증할 목표 텍스트
            
        Returns:
            Tuple[bool, str, Dict]: (통과 여부, 메시지, 상세 정보)
        """
        try:
            logger.info(f"목표 검증 시작: '{goal}'")
            
            # 1단계: Safety API 유해성 검사
            safety_passed, safety_message, safety_info = self.safety_service.check_safety(goal)
            
            logger.info(f"1단계 Safety API - 통과: {safety_passed}, 메시지: {safety_message}")
            
            if not safety_passed:
                logger.warning(f"1단계 Safety API 차단: {goal} - {safety_message}")
                return False, safety_message, {
                    "step": 1,
                    "step_name": "Safety API",
                    "blocked": True,
                    "safety_info": safety_info
                }
            
            # 2단계: 규칙 기반 검사 (빠른 필터링)
            logger.info(f"2단계 규칙 검사 시작: {goal}")
            goal_valid, goal_error = self.validation_service.validate_goal_input(goal)
            
            if not goal_valid:
                logger.warning(f"2단계 규칙 검사 차단: {goal} - {goal_error}")
                return False, goal_error, {
                    "step": 2,
                    "step_name": "규칙 기반 검사",
                    "blocked": True,
                    "validation_error": goal_error
                }
            
            logger.info(f"2단계 규칙 검사 통과: {goal}")
            
            # 3단계: LLM 심층 분석 (정교한 분석)
            logger.info(f"3단계 LLM 분석 시작: {goal}")
            llm_valid, llm_error = await self.llm_analysis_service.analyze_goal_safety(goal)
            
            if not llm_valid:
                logger.warning(f"3단계 LLM 분석 차단: {goal} - {llm_error}")
                return False, llm_error, {
                    "step": 3,
                    "step_name": "LLM 심층 분석",
                    "blocked": True,
                    "llm_error": llm_error
                }
            
            logger.info(f"3단계 LLM 분석 통과: {goal}")
            
            # 모든 단계 통과
            logger.info(f"✅ 목표 검증 완료 - 모든 단계 통과: {goal}")
            return True, "목표 검증 통과", {
                "step": 3,
                "step_name": "모든 단계 통과",
                "blocked": False,
                "safety_info": safety_info,
                "validation_passed": True,
                "llm_analysis_passed": True
            }
            
        except Exception as e:
            logger.error(f"목표 검증 중 오류 발생: {e}")
            return False, f"목표 검증 중 오류가 발생했습니다: {str(e)}", {
                "step": 0,
                "step_name": "오류 발생",
                "blocked": True,
                "error": str(e)
            }
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        검증 서비스 통계 정보 반환
        
        Returns:
            Dict: 검증 서비스 통계
        """
        try:
            return {
                "safety_api": {
                    "available": self.safety_service is not None
                },
                "input_validation": self.validation_service.get_validation_stats(),
                "llm_analysis": {
                    "available": self.llm_analysis_service is not None
                }
            }
        except Exception as e:
            logger.error(f"검증 통계 조회 실패: {e}")
            return {"error": str(e)}
