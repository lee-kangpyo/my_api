"""
피드백 생성 프롬프트 모듈
"""

def create_feedback_prompt(completed_activities: list, current_progress: float) -> str:
    """
    피드백 생성 프롬프트 생성
    
    Args:
        completed_activities: 완료한 활동 목록
        current_progress: 현재 진행률
        
    Returns:
        생성된 프롬프트
    """
    
    # None 값 처리
    completed_activities_str = ', '.join(completed_activities) if completed_activities else ""
    current_progress_str = f"{current_progress}%" if current_progress is not None else ""
    
    prompt = f"""
사용자의 진행 상황을 분석하고 격려 메시지를 생성해주세요:

완료한 활동: {completed_activities_str}
현재 진행률: {current_progress_str}

다음 JSON 형식으로 응답해주세요:

```json
{{
  "feedback_message": "격려와 함께 진행 상황을 평가한 메시지",
  "next_steps": ["다음 활동 1", "다음 활동 2", "다음 활동 3"],
  "motivation_quote": "힘을 주는 명언",
  "progress_analysis": "현재 상황 분석 및 조언"
}}
```
"""
    
    return prompt.strip() 