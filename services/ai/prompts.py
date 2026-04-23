"""
AI 프롬프트 템플릿 모듈 (v2)
Phase 생성 및 주간 계획 생성을 위한 프롬프트 함수
"""
from typing import Optional


def build_phase_generation_messages(
    goal_text: str,
    goal_type: str,
    deadline_date: Optional[str],
    daily_available_time: Optional[int],
    current_level: int = 1,
) -> list[dict]:
    """
    Phase 생성 프롬프트 메시지 조립
    
    Args:
        goal_text: 사용자의 목표 텍스트
        goal_type: 목표 타입 ('DEADLINE' or 'ONGOING')
        deadline_date: 마감일 (ISO 형식 문자열, None 가능)
        daily_available_time: 하루 사용 가능 시간(분)
        current_level: 사용자 현재 레벨
    
    Returns:
        OpenAI 형식의 메시지 리스트
    """
    # 컨텍스트 조립
    deadline_info = f"마감일: {deadline_date}" if deadline_date else "마감일: 없음 (지속적인 목표)"
    time_info = f"하루 {daily_available_time}분 가능" if daily_available_time else "사용 가능 시간 미설정"
    type_info = "기한이 있는 목표" if goal_type == "DEADLINE" else "지속적으로 유지하는 목표"
    
    system_prompt = """당신은 목표 달성 코치입니다. 사용자의 목표를 분석하여 단계별 Phase로 분해해 주세요.

규칙:
- Phase는 2개 이상 5개 이하로 생성합니다
- 각 Phase는 명확하고 달성 가능한 중간 목표를 나타내야 합니다
- 예상 주수는 실제 사용 가능 시간을 고려하여 현실적으로 설정합니다
- Phase는 순차적으로 진행되어야 합니다 (이전 Phase 완료 후 다음 Phase 진행)
- 한국어로 응답해 주세요"""

    user_prompt = f"""다음 목표를 Phase로 분해해 주세요:

목표: {goal_text}
목표 타입: {type_info}
{deadline_info}
사용 가능 시간: {time_info}
사용자 레벨: {current_level}

Phase를 2~5개로 구성하여 단계적 달성 경로를 만들어 주세요."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def build_weekly_plan_messages(
    goal_text: str,
    phase_title: str,
    phase_description: str,
    phase_order: int,
    total_phases: int,
    daily_available_time: Optional[int],
    week_number: int,
    deadline_date: Optional[str] = None,
    previous_week_summary: Optional[str] = None,
    completed_tasks_count: int = 0,
    skipped_tasks_count: int = 0,
) -> list[dict]:
    """
    주간 계획 생성 프롬프트 메시지 조립
    
    Args:
        goal_text: 사용자의 목표 텍스트
        phase_title: 현재 Phase 제목
        phase_description: 현재 Phase 설명
        phase_order: 현재 Phase 순서
        total_phases: 전체 Phase 수
        daily_available_time: 하루 사용 가능 시간(분)
        week_number: 이번이 몇 번째 주인지
        deadline_date: 목표의 마감일 (None 가능)
        previous_week_summary: 지난 주 활동 요약 (None이면 첫 주)
        completed_tasks_count: 지난 주 완료한 태스크 수
        skipped_tasks_count: 지난 주 건너뛴 태스크 수
    
    Returns:
        OpenAI 형식의 메시지 리스트
    """
    time_info = f"하루 {daily_available_time}분" if daily_available_time else "시간 미설정"
    
    # 이전 주 컨텍스트
    if previous_week_summary:
        previous_context = f"""
지난 주 활동:
- 완료한 태스크: {completed_tasks_count}개
- 건너뛴 태스크: {skipped_tasks_count}개
- 요약: {previous_week_summary}"""
    else:
        previous_context = "\n이번이 첫 번째 주간 계획입니다."
    
    system_prompt = """당신은 주간 학습 계획 코치입니다. 사용자의 현재 Phase에 맞는 이번 주 실천 가능한 태스크를 생성해 주세요.

규칙:
- 태스크는 3개 이상 7개 이하로 생성합니다
- 각 태스크는 구체적이고 실천 가능해야 합니다
- 예상 시간은 사용자의 하루 가용 시간을 초과하지 않아야 합니다
- 이전 주 활동 내역이 있으면 적응형으로 난이도/양을 조절합니다
- ai_message는 격려와 이번 주 포인트를 담은 친근한 코멘트를 작성합니다
- 한국어로 응답해 주세요"""

    user_prompt = f"""이번 주 학습 계획을 만들어 주세요:

전체 목표: {goal_text}
현재 Phase: {phase_order}/{total_phases} - {phase_title}
Phase 설명: {phase_description}
하루 가용 시간: {time_info}
진행 주차: {week_number}주차
마감일: {deadline_date if deadline_date else '없음'}
{previous_context}

이번 주에 집중할 3~7개의 구체적인 태스크를 생성해 주세요."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
