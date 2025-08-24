#!/usr/bin/env python3
"""
임베딩 서비스
GGUF Dense 벡터 + Kiwi Sparse 키워드 추출
"""

import json
import logging
from typing import List, Dict, Any, Tuple
import numpy as np
from .model_manager import model_manager
from .keyword_extractor import KeywordExtractorFactory

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingService:
    """임베딩 서비스 클래스"""
    
    def __init__(self, keyword_method: str = "basic_kiwi"):
        """
        임베딩 서비스 초기화
        
        Args:
            keyword_method (str): 키워드 추출 방식 ("basic_kiwi", "improved_kiwi")
        """
        self.vector_dimension = 1024
        self.keyword_extractor = KeywordExtractorFactory.create_extractor(keyword_method)
        logger.info(f"EmbeddingService 초기화 완료 (키워드 추출: {keyword_method})")
    
    def generate_dense_embedding(self, text: str) -> np.ndarray:
        """
        Dense 벡터 생성 (GGUF 모델 사용)
        
        Args:
            text (str): 임베딩할 텍스트
            
        Returns:
            np.ndarray: 1024차원 Dense 벡터
        """
        try:
            # GGUF 모델 가져오기
            gguf_model = model_manager.get_gguf_model()
            
            # 임베딩 생성
            embedding = gguf_model.embed(text)
            embedding_array = np.array(embedding)
            
            logger.debug(f"Dense 임베딩 생성 완료: {text[:50]}... -> {embedding_array.shape}")
            return embedding_array
            
        except Exception as e:
            logger.error(f"Dense 임베딩 생성 실패: {e}")
            raise
    
    def extract_sparse_keywords(self, text: str) -> Dict[str, Any]:
        """
        Sparse 키워드 추출 (모듈화된 키워드 추출기 사용)
        
        Args:
            text (str): 키워드를 추출할 텍스트
            
        Returns:
            Dict[str, Any]: 키워드 정보 (keywords, weights, metadata)
        """
        try:
            # 모듈화된 키워드 추출기 사용
            result = self.keyword_extractor.extract_keywords(text)
            
            logger.debug(f"Sparse 키워드 추출 완료: {text[:50]}... -> {len(result['weights'])}개 키워드")
            return result
            
        except Exception as e:
            logger.error(f"Sparse 키워드 추출 실패: {e}")
            raise
    
    def create_hybrid_embedding(self, text: str) -> Dict[str, Any]:
        """
        하이브리드 임베딩 생성 (Dense + Sparse)
        
        Args:
            text (str): 임베딩할 텍스트
            
        Returns:
            Dict[str, Any]: Dense 벡터 + Sparse 키워드 정보
        """
        try:
            logger.info(f"하이브리드 임베딩 생성 시작: {text[:100]}...")
            
            # Dense 벡터 생성
            dense_vector = self.generate_dense_embedding(text)
            
            # Sparse 키워드 추출
            sparse_data = self.extract_sparse_keywords(text)
            
            # 결과 조합
            result = {
                "text": text,
                "dense_vector": dense_vector.tolist(),  # JSON 직렬화를 위해 리스트로 변환
                "sparse_data": sparse_data,
                "vector_dimension": len(dense_vector),
                "created_method": "gguf_kiwi"
            }
            
            logger.info(f"✅ 하이브리드 임베딩 생성 완료: {len(dense_vector)}차원 + {len(sparse_data['weights'])}개 키워드")
            return result
            
        except Exception as e:
            logger.error(f"하이브리드 임베딩 생성 실패: {e}")
            raise
    
    def create_batch_embeddings(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        배치 임베딩 생성
        
        Args:
            texts (List[str]): 임베딩할 텍스트 리스트
            
        Returns:
            List[Dict[str, Any]]: 하이브리드 임베딩 리스트
        """
        try:
            logger.info(f"배치 임베딩 생성 시작: {len(texts)}개 텍스트")
            
            results = []
            for i, text in enumerate(texts):
                logger.info(f"진행률: {i+1}/{len(texts)} - {text[:50]}...")
                embedding = self.create_hybrid_embedding(text)
                results.append(embedding)
            
            logger.info(f"✅ 배치 임베딩 생성 완료: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"배치 임베딩 생성 실패: {e}")
            raise
    
    def format_for_database(self, embedding_data: Dict[str, Any]) -> Tuple[List[float], str, str]:
        """
        데이터베이스 저장용 형식으로 변환
        
        Args:
            embedding_data (Dict[str, Any]): 하이브리드 임베딩 데이터
            
        Returns:
            Tuple[List[float], str, str]: (dense_vector, sparse_json, keywords_str)
        """
        try:
            # Dense 벡터 (VECTOR(1024) 컬럼용)
            dense_vector = embedding_data["dense_vector"]
            
            # Sparse JSON (PLAN_SPARSE_VECTOR 컬럼용)
            sparse_json = json.dumps(embedding_data["sparse_data"], ensure_ascii=False)
            
            # 키워드 문자열 (SPARSE_KEYWORDS 컬럼용)
            keywords_str = embedding_data["sparse_data"]["keywords"]
            
            return dense_vector, sparse_json, keywords_str
            
        except Exception as e:
            logger.error(f"데이터베이스 형식 변환 실패: {e}")
            raise
    
    def get_service_info(self) -> Dict[str, Any]:
        """서비스 정보 반환"""
        model_info = model_manager.get_model_info()
        return {
            "service_name": "EmbeddingService",
            "vector_dimension": self.vector_dimension,
            "models": model_info,
            "supported_methods": ["dense_embedding", "sparse_keywords", "hybrid_embedding"]
        }
