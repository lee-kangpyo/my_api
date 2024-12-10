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
SQLALCHEMY_DATABASE_URL = os.getenv("mysql")

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()