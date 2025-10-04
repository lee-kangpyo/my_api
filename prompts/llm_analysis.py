"""
LLM 목표 분석 프롬프트
"""

def create_llm_analysis_prompt(goal_text: str) -> str:
    """
    LLM 목표 적합성 분석 프롬프트 생성
    
    Args:
        goal_text: 사용자가 입력한 목표 텍스트
        
    Returns:
        LLM 분석용 프롬프트
    """
    return f"""너는 목표 설정 앱의 관리자야. 다음 문장이 사용자의 건전한 목표 달성을 위한 내용으로 적합한지 판단해 줘.
'T' 또는 'F'로만 대답해.
사용자 입력: {goal_text}"""
