# Database Migrations

Alembic를 이용한 데이터베이스 마이그레이션 관리.

## 마이그레이션 실행

### 전체 마이그레이션 적용
```bash
cd backend
alembic upgrade head
```

### 특정 버전으로 마이그레이션
```bash
alembic upgrade <revision_id>
```

## 롤백

### 마지막 마이그레이션 취소
```bash
alembic downgrade -1
```

### 특정 버전으로 롤백
```bash
alembic downgrade <revision_id>
```

### 초기 상태로 롤백
```bash
alembic downgrade base
```

## 현재 버전 확인

### 현재 마이그레이션 상태
```bash
alembic current
```

### 마이그레이션 히스토리
```bash
alembic history
```

### 상세 정보
```bash
alembic show <revision_id>
```

## 새 마이그레이션 생성

### 자동 생성
```bash
alembic revision --message "description"
```

### 자동 생성 (자동 리비전 ID)
```bash
alembic revision --autogenerate -m "description"
```

## 주의사항

- 마이그레이션 실행 전 반드시 DB 백업 수행
- 프로덕션 환경에서는 `alembic upgrade head` 대신 특정 버전 명시 권장
- 롤백 시 데이터 손실 가능성 확인 필수
- `env.py`에서 `from models import Base`를 통해 모델 정의와 동기화 유지

## 구조

```
migrations/
├── versions/           # 마이그레이션 파일 디렉토리
├── env.py             # Alembic 환경 설정
├── script.py.mako     # 마이그레이션 스크립트 템플릿
└── README.md          # 본 문서
```
