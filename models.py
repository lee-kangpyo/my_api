
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, String, Text, text, Enum, Integer, Boolean, TIMESTAMP
from sqlalchemy.dialects.mysql import BIGINT, INTEGER, LONGTEXT
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import warnings
from sqlalchemy.exc import SAWarning

# 특정 경고 클래스를 무시하도록 설정 -- 모델들이 같은 컬럼 이름을 가졌을때 에러가뜸...
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

# ===== SmallStep 앱 모델들 =====
class SMALLSTEP_USERS(Base):
    __tablename__ = 'SMALLSTEP_USERS'
    __table_args__ = {'comment': 'SmallStep 사용자 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    NAME = Column(String(100), nullable=False)
    EMAIL = Column(String(100), nullable=True)
    LEVEL = Column(INTEGER(11), default=1)
    CONSECUTIVE_DAYS = Column(INTEGER(11), default=0)
    TOTAL_STEPS = Column(INTEGER(11), default=0)
    COMPLETED_STEPS = Column(INTEGER(11), default=0)
    CURRENT_GOAL = Column(String(100), nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    UPDATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))


class SMALLSTEP_GOALS(Base):
    __tablename__ = 'SMALLSTEP_GOALS'
    __table_args__ = {'comment': 'SmallStep 목표 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    USER_ID = Column(ForeignKey('SMALLSTEP_USERS.ID'), nullable=False, index=True)
    TITLE = Column(String(200), nullable=False)
    DESCRIPTION = Column(Text, nullable=True)
    CATEGORY = Column(String(50), nullable=True)
    STATUS = Column(Enum('active', 'completed', 'paused'), default='active')
    PROGRESS = Column(INTEGER(11), default=0)
    TARGET_DATE = Column(DateTime, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    UPDATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    SMALLSTEP_USERS = relationship('SMALLSTEP_USERS')


class SMALLSTEP_ACTIVITIES(Base):
    __tablename__ = 'SMALLSTEP_ACTIVITIES'
    __table_args__ = {'comment': 'SmallStep 활동 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    GOAL_ID = Column(ForeignKey('SMALLSTEP_GOALS.ID'), nullable=False, index=True)
    WEEK = Column(INTEGER(11), nullable=False)
    DAY = Column(INTEGER(11), nullable=False)
    PHASE_LINK = Column(INTEGER(11), nullable=False)
    TITLE = Column(String(200), nullable=False)
    DESCRIPTION = Column(Text, nullable=True)
    ACTIVITY_TYPE = Column(String(50), nullable=True)
    IS_COMPLETED = Column(Boolean, default=False)
    COMPLETED_AT = Column(DateTime, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))

    SMALLSTEP_GOALS = relationship('SMALLSTEP_GOALS')


class SMALLSTEP_GAME_DATA(Base):
    __tablename__ = 'SMALLSTEP_GAME_DATA'
    __table_args__ = {'comment': 'SmallStep 게임 데이터 테이블'}

    ID = Column(INTEGER(11), primary_key=True)
    USER_ID = Column(ForeignKey('SMALLSTEP_USERS.ID'), nullable=False, index=True)
    LEVEL = Column(INTEGER(11), default=1)
    EXPERIENCE = Column(INTEGER(11), default=0)
    CURRENT_STREAK = Column(INTEGER(11), default=0)
    LONGEST_STREAK = Column(INTEGER(11), default=0)
    LAST_COMPLETED_DATE = Column(DateTime, nullable=True)
    CREATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp()"))
    UPDATED_AT = Column(DateTime, nullable=False, server_default=text("current_timestamp() ON UPDATE current_timestamp()"))

    SMALLSTEP_USERS = relationship('SMALLSTEP_USERS')


# ===== SmallStep AI 마스터 플래너 모델들 =====
class SS_CACHED_PLANS(Base):
    __tablename__ = 'SS_CACHED_PLANS'
    __table_args__ = {'comment': 'AI 마스터 플래너 캐시된 계획 테이블'}

    ID = Column(String(36), primary_key=True)
    PLAN_VECTOR = Column('PLAN_VECTOR', nullable=False)  # VECTOR(1024) - SQLAlchemy에서 직접 지원하지 않음
    PLAN_SPARSE_VECTOR = Column(LONGTEXT, nullable=True)  # JSON 데이터
    PLAN_DATA = Column(LONGTEXT, nullable=False)  # JSON 데이터
    SPARSE_KEYWORDS = Column(Text, nullable=True)
    DURATION_WEEKS = Column(INTEGER(11), nullable=True)
    WEEKLY_FREQUENCY = Column(INTEGER(11), nullable=True)
    KEYWORD_STATUS = Column(String(1), nullable=True, default='I')
    CREATED_AT = Column(TIMESTAMP, nullable=True, server_default=text("current_timestamp()"))


class SS_GOAL_TEMPLATES(Base):
    __tablename__ = 'SS_GOAL_TEMPLATES'
    __table_args__ = {'comment': 'AI 마스터 플래너 목표 템플릿 테이블'}

    ID = Column(INTEGER(11), primary_key=True, autoincrement=True)
    CATEGORY = Column(String(100), nullable=False)
    GOAL_TEXT = Column(String(255), nullable=False)
    DISPLAY_ORDER = Column(INTEGER(11), nullable=True)
    CACHED_PLAN_ID = Column(String(36), nullable=True)


class SS_USER_PLANS(Base):
    __tablename__ = 'SS_USER_PLANS'
    __table_args__ = {'comment': 'AI 마스터 플래너 사용자 계획 테이블'}

    ID = Column(String(36), primary_key=True)
    USER_ID = Column(String(36), nullable=False)
    PLAN_DATA = Column(LONGTEXT, nullable=False)  # JSON 데이터
    BACKED_UP_AT = Column(TIMESTAMP, nullable=True, server_default=text("current_timestamp()"))