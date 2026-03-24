#!/usr/bin/env python3
"""
하이브리드 검색 서비스
Dense Vector + Sparse Keywords 기반 검색
"""

import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_smallstep_db
from models import SS_CACHED_PLANS
from .embedding_service import EmbeddingService

# 로깅 설정
logger = logging.getLogger(__name__)
smallstep_analytics = logging.getLogger("smallstep.analytics")

class SearchService:
    """하이브리드 검색 서비스 클래스"""
    
    def __init__(self):
        """검색 서비스 초기화"""
        self.embedding_service = EmbeddingService(keyword_method="improved_kiwi")
        logger.info("SearchService 초기화 완료")
    
    def get_db_session(self) -> Session:
        """SmallStep 데이터베이스 세션 가져오기"""
        try:
            db = next(get_smallstep_db())
            return db
        except Exception as e:
            logger.error(f"SmallStep 데이터베이스 세션 생성 실패: {e}")
            raise
    
    def _vector_similarity_search_internal(self, query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        벡터 유사도 검색 (Dense Search)
        
        Args:
            query_vector (List[float]): 검색할 벡터 (1024차원)
            limit (int): 반환할 최대 결과 수
            
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        try:
            db = self.get_db_session()
            
            # 벡터를 배열 형식으로 변환 (MariaDB VECTOR 타입)
            vector_str = f"[{','.join(map(str, query_vector))}]"
            
            # MariaDB VECTOR 검색 쿼리
            # VEC_DISTANCE: 벡터 간 거리 계산 (낮을수록 유사)
            # VEC_FromText: 문자열을 VECTOR 타입으로 변환
            query = text("""
                SELECT 
                    ID,
                    PLAN_DATA,
                    SPARSE_KEYWORDS,
                    VEC_DISTANCE(PLAN_VECTOR, VEC_FromText(:query_vector)) as vector_distance,
                    CREATED_AT
                FROM SS_CACHED_PLANS 
                ORDER BY vector_distance ASC
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                'query_vector': vector_str,
                'limit': limit
            })
            
            results = []
            for row in result:
                results.append({
                    'id': row.ID,
                    'plan_data': json.loads(row.PLAN_DATA) if row.PLAN_DATA else {},
                    'sparse_keywords': row.SPARSE_KEYWORDS,
                    'vector_distance': float(row.vector_distance),
                    'vector_similarity': 1.0 / (1.0 + float(row.vector_distance)),  # 거리를 유사도로 변환
                    'created_at': row.CREATED_AT,
                    'search_type': 'vector'
                })
            
            logger.info(f"벡터 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise
        finally:
            if 'db' in locals():
                db.close()
    
    def keyword_match_search(self, keywords: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        키워드 매칭 검색 (Sparse Search)
        
        Args:
            keywords (str): 검색할 키워드들 (공백으로 구분)
            limit (int): 반환할 최대 결과 수
            
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        try:
            db = self.get_db_session()
            
            # MariaDB FULLTEXT 검색 쿼리
            # MATCH AGAINST: 키워드 매칭 점수 (높을수록 관련성 높음)
            query = text("""
                SELECT 
                    ID,
                    PLAN_DATA,
                    SPARSE_KEYWORDS,
                    MATCH(SPARSE_KEYWORDS) AGAINST(:keywords IN NATURAL LANGUAGE MODE) as keyword_score,
                    CREATED_AT
                FROM SS_CACHED_PLANS
                WHERE MATCH(SPARSE_KEYWORDS) AGAINST(:keywords IN NATURAL LANGUAGE MODE) > 0
                ORDER BY keyword_score DESC
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                'keywords': keywords,
                'limit': limit
            })
            
            results = []
            for row in result:
                results.append({
                    'id': row.ID,
                    'plan_data': json.loads(row.PLAN_DATA) if row.PLAN_DATA else {},
                    'sparse_keywords': row.SPARSE_KEYWORDS,
                    'keyword_score': float(row.keyword_score),
                    'keyword_relevance': float(row.keyword_score),  # API에서 사용하는 키
                    'created_at': row.CREATED_AT,
                    'search_type': 'keyword'
                })
            
            logger.info(f"키워드 검색 완료: {len(results)}개 결과")
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            raise
        finally:
            if 'db' in locals():
                db.close()
    
    def hybrid_search(self, query_text: str, limit: int = 10, db: Session = None) -> Dict[str, Any]:
        """
        하이브리드 검색 (벡터 + 키워드)
        
        Args:
            query_text (str): 검색할 텍스트
            limit (int): 반환할 최대 결과 수
            db (Session): 데이터베이스 세션 (선택적)
            
        Returns:
            Dict: 벡터 검색 결과와 키워드 검색 결과
        """
        try:
            logger.info(f"하이브리드 검색 시작: '{query_text}'")
            
            # 데이터베이스 세션 가져오기
            if db is None:
                db = self.get_db_session()
                should_close_db = True
            else:
                should_close_db = False
            
            # 임베딩 생성
            hybrid_embedding = self.embedding_service.create_hybrid_embedding(query_text)
            
            results = {
                'query': query_text,
                'search_type': 'hybrid',
                'vector_results': [],
                'keyword_results': [],
                'embedding_info': {
                    'vector_dimension': len(hybrid_embedding['dense_vector']),
                    'keywords_extracted': hybrid_embedding['sparse_data']['keywords'],
                    'keyword_count': len(hybrid_embedding['sparse_data']['weights'])
                }
            }
            
            # 벡터 검색
            dense_vector = hybrid_embedding['dense_vector']
            if hasattr(dense_vector, 'tolist'):
                dense_vector = dense_vector.tolist()
            vector_results = self._vector_similarity_search_internal(dense_vector, limit)
            results['vector_results'] = vector_results
            
            # 키워드 검색
            keywords = hybrid_embedding['sparse_data']['keywords'].replace(', ', ' ')
            keyword_results = self.keyword_match_search(keywords, limit)
            results['keyword_results'] = keyword_results
            
            # 결과 요약
            total_vector = len(results['vector_results'])
            total_keyword = len(results['keyword_results'])
            
            logger.info(f"하이브리드 검색 완료 - 벡터: {total_vector}개, 키워드: {total_keyword}개")
            
            return results
            
        except Exception as e:
            logger.error(f"하이브리드 검색 실패: {e}")
            raise
        finally:
            if should_close_db and 'db' in locals():
                db.close()

    def keyword_search(self, query_text: str, limit: int = 10, db: Session = None) -> List[Dict[str, Any]]:
        """
        텍스트에서 키워드를 추출하여 검색
        
        Args:
            query_text (str): 검색할 텍스트
            limit (int): 반환할 최대 결과 수
            db (Session): 데이터베이스 세션 (선택적)
            
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        try:
            # 데이터베이스 세션 가져오기
            if db is None:
                db = self.get_db_session()
                should_close_db = True
            else:
                should_close_db = False
            
            # 임베딩 생성
            hybrid_embedding = self.embedding_service.create_hybrid_embedding(query_text)
            keywords = hybrid_embedding['sparse_data']['keywords'].replace(', ', ' ')
            
            # 키워드 검색 실행
            results = self.keyword_match_search(keywords, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"키워드 검색 실패: {e}")
            raise
        finally:
            if should_close_db and 'db' in locals():
                db.close()

    def vector_similarity_search(self, query_text: str, limit: int = 10, db: Session = None) -> List[Dict[str, Any]]:
        """
        텍스트를 벡터로 변환하여 유사도 검색 (API용)
        
        Args:
            query_text (str): 검색할 텍스트
            limit (int): 반환할 최대 결과 수
            db (Session): 데이터베이스 세션 (선택적)
            
        Returns:
            List[Dict]: 검색 결과 리스트
        """
        try:
            # 데이터베이스 세션 가져오기
            if db is None:
                db = self.get_db_session()
                should_close_db = True
            else:
                should_close_db = False
            
            # 임베딩 생성
            hybrid_embedding = self.embedding_service.create_hybrid_embedding(query_text)
            dense_vector = hybrid_embedding['dense_vector']
            if hasattr(dense_vector, 'tolist'):
                dense_vector = dense_vector.tolist()
            
            # 벡터 검색 실행
            results = self._vector_similarity_search_internal(dense_vector, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"벡터 검색 실패: {e}")
            raise
        finally:
            if should_close_db and 'db' in locals():
                db.close()

    def basic_search(self, query_text: str, search_type: str = "both", limit: int = 5) -> Dict[str, Any]:
        """
        기본 검색 기능 (벡터 또는 키워드 또는 둘 다)
        
        Args:
            query_text (str): 검색할 텍스트
            search_type (str): "vector", "keyword", "both" 중 하나
            limit (int): 반환할 최대 결과 수
            
        Returns:
            Dict: 검색 결과 및 메타데이터
        """
        try:
            logger.info(f"기본 검색 시작: '{query_text}' (타입: {search_type})")
            
            # SmallStep 분석 로그 기록
            smallstep_analytics.info(f"검색시작: {query_text} | 타입: {search_type}")
            
            # 임베딩 생성
            hybrid_embedding = self.embedding_service.create_hybrid_embedding(query_text)
            
            results = {
                'query': query_text,
                'search_type': search_type,
                'vector_results': [],
                'keyword_results': [],
                'embedding_info': {
                    'vector_dimension': len(hybrid_embedding['dense_vector']),
                    'keywords_extracted': hybrid_embedding['sparse_data']['keywords'],
                    'keyword_count': len(hybrid_embedding['sparse_data']['weights'])
                }
            }
            
            # 벡터 검색
            if search_type in ["vector", "both"]:
                dense_vector = hybrid_embedding['dense_vector']
                if hasattr(dense_vector, 'tolist'):
                    dense_vector = dense_vector.tolist()
                vector_results = self.vector_similarity_search(dense_vector, limit)
                results['vector_results'] = vector_results
            
            # 키워드 검색
            if search_type in ["keyword", "both"]:
                keywords = hybrid_embedding['sparse_data']['keywords'].replace(', ', ' ')
                keyword_results = self.keyword_match_search(keywords, limit)
                results['keyword_results'] = keyword_results
            
            # 결과 요약
            total_vector = len(results['vector_results'])
            total_keyword = len(results['keyword_results'])
            
            logger.info(f"검색 완료 - 벡터: {total_vector}개, 키워드: {total_keyword}개")
            
            # SmallStep 분석 로그 기록 (검색 완료)
            smallstep_analytics.info(f"검색완료: {query_text} | 벡터결과: {total_vector}개 | 키워드결과: {total_keyword}개")
            
            return results
            
        except Exception as e:
            logger.error(f"기본 검색 실패: {e}")
            raise
    
    def get_search_stats(self) -> Dict[str, Any]:
        """검색 서비스 통계 정보"""
        try:
            db = self.get_db_session()
            
            # 총 계획 수 조회
            total_plans = db.query(SS_CACHED_PLANS).count()
            
            return {
                'service_name': 'SearchService',
                'total_cached_plans': total_plans,
                'embedding_service': self.embedding_service.get_service_info(),
                'supported_search_types': ['vector', 'keyword', 'both'],
                'database_status': 'connected'
            }
            
        except Exception as e:
            logger.error(f"통계 정보 조회 실패: {e}")
            return {
                'service_name': 'SearchService',
                'database_status': 'error',
                'error': str(e)
            }
        finally:
            if 'db' in locals():
                db.close()
