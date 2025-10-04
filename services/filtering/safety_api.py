"""
Gemini Safety API를 사용한 1단계 유해성 검사 서비스
"""

import google.generativeai as genai
import os
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class SafetyLevel(Enum):
    """유해성 등급"""
    NEGLIGIBLE = "NEGLIGIBLE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class SafetyCategory(Enum):
    """유해성 카테고리"""
    HARM_CATEGORY_HARASSMENT = "HARM_CATEGORY_HARASSMENT"
    HARM_CATEGORY_HATE_SPEECH = "HARM_CATEGORY_HATE_SPEECH"
    HARM_CATEGORY_SEXUALLY_EXPLICIT = "HARM_CATEGORY_SEXUALLY_EXPLICIT"
    HARM_CATEGORY_DANGEROUS_CONTENT = "HARM_CATEGORY_DANGEROUS_CONTENT"

class SafetyAPIService:
    """Gemini Safety API를 사용한 유해성 검사 서비스"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        logger.info(f"Safety API 초기화 시작 - API 키 존재: {self.api_key is not None}")
        
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY가 설정되지 않음")
            self.model = None
        else:
            try:
                logger.info("Gemini 설정 중...")
                genai.configure(api_key=self.api_key)
                logger.info("GenerativeModel 생성 중...")
                self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
                logger.info("Safety API 모델 초기화 성공")
            except Exception as e:
                logger.error(f"Safety API 모델 초기화 실패: {e}")
                self.model = None
    
    def check_safety(self, text: str) -> Tuple[bool, str, Dict]:
        """
        Gemini Safety API를 사용한 유해성 검사
        
        Args:
            text: 검사할 텍스트
            
        Returns:
            Tuple[bool, str, Dict]: (통과 여부, 메시지, 상세 정보)
        """
        logger.info(f"check_safety 호출됨 - 텍스트: '{text}', 모델 존재: {self.model is not None}")
        
        if not self.model:
            logger.warning("Safety API 모델이 없음 - 검증 건너뜀")
            return True, "Safety API 모델 없음", {}
        
        try:
            # Safety API 호출
            logger.info(f"Safety API 호출 시작: '{text}'")
            response = self.model.generate_content(
                text,
                safety_settings=[
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            )
            logger.info(f"Safety API 응답 받음: {response}")
            
            # 응답 분석
            safety_result = self._analyze_safety_response(response)
            
            if safety_result['max_level'] == SafetyLevel.HIGH:
                logger.warning(f"유해성 HIGH 차단: {text}")
                return False, "처리할 수 없는 내용입니다.", safety_result
            
            elif safety_result['max_level'] == SafetyLevel.MEDIUM:
                logger.info(f"유해성 MEDIUM - 2단계로 전달: {text}")
                return True, "2단계_LLM_분석", safety_result
            
            else:  # LOW or NEGLIGIBLE
                logger.info(f"유해성 LOW/NEGLIGIBLE - 3단계로 전달: {text}")
                return True, "3단계_규칙_검사", safety_result
                
        except Exception as e:
            logger.error(f"Safety API 호출 실패: {e}")
            # API 실패 시 안전하게 통과 처리
            return True, "Safety API 오류 - 통과", {"error": str(e)}
    
    def _analyze_safety_response(self, response) -> Dict:
        """Safety API 응답 분석"""
        try:
            # Gemini 응답에서 safety 정보 추출
            safety_info = {
                'max_level': SafetyLevel.LOW,
                'categories': {},
                'blocked': False,
                'raw_response': str(response)
            }
            
            # 응답이 차단되었는지 확인
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                
                # Safety ratings 확인
                if hasattr(candidate, 'safety_ratings'):
                    max_level = SafetyLevel.LOW
                    
                    for rating in candidate.safety_ratings:
                        category = rating.category
                        probability = rating.probability
                        
                        # 등급 매핑
                        if probability == 'HIGH':
                            level = SafetyLevel.HIGH
                        elif probability == 'MEDIUM':
                            level = SafetyLevel.MEDIUM
                        elif probability == 'LOW':
                            level = SafetyLevel.LOW
                        else:
                            level = SafetyLevel.NEGLIGIBLE
                        
                        safety_info['categories'][category] = {
                            'level': level,
                            'probability': probability
                        }
                        
                        # 최고 등급 업데이트
                        if level == SafetyLevel.HIGH:
                            max_level = SafetyLevel.HIGH
                        elif level == SafetyLevel.MEDIUM and max_level != SafetyLevel.HIGH:
                            max_level = SafetyLevel.MEDIUM
                    
                    safety_info['max_level'] = max_level
                    safety_info['blocked'] = max_level in [SafetyLevel.HIGH, SafetyLevel.MEDIUM]
                    
                    logger.info(f"Safety 분석 결과 - 최고등급: {max_level}, 차단됨: {safety_info['blocked']}")
                    logger.info(f"Safety 카테고리별 등급: {safety_info['categories']}")
            
            return safety_info
            
        except Exception as e:
            logger.error(f"Safety 응답 분석 실패: {e}")
            return {
                'max_level': SafetyLevel.LOW,
                'categories': {},
                'blocked': False,
                'error': str(e)
            }
    
    def get_safety_stats(self) -> Dict:
        """Safety API 통계 반환"""
        return {
            'api_available': self.model is not None,
            'api_key_configured': self.api_key is not None,
            'model_name': 'gemini-2.0-flash-lite' if self.model else None
        }
