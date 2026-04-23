"""
게이미피케이션 서비스 (v2)
경험치(XP), 레벨, 연속 달성(Streak) 및 활동 로그 관리를 담당합니다.
"""
import logging
from datetime import datetime, timedelta
import math
from sqlalchemy.orm import Session
from sqlalchemy import func
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
        
        # 스트릭 업데이트 (당일 첫 활동인 경우) 및 스트릭 보너스 계산
        streak_bonus = self._update_streak_and_get_bonus(user)
        xp_earned += streak_bonus
        
        # XP 업데이트 및 레벨 계산
        current_xp = user.EXPERIENCE_POINTS or 0
        new_xp = current_xp + xp_earned
        user.EXPERIENCE_POINTS = new_xp
        user.LEVEL = self._calculate_level(new_xp)
        
        # 로그 기록
        self._log_activity(user_id, task_id, goal_id, 'COMPLETED', xp_earned)
        
        self.db.commit()
        return xp_earned

    def award_weekly_completion_bonus(self, user_id: int, goal_id: int):
        """주간 모든 태스크 완료 보너스"""
        user = self.db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
        if user:
            user.EXPERIENCE_POINTS = (user.EXPERIENCE_POINTS or 0) + XP_REWARD_WEEKLY_ALL_COMPLETED
            user.LEVEL = self._calculate_level(user.EXPERIENCE_POINTS)
            self._log_activity(user_id, None, goal_id, 'WEEKLY_COMPLETED_BONUS', XP_REWARD_WEEKLY_ALL_COMPLETED)
            self.db.commit()

    def award_phase_completion_bonus(self, user_id: int, goal_id: int):
        """Phase 완료 보너스"""
        user = self.db.query(SMALLSTEP_USERS).filter(SMALLSTEP_USERS.ID == user_id).first()
        if user:
            user.EXPERIENCE_POINTS = (user.EXPERIENCE_POINTS or 0) + XP_REWARD_PHASE_COMPLETED
            user.LEVEL = self._calculate_level(user.EXPERIENCE_POINTS)
            self._log_activity(user_id, None, goal_id, 'PHASE_COMPLETED_BONUS', XP_REWARD_PHASE_COMPLETED)
            self.db.commit()

    def _update_streak_and_get_bonus(self, user: SMALLSTEP_USERS) -> int:
        """스트릭을 업데이트하고 보너스 XP를 반환합니다."""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        
        # 오늘 이미 기록이 있는지 확인 (action이 COMPLETED인 것만)
        today_start = datetime.combine(today, datetime.min.time())
        yesterday_start = datetime.combine(yesterday, datetime.min.time())
        
        today_logs = self.db.query(SMALLSTEP_ACTIVITY_LOG).filter(
            SMALLSTEP_ACTIVITY_LOG.USER_ID == user.ID,
            SMALLSTEP_ACTIVITY_LOG.ACTION == 'COMPLETED',
            SMALLSTEP_ACTIVITY_LOG.CREATED_AT >= today_start
        ).count()
        
        if today_logs > 0:
            # 이미 오늘 활동했으므로 스트릭 증가 안 함
            return 0
            
        yesterday_logs = self.db.query(SMALLSTEP_ACTIVITY_LOG).filter(
            SMALLSTEP_ACTIVITY_LOG.USER_ID == user.ID,
            SMALLSTEP_ACTIVITY_LOG.ACTION == 'COMPLETED',
            SMALLSTEP_ACTIVITY_LOG.CREATED_AT >= yesterday_start,
            SMALLSTEP_ACTIVITY_LOG.CREATED_AT < today_start
        ).count()
        
        current_streak = user.CURRENT_STREAK or 0
        longest_streak = user.LONGEST_STREAK or 0
        
        if yesterday_logs > 0:
            new_streak = current_streak + 1
        else:
            new_streak = 1 # 연속이 끊겼으므로 1로 초기화
            
        user.CURRENT_STREAK = new_streak
        if new_streak > longest_streak:
            user.LONGEST_STREAK = new_streak
            
        # 연속 달성 보너스
        if new_streak == 3:
            return XP_REWARD_3_DAYS_STREAK
        elif new_streak == 7:
            return XP_REWARD_7_DAYS_STREAK
            
        return 0

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
