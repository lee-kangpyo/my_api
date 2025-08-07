#import contextlib
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

logging.basicConfig()  # 로깅 레벨 설정
logging.getLogger('sqlalchemy.engine').setLevel(logging.ERROR)

load_dotenv()

# 기존 로또 앱용 데이터베이스 연결
SQLALCHEMY_DATABASE_URL = os.getenv("mysql")
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SmallStep 전용 데이터베이스 연결
SMALLSTEP_DATABASE_URL = os.getenv("smallstep_mysql")
smallstep_engine = create_engine(SMALLSTEP_DATABASE_URL, pool_pre_ping=True)
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