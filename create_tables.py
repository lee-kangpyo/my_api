#!/usr/bin/env python3
"""
SmallStep 데이터베이스 테이블 생성 스크립트
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from models import Base

def create_smallstep_tables():
    """SmallStep 데이터베이스 테이블 생성"""
    load_dotenv()
    
    # SmallStep 데이터베이스 연결
    smallstep_database_url = os.getenv("smallstep_mysql")
    if not smallstep_database_url:
        print("❌ smallstep_mysql 환경변수가 설정되지 않았습니다.")
        print("📝 .env 파일에 다음을 추가하세요:")
        print("smallstep_mysql=mysql+pymysql://username:password@localhost:3306/smallstep")
        return False
    
    try:
        # 엔진 생성
        engine = create_engine(smallstep_database_url, pool_pre_ping=True)
        
        # 테이블 생성
        print("🔧 SmallStep 테이블 생성 중...")
        Base.metadata.create_all(bind=engine)
        
        print("✅ SmallStep 테이블이 성공적으로 생성되었습니다!")
        print("📋 생성된 테이블:")
        print("   - SMALLSTEP_USERS")
        print("   - SMALLSTEP_GOALS") 
        print("   - SMALLSTEP_ACTIVITIES")
        print("   - SMALLSTEP_GAME_DATA")
        
        return True
        
    except Exception as e:
        print(f"❌ 테이블 생성 중 오류 발생: {str(e)}")
        print("🔍 다음을 확인하세요:")
        print("   1. MySQL 서버가 실행 중인지")
        print("   2. 데이터베이스 연결 정보가 올바른지")
        print("   3. 사용자 권한이 충분한지")
        return False

if __name__ == "__main__":
    print("🚀 SmallStep 데이터베이스 설정 시작")
    print("=" * 50)
    
    success = create_smallstep_tables()
    
    if success:
        print("=" * 50)
        print("🎉 설정이 완료되었습니다!")
        print("이제 서버를 실행할 수 있습니다: uvicorn main:app --reload")
    else:
        print("=" * 50)
        print("❌ 설정에 실패했습니다.")
        print("위의 오류 메시지를 확인하고 다시 시도하세요.") 