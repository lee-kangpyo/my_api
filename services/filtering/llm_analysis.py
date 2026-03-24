"""
LLM 목표 분석 서비스
"""

import google.generativeai as genai
import os
import logging
from typing import Tuple
from prompts.llm_analysis import create_llm_analysis_prompt

logger = logging.getLogger(__name__)

class LLMAnalysisService:
    """LLM 목표 분석 서비스"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        logger.info(f"LLM Analysis 서비스 초기화 시작 - API 키 존재: {self.api_key is not None}")

        if not self.api_key:
            logger.warning("GOOGLE_API_KEY가 설정되지 않음")
            self.model = None
        else:
            try:
                logger.info("Gemini 설정 중...")
                genai.configure(api_key=self.api_key)
                logger.info("GenerativeModel 생성 중...")
                self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                logger.info("LLM Analysis 모델 초기화 성공")
            except Exception as e:
                logger.error(f"LLM Analysis 모델 초기화 실패: {e}")
                self.model = None

    async def analyze_goal_safety(self, goal_text: str) -> Tuple[bool, str]:
        """
        목표 적합성 분석
        
        Args:
            goal_text: 분석할 목표 텍스트
            
        Returns:
            (is_valid, message): (유효성, 메시지)
        """
        try:
            if not self.model:
                return True, "LLM 모델 없음 - 통과"
            
            # 프롬프트 생성
            prompt = create_llm_analysis_prompt(goal_text)
            
            # LLM 호출
            response = self.model.generate_content(prompt)
            result = response.text.strip().lower()
            
            print(f"LLM 심층 분석 프롬프트: {prompt}")
            print(f"LLM 심층 분석 응답: {result}")
            
            # 결과 판단 (T/F로 간단하게)
            if "T" in result.upper():
                return True, "LLM 분석 통과"
            elif "F" in result.upper():
                return False, "목표로 설정하기에 적합하지 않은 내용입니다."
            else:
                return True, "LLM 응답 불명확 - 통과"
                
        except Exception as e:
            print(f"LLM 심층 분석 오류: {e}")
            return True, f"LLM 분석 오류 - 통과: {str(e)}"
    
    def get_service_stats(self) -> dict:
        """서비스 상태 정보 반환"""
        return {
            'api_available': self.model is not None,
            'api_key_set': self.api_key is not None
        }
