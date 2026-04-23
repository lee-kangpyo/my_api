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

    ID = Column(INTEGER(11), primary_key=True)
    NAME = Column(String(100), nullable=False)
    EMAIL = Column(String(100), nullable=True)
    LEVEL = Column(INTEGER(11), default=1)
    DAILY_AVAILABLE_TIME = Column(INTEGER(11), nullable=True)
    EXPERIENCE_POINTS = Column(INTEGER(11), default=0)
    CURRENT_STREAK = Column(INTEGER(11), default=0)
    LONGEST_STREAK = Column(INTEGER(11), default=0)
    NOTIFICATION_ENABLED = Column(Boolean, default=True)
    NOTIFICATION_TIME = Column(String(10), nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    UPDATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    goals = relationship('SMALLSTEP_GOALS', back_populates='smallstep_users', cascade='all, delete-orphan')


class SMALLSTEP_GOALS(Base):
    __tablename__ = 'SMALLSTEP_GOALS'
    __table_args__ = {'comment': 'SmallStep 목표 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    USER_ID = Column(ForeignKey('SMALLSTEP_USERS.ID'), nullable=False, index=True)
    GOAL_TEXT = Column(Text, nullable=False)
    GOAL_TYPE = Column(Enum('DEADLINE', 'ONGOING'), default='ONGOING')
    STATUS = Column(Enum('ACTIVE', 'MAINTAIN', 'PAUSED', 'COMPLETED', 'ARCHIVED'), default='ACTIVE')
    DEADLINE_DATE = Column(DateTime, nullable=True)
    CURRENT_LEVEL = Column(INTEGER(11), default=1)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    UPDATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    smallstep_users = relationship('SMALLSTEP_USERS', back_populates='goals')
    phases = relationship('SMALLSTEP_PHASES', back_populates='goals', cascade='all, delete-orphan')
    tasks = relationship('SMALLSTEP_TASKS', back_populates='goals', cascade='all, delete-orphan')


class SMALLSTEP_PHASES(Base):
    __tablename__ = 'SMALLSTEP_PHASES'
    __table_args__ = {'comment': 'SmallStep 단계 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    GOAL_ID = Column(ForeignKey('SMALLSTEP_GOALS.ID'), nullable=False, index=True)
    PHASE_ORDER = Column(INTEGER(11), nullable=False)
    PHASE_TITLE = Column(String(200), nullable=False)
    PHASE_DESCRIPTION = Column(Text, nullable=True)
    ESTIMATED_WEEKS = Column(INTEGER(11), nullable=True)
    STATUS = Column(Enum('PENDING', 'ACTIVE', 'COMPLETED'), default='PENDING')
    STARTED_AT = Column(DateTime, nullable=True)
    COMPLETED_AT = Column(DateTime, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    goals = relationship('SMALLSTEP_GOALS', back_populates='phases')
    weekly_plans = relationship('SMALLSTEP_WEEKLY_PLANS', back_populates='phases', cascade='all, delete-orphan')


class SMALLSTEP_WEEKLY_PLANS(Base):
    __tablename__ = 'SMALLSTEP_WEEKLY_PLANS'
    __table_args__ = {'comment': 'SmallStep 주간 계획 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    GOAL_ID = Column(ForeignKey('SMALLSTEP_GOALS.ID'), nullable=False, index=True)
    PHASE_ID = Column(ForeignKey('SMALLSTEP_PHASES.ID'), nullable=False, index=True)
    WEEK_START_DATE = Column(DateTime, nullable=False)
    WEEK_END_DATE = Column(DateTime, nullable=False)
    AI_CONTEXT = Column(JSON, nullable=True)
    AI_RESPONSE = Column(JSON, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    phases = relationship('SMALLSTEP_PHASES', back_populates='weekly_plans')
    tasks = relationship('SMALLSTEP_TASKS', back_populates='weekly_plans', cascade='all, delete-orphan')


class SMALLSTEP_TASKS(Base):
    __tablename__ = 'SMALLSTEP_TASKS'
    __table_args__ = {'comment': 'SmallStep 작업 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    WEEKLY_PLAN_ID = Column(ForeignKey('SMALLSTEP_WEEKLY_PLANS.ID'), nullable=False, index=True)
    GOAL_ID = Column(ForeignKey('SMALLSTEP_GOALS.ID'), nullable=False, index=True)
    TASK_ORDER = Column(INTEGER(11), nullable=False)
    TASK_TITLE = Column(String(200), nullable=False)
    TASK_DESCRIPTION = Column(Text, nullable=True)
    ESTIMATED_MINUTES = Column(INTEGER(11), nullable=True)
    STATUS = Column(Enum('LOCKED', 'AVAILABLE', 'COMPLETED', 'SKIPPED'), default='LOCKED')
    COMPLETED_AT = Column(DateTime, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    weekly_plans = relationship('SMALLSTEP_WEEKLY_PLANS', back_populates='tasks')
    goals = relationship('SMALLSTEP_GOALS', back_populates='tasks')


class SMALLSTEP_ACTIVITY_LOG(Base):
    __tablename__ = 'SMALLSTEP_ACTIVITY_LOG'
    __table_args__ = {'comment': 'SmallStep 활동 로그 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    USER_ID = Column(ForeignKey('SMALLSTEP_USERS.ID'), nullable=False, index=True)
    TASK_ID = Column(ForeignKey('SMALLSTEP_TASKS.ID'), nullable=True, index=True)
    GOAL_ID = Column(ForeignKey('SMALLSTEP_GOALS.ID'), nullable=True, index=True)
    ACTION = Column(Enum('COMPLETED', 'SKIPPED'), nullable=False)
    XP_EARNED = Column(INTEGER(11), default=0)
    COMPLETED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    SMALLSTEP_USERS = relationship('SMALLSTEP_USERS')