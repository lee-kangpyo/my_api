#import contextlib
import os
from pathlib import Path
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig()  # 로깅 레벨 설정
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

load_dotenv()

# 프로젝트 루트 기준으로 SSL 인증서 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
SSL_CA_PATH = PROJECT_ROOT / "backend" / "ssl" / "ca-cert.pem"

# SSL 설정 준비
def get_ssl_config():
    if SSL_CA_PATH.exists():
        return {
            'ca': str(SSL_CA_PATH),
            'check_hostname': False,  # 호스트명 검증 비활성화
            'verify_mode': False      # 인증서 검증 비활성화
        }
    return None

# 기존 로또 앱용 데이터베이스 연결
SQLALCHEMY_DATABASE_URL = os.getenv("mysql")
ssl_config = get_ssl_config()
if ssl_config:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True, connect_args={"ssl": ssl_config})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# SmallStep 전용 데이터베이스 연결
SMALLSTEP_DATABASE_URL = os.getenv("smallstep_mysql")
if ssl_config:
    smallstep_engine = create_engine(SMALLSTEP_DATABASE_URL, pool_pre_ping=True, connect_args={"ssl": ssl_config})
else:
    smallstep_engine = create_engine(SMALLSTEP_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
smallstep_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=smallstep_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_smallstep_db():
    db = smallstep_SessionLocal()
    try:
        yield db
    finally:
        db.close()