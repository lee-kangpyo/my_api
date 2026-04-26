from sqlalchemy import CHAR, Column, DateTime, ForeignKey, String, Text, text, Enum, Integer, Boolean, TIMESTAMP, JSON
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import warnings
from sqlalchemy.exc import SAWarning

warnings.filterwarnings('ignore', category=SAWarning, message="^Implicitly combining column .*")

Base = declarative_base()
metadata = Base.metadata

# ===== 기존 로또 앱 모델들 =====
class LOTTOSUGGESTION(Base):
    __tablename__ = 'LOTTO_SUGGESTION'
    __table_args__ = {'comment': '로또 앱 유저 제안하기 테이블'}

    NO = Column(INTEGER(11), primary_key=True)
    SUGGESTION = Column(String(100), nullable=False)
    ADDITIONAL = Column(String(50), nullable=False)
    CREATEDATE = Column(DateTime, nullable=False, server_default=text("curdate()"))


class LOTTOBUGREPORT(Base):
    __tablename__ = 'LOTTO_BUGREPORT'
    __table_args__ = {'comment': '버그 신고 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    CONTENT = Column(String(100), nullable=False)
    STEP = Column(String(100), nullable=False)
    CREATEDATE = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))


class LOTTOBUGREPORTIMAGE(Base):
    __tablename__ = 'LOTTO_BUGREPORT_IMAGE'
    __table_args__ = {'comment': '버그 리포트 이미지'}

    ID = Column(INTEGER(11), primary_key=True)
    BUGREPORTID = Column(ForeignKey('LOTTO_BUGREPORT.ID'), nullable=False, index=True)
    IMAGEINDEX = Column(INTEGER(11), nullable=False)
    FILENAME = Column(String(255), nullable=False)

    LOTTO_BUGREPORT = relationship('LOTTOBUGREPORT')


# ===== SmallStep 앱 모델들 (v2 스키마) =====
class SMALLSTEP_USERS(Base):
    __tablename__ = 'SMALLSTEP_USERS'
    __table_args__ = {'comment': 'SmallStep 사용자 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    level = Column(INTEGER(11), default=1)
    daily_available_time = Column(INTEGER(11), nullable=True)
    experience_points = Column(INTEGER(11), default=0)
    current_streak = Column(INTEGER(11), default=0)
    longest_streak = Column(INTEGER(11), default=0)
    notification_enabled = Column(Boolean, default=True)
    notification_time = Column(String(10), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    goals = relationship('SMALLSTEP_GOALS', back_populates='smallstep_users', cascade='all, delete-orphan')


class SMALLSTEP_GOALS(Base):
    __tablename__ = 'SMALLSTEP_GOALS'
    __table_args__ = {'comment': 'SmallStep 목표 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(ForeignKey('SMALLSTEP_USERS.id'), nullable=False, index=True)
    title = Column(String(200), nullable=False, default='')
    description = Column(Text, nullable=True)
    goal_text = Column(Text, nullable=False)
    goal_type = Column(Enum('DEADLINE', 'ONGOING'), default='ONGOING')
    status = Column(Enum('active', 'completed', 'paused'), default='active')
    deadline_date = Column(DateTime, nullable=True)
    current_level = Column(INTEGER(11), default=1)
    created_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    updated_at = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    smallstep_users = relationship('SMALLSTEP_USERS', back_populates='goals')
    phases = relationship('SMALLSTEP_PHASES', back_populates='goals', cascade='all, delete-orphan')
    tasks = relationship('SMALLSTEP_TASKS', back_populates='goals', cascade='all, delete-orphan')


class SMALLSTEP_PHASES(Base):
    __tablename__ = 'SMALLSTEP_PHASES'
    __table_args__ = {'comment': 'SmallStep 단계 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    goal_id = Column(ForeignKey('SMALLSTEP_GOALS.id'), nullable=False, index=True)
    phase_order = Column(INTEGER(11), nullable=False)
    phase_title = Column(String(200), nullable=False)
    phase_description = Column(Text, nullable=True)
    estimated_weeks = Column(INTEGER(11), nullable=True)
    status = Column(Enum('PENDING', 'ACTIVE', 'COMPLETED'), default='PENDING')
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    goals = relationship('SMALLSTEP_GOALS', back_populates='phases')
    weekly_plans = relationship('SMALLSTEP_WEEKLY_PLANS', back_populates='phases', cascade='all, delete-orphan')


class SMALLSTEP_WEEKLY_PLANS(Base):
    __tablename__ = 'SMALLSTEP_WEEKLY_PLANS'
    __table_args__ = {'comment': 'SmallStep 주간 계획 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    goal_id = Column(ForeignKey('SMALLSTEP_GOALS.id'), nullable=False, index=True)
    phase_id = Column(ForeignKey('SMALLSTEP_PHASES.id'), nullable=False, index=True)
    week_start_date = Column(DateTime, nullable=False)
    week_end_date = Column(DateTime, nullable=False)
    ai_context = Column(JSON, nullable=True)
    ai_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    phases = relationship('SMALLSTEP_PHASES', back_populates='weekly_plans')
    tasks = relationship('SMALLSTEP_TASKS', back_populates='weekly_plans', cascade='all, delete-orphan')


class SMALLSTEP_TASKS(Base):
    __tablename__ = 'SMALLSTEP_TASKS'
    __table_args__ = {'comment': 'SmallStep 작업 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    weekly_plan_id = Column(ForeignKey('SMALLSTEP_WEEKLY_PLANS.id'), nullable=False, index=True)
    goal_id = Column(ForeignKey('SMALLSTEP_GOALS.id'), nullable=False, index=True)
    task_order = Column(INTEGER(11), nullable=False)
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=True)
    estimated_minutes = Column(INTEGER(11), nullable=True)
    status = Column(Enum('LOCKED', 'AVAILABLE', 'COMPLETED', 'SKIPPED'), default='LOCKED')
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    weekly_plans = relationship('SMALLSTEP_WEEKLY_PLANS', back_populates='tasks')
    goals = relationship('SMALLSTEP_GOALS', back_populates='tasks')


class SMALLSTEP_ACTIVITY_LOG(Base):
    __tablename__ = 'SMALLSTEP_ACTIVITY_LOG'
    __table_args__ = {'comment': 'SmallStep 활동 로그 테이블'}

    id = Column(INTEGER(11), primary_key=True)
    user_id = Column(ForeignKey('SMALLSTEP_USERS.id'), nullable=False, index=True)
    task_id = Column(ForeignKey('SMALLSTEP_TASKS.id'), nullable=True, index=True)
    goal_id = Column(ForeignKey('SMALLSTEP_GOALS.id'), nullable=True, index=True)
    action = Column(Enum('COMPLETED', 'SKIPPED'), nullable=False)
    xp_earned = Column(INTEGER(11), default=0)
    completed_at = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    SMALLSTEP_USERS = relationship('SMALLSTEP_USERS')