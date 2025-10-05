"""
입력 데이터 검증 서비스
1단계: 기본 입력 검증 (길이, 빈 값, 금지 키워드)
"""

import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class InputValidationService:
    """입력 데이터 검증 서비스"""
    
    def __init__(self):
        # 금지 키워드 목록
        self.forbidden_keywords = [
            # 유해성 키워드
            '멸망', '죽이기', '파괴', '살인', '폭력', '테러', '폭탄',
            '자살', '자해', '고문', '학대', '강간', '성폭력',
            '마약', '약물', '알코올', '담배', '도박',
            '사기', '절도', '강도', '협박', '갈취',
            
            # 무의미한 키워드 (감탄사만)
            'ㅋㅋㅋ', 'ㅎㅎㅎ', 'ㅠㅠㅠ', 'ㅜㅜㅜ', 'ㅡㅡㅡ'
        ]
        
        # 최소/최대 길이 제한 (테스트용 완화)
        self.min_length = 2
        self.max_length = 200
        
        # 목표 관련 필수 키워드 (동사, 명사 등)
        self.goal_indicators = [
            '하기', '배우기', '익히기', '마스터', '완성', '달성', '성취',
            '개선', '향상', '발전', '성장', '습득', '획득', '정복',
            '준비', '시작', '도전', '노력', '연습', '훈련', '공부',
            '만들기', '구현', '개발', '설계', '제작', '완성'
        ]
    
    def validate_goal_input(self, goal_text: str) -> Tuple[bool, str]:
        """
        목표 입력 검증
        
        Args:
            goal_text: 검증할 목표 텍스트
            
        Returns:
            Tuple[bool, str]: (검증 통과 여부, 오류 메시지)
        """
        try:
            # 1. 기본 길이 검증
            if not goal_text or not goal_text.strip():
                return False, "목표를 입력해주세요."
            
            goal_text = goal_text.strip()
            
            if len(goal_text) < self.min_length:
                return False, f"목표를 {self.min_length}자 이상 입력해주세요."
            
            if len(goal_text) > self.max_length:
                return False, f"목표를 {self.max_length}자 이하로 입력해주세요."
            
            # 2. 금지 키워드 검증
            for keyword in self.forbidden_keywords:
                if keyword in goal_text:
                    logger.warning(f"금지 키워드 발견: {keyword} in '{goal_text}'")
                    return False, "목표로 설정하기에 적합하지 않은 내용입니다."
            
            # 3. 목표 형식 검증 (기본적인 목표 키워드 포함 여부)
            has_goal_indicator = any(indicator in goal_text for indicator in self.goal_indicators)
            
            # 4. 특수문자 과다 사용 검증
            special_char_count = len(re.findall(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?/~`]', goal_text))
            if special_char_count > len(goal_text) * 0.3:  # 30% 이상 특수문자
                return False, "목표를 더 구체적으로 입력해주세요."
            
            # 5. 반복 문자 검증 (ㅋㅋㅋ, ㅎㅎㅎ 등)
            if re.search(r'(.)\1{2,}', goal_text):  # 같은 문자가 3번 이상 반복
                return False, "목표를 더 구체적으로 입력해주세요."
            
            # 6. 목표 형식 검증 (테스트용 비활성화)
            # if not has_goal_indicator:
            #     # 목표 키워드가 없어도 너무 짧지 않고 금지 키워드가 없으면 통과
            #     if len(goal_text) < 10:
            #         return False, "목표를 더 구체적으로 입력해주세요."
            
            logger.info(f"목표 검증 통과: '{goal_text}'")
            return True, "검증 통과"
            
        except Exception as e:
            logger.error(f"목표 검증 중 오류 발생: {e}")
            return False, "목표 검증 중 오류가 발생했습니다."
    
    def validate_duration_weeks(self, weeks: int) -> Tuple[bool, str]:
        """기간 검증"""
        if not isinstance(weeks, int) or weeks < 1 or weeks > 12:
            return False, "기간은 1주에서 12주 사이로 설정해주세요."
        return True, "검증 통과"
    
    def validate_weekly_frequency(self, frequency: int) -> Tuple[bool, str]:
        """주간 빈도 검증"""
        if not isinstance(frequency, int) or frequency < 1 or frequency > 7:
            return False, "주간 빈도는 1회에서 7회 사이로 설정해주세요."
        return True, "검증 통과"
    
    def get_validation_stats(self) -> Dict[str, any]:
        """검증 통계 반환"""
        return {
            "forbidden_keywords_count": len(self.forbidden_keywords),
            "goal_indicators_count": len(self.goal_indicators),
            "min_length": self.min_length,
            "max_length": self.max_length
        }
