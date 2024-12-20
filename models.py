
from sqlalchemy import CHAR, Column, DateTime, ForeignKey, String, Table, Text, text, Enum
from sqlalchemy.dialects.mysql import BIGINT, INTEGER
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import warnings
from sqlalchemy.exc import SAWarning

# 특정 경고 클래스를 무시하도록 설정 -- 모델들이 같은 컬럼 이름을 가졌을때 에러가뜸...
warnings.filterwarnings('ignore', category=SAWarning, message="^Implicitly combining column .*")

Base = declarative_base()
metadata = Base.metadata

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