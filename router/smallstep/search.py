#!/usr/bin/env python3
"""
검색 서비스 API 라우터
벡터 검색, 키워드 검색, 하이브리드 검색 엔드포인트 제공
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_smallstep_db
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.search_service import SearchService
from services.embedding_service import EmbeddingService

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/smallstep",
    tags=["SmallStep - 검색 서비스"]
)

# 서비스 인스턴스 생성
search_service = SearchService()
embedding_service = EmbeddingService()

# Pydantic 모델 정의
class SearchRequest(BaseModel):
    """검색 요청 모델"""
    query: str
    limit: int = 10
    search_type: str = "both"  # "vector", "keyword", "both"

class SearchResult(BaseModel):
    """검색 결과 모델"""
    id: str
    plan_data: Dict[str, Any]
    vector_similarity: Optional[float] = None
    keyword_relevance: Optional[float] = None
    combined_score: Optional[float] = None
    sparse_keywords: Optional[str] = None
    created_at: Optional[str] = None

class SearchResponse(BaseModel):
    """검색 응답 모델"""
    query: str
    search_type: str
    total_results: int
    vector_results: List[SearchResult] = []
    keyword_results: List[SearchResult] = []
    processing_time: float

@router.post("/search/vector", 
             response_model=SearchResponse,
             summary="벡터 유사도 검색",
             description="""
벡터 유사도를 기반으로 계획을 검색합니다.

**기능:**
- 텍스트를 벡터로 변환하여 유사도 검색
- 1024차원 Dense 벡터 사용
- 유클리드 거리 기반 유사도 계산

**요청 예시:**
```json
{
  "query": "영어 회화 공부",
  "limit": 5
}
```

**응답 예시:**
```json
{
  "query": "영어 회화 공부",
  "search_type": "vector",
  "total_results": 3,
  "vector_results": [
    {
      "id": "plan-123",
      "plan_data": {"title": "영어 회화 마스터 플랜"},
      "vector_similarity": 0.85,
      "sparse_keywords": "영어, 회화, 공부"
    }
  ],
  "processing_time": 0.15
}
""")
def vector_search(request: SearchRequest, db: Session = Depends(get_smallstep_db)):
    """벡터 유사도 검색"""
    try:
        import time
        start_time = time.time()
        
        # 벡터 검색 실행
        results = search_service.vector_similarity_search(
            query_text=request.query,
            limit=request.limit,
            db=db
        )
        
        # 결과 변환
        vector_results = []
        for result in results:
            vector_results.append(SearchResult(
                id=result['id'],
                plan_data=result.get('plan_data', {}),
                vector_similarity=result.get('vector_similarity'),
                sparse_keywords=result.get('sparse_keywords'),
                created_at=result.get('created_at')
            ))
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            search_type="vector",
            total_results=len(vector_results),
            vector_results=vector_results,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="벡터 검색 중 오류가 발생했습니다."
        )

@router.post("/search/keyword", 
             response_model=SearchResponse,
             summary="키워드 검색",
             description="""
키워드를 기반으로 계획을 검색합니다.

**기능:**
- FULLTEXT 인덱스를 사용한 키워드 검색
- 자연어 처리 기반 관련도 계산
- 빠른 텍스트 검색

**요청 예시:**
```json
{
  "query": "독서 습관",
  "limit": 5
}
```
""")
def keyword_search(request: SearchRequest, db: Session = Depends(get_smallstep_db)):
    """키워드 검색"""
    try:
        import time
        start_time = time.time()
        
        # 키워드 검색 실행
        results = search_service.keyword_search(
            query_text=request.query,
            limit=request.limit,
            db=db
        )
        
        # 결과 변환
        keyword_results = []
        for result in results:
            keyword_results.append(SearchResult(
                id=result['id'],
                plan_data=result.get('plan_data', {}),
                keyword_relevance=result.get('keyword_relevance'),
                sparse_keywords=result.get('sparse_keywords'),
                created_at=result.get('created_at')
            ))
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            search_type="keyword",
            total_results=len(keyword_results),
            keyword_results=keyword_results,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Keyword search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="키워드 검색 중 오류가 발생했습니다."
        )

@router.post("/search/hybrid", 
             response_model=SearchResponse,
             summary="하이브리드 검색",
             description="""
벡터 검색과 키워드 검색을 결합한 하이브리드 검색입니다.

**기능:**
- 벡터 유사도 + 키워드 관련도 조합
- 가중치 기반 점수 계산 (벡터 70%, 키워드 30%)
- 더 정확한 검색 결과 제공

**요청 예시:**
```json
{
  "query": "운동 습관 만들기",
  "limit": 10,
  "search_type": "both"
}
```
""")
def hybrid_search(request: SearchRequest, db: Session = Depends(get_smallstep_db)):
    """하이브리드 검색"""
    try:
        import time
        start_time = time.time()
        
        # 하이브리드 검색 실행
        results = search_service.hybrid_search(
            query_text=request.query,
            limit=request.limit,
            db=db
        )
        
        # 결과 변환
        vector_results = []
        keyword_results = []
        
        for result in results.get('vector_results', []):
            vector_results.append(SearchResult(
                id=result['id'],
                plan_data=result.get('plan_data', {}),
                vector_similarity=result.get('vector_similarity'),
                sparse_keywords=result.get('sparse_keywords'),
                created_at=result.get('created_at')
            ))
        
        for result in results.get('keyword_results', []):
            keyword_results.append(SearchResult(
                id=result['id'],
                plan_data=result.get('plan_data', {}),
                keyword_relevance=result.get('keyword_relevance'),
                sparse_keywords=result.get('sparse_keywords'),
                created_at=result.get('created_at')
            ))
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            query=request.query,
            search_type="hybrid",
            total_results=len(vector_results) + len(keyword_results),
            vector_results=vector_results,
            keyword_results=keyword_results,
            processing_time=processing_time
        )
        
    except Exception as e:
        logger.error(f"Hybrid search failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="하이브리드 검색 중 오류가 발생했습니다."
        )

@router.get("/search/health",
            summary="검색 서비스 헬스체크",
            description="검색 서비스의 상태를 확인합니다.")
def search_health():
    """검색 서비스 헬스체크"""
    try:
        # 서비스 상태 확인
        embedding_status = "healthy" if embedding_service else "unhealthy"
        search_status = "healthy" if search_service else "unhealthy"
        
        return {
            "status": "healthy" if embedding_status == "healthy" and search_status == "healthy" else "unhealthy",
            "service": "SmallStep Search Service",
            "components": {
                "embedding_service": embedding_status,
                "search_service": search_status
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "SmallStep Search Service",
            "error": str(e)
        }
