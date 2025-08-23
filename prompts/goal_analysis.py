"""
목표 분석 프롬프트 모듈
"""

def create_goal_analysis_prompt(goal: str, duration_weeks: int = None, weekly_frequency: int = None) -> str:
    """
    목표 분석 프롬프트 생성
    
    Args:
        goal: 목표
        duration_weeks: 기간 (주)
        weekly_frequency: 주당 횟수
        
    Returns:
        생성된 프롬프트
    """
    
    # None 값 처리
    duration_weeks_str = str(duration_weeks) if duration_weeks is not None else ""
    weekly_frequency_str = str(weekly_frequency) if weekly_frequency is not None else ""
    
    # 기본 프롬프트
    prompt = f"""
# [지시문]
당신은 사용자의 목표를 ①전체적인 '로드맵'과 ②구체적인 '일일 스케줄'로 구성된, 완벽한 '마스터 플랜'을 설계하는 '목표 달성 전략 총괄 아키텍트'입니다. 당신의 임무는 아래 [입력 정보]를 분석하여, 이 두 가지 핵심 요소를 모두 포함하는 단일 JSON 객체를 생성하는 것입니다.

## [수행 규칙]
1.  **마스터 플랜 구조 설계:** 최종 결과물은 `roadmap`과 `schedule`이라는 두 개의 최상위 키를 가진 단일 JSON 객체여야 합니다.
2.  **`roadmap` 설계:**
    * 먼저, 사용자의 '목표'를 달성하기 위한 전체 여정을 3~5개의 논리적인 `phase`(단계)로 구성하여 `roadmap`을 설계합니다.
    * 각 `phase`에는 그 단계의 핵심 목표와 주요 마일스톤을 포함시켜, 사용자가 큰 그림을 이해할 수 있도록 합니다.
3.  **`schedule` 설계:**
    * 앞서 설계한 `roadmap`을 바탕으로, '기간'과 '주당 횟수' 같은 사용자의 제약 조건을 모두 반영하여 상세한 `schedule`을 생성합니다.
    * `schedule`의 각 항목은 `week`, `day` 정보를 포함하며, `roadmap`의 어떤 `phase`에 해당하는지를 명시적으로 연결(`phase_link`)해야 합니다.
    * 모든 조건부 로직(기간, 횟수)은 이 `schedule` 부분에 적용됩니다.
4.  **활동 유형(activity_type)의 지능적 정의:** 목표의 성격(운동/학습 등)에 맞게 `schedule` 내의 활동 유형을 지능적으로 정의합니다.
5.  **JSON 형식 준수:** 최종 결과물은 다른 설명 없이, 아래 [출력 형식]을 엄격히 준수하는 단일 JSON 객체여야 합니다.
6.  **주석 제거:** 주석(//)이나 설명을 JSON 안에 넣지 마세요
7.  **한글 사용:** 한글을 사용하여 출력합니다.


---

## [입력 정보]

### [필수 입력]
* **목표:** {goal}

### [선택 입력]
* **기간 (주):** {duration_weeks_str}
* **주당 횟수:** {weekly_frequency_str}

---

## [출력 형식]
```json
{{
  "roadmap": [
    {{
      "phase": "number (단계 번호)",
      "phase_title": "string (해당 단계의 제목)",
      "phase_description": "string (단계에 대한 설명)",
      "key_milestones": ["string (이 단계의 핵심 달성 과제1)", "string (과제2)"]
    }}
  ],
  "schedule": [
    {{
      "week": 1,
      "day": 1,
      "phase_link": "number (연결된 roadmap의 phase 번호)",
      "activity_type": "string (목표에 맞게 지능적으로 생성된 활동 유형)",
      "title": "string (그날의 핵심 활동 이름)",
      "description": "string (구체적인 활동 내용과 격려 메시지)"
    }}
  ]
}}
"""
    
    return prompt.strip() 