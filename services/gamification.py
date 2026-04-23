"""
게이미피케이션 서비스 (v2)
경험치(XP), 레벨, 연속 달성(Streak) 및 활동 로그 관리를 담당합니다.
"""
import logging
from datetime import datetime, timedelta
import math
from sqlalchemy.orm import Session
from models import SMALLSTEP_USERS, SMALLSTEP_ACTIVITY_LOG

logger = logging.getLogger(__name__)

# XP 부여 상수
XP_REWARD_TASK_COMPLETED = 10
XP_REWARD_WEEKLY_ALL_COMPLETED = 50
XP_REWARD_3_DAYS_STREAK = 20
XP_REWARD_7_DAYS_STREAK = 50
XP_REWARD_PHASE_COMPLETED = 100

class GamificationService:
    def __init__(self, db: Session):
        self.db = db

    def _calculate_level(self, xp: int) -> int:
        """XP에 따른 레벨 계산 로직"""
        if xp < 100:
            return 1
        return int(math.sqrt(xp / 100)) + 1

    def award_task_completion_xp(self, user_id: int, task_id: int, goal_id: int) -> int:
        """태스크 완료 시 XP 부여 및 로그 기록"""
        user = self.db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
        if not user:
            return 0
            
        xp_earned = XP_REWARD_TASK_COMPLETED
        
        # XP 업데이트 및 레벨 계산
        current_xp = user.EXPERIENCE_POINTS or 0
        new_xp = current_xp + xp_earned
        user.EXPERIENCE_POINTS = new_xp
        user.LEVEL = self._calculate_level(new_xp)
        
        # 스트릭 업데이트 (당일 첫 활동인 경우)
        self._update_streak(user)
        
        # 로그 기록
        self._log_activity(user_id, task_id, goal_id, 'COMPLETED', xp_earned)
        
        self.db.commit()
        return xp_earned

    def _update_streak(self, user: SMALLSTEP_USERS):
        """스트릭 업데이트 로직 (간소화된 MVP 버전)"""
        # 실제 환경에서는 ACTIVITY_LOG를 보고 오늘 이미 완료했는지 판단
        # 지금은 호출될 때마다 연속일이라고 가정하거나 1 증가 (정교한 로직은 추후 보완)
        current_streak = user.CURRENT_STREAK or 0
        longest_streak = user.LONGEST_STREAK or 0
        
        new_streak = current_streak + 1
        user.CURRENT_STREAK = new_streak
        
        if new_streak > longest_streak:
            user.LONGEST_STREAK = new_streak

    def _log_activity(self, user_id: int, task_id: int, goal_id: int, action: str, xp_earned: int):
        """활동 로그 기록"""
        log = SMALLSTEP_ACTIVITY_LOG(
            USER_ID=user_id,
            TASK_ID=task_id,
            GOAL_ID=goal_id,
            ACTION=action,
            XP_EARNED=xp_earned
        )
        self.db.add(log)
