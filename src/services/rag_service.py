"""
RAG 서비스 모듈: RAG(Retrieval-Augmented Generation) 관련 서비스를 제공합니다.

이 모듈은 문서 임베딩, 저장소 접근 및 유사성 검색을 위한 기능을 제공합니다.
"""

from typing import List, Optional, Dict, Any
import logging
import os
from functools import lru_cache
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_chroma import Chroma
from src.modules.rag import DocumentEmbedder
# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 상수
DEFAULT_TOP_K = int(os.getenv("RAG_DEFAULT_TOP_K", "5"))
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "code_documents")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

# 싱글톤 인스턴스
_document_embedder = None
_vectorstore = None
_config = {
    "top_k": DEFAULT_TOP_K,
    "persist_directory": PERSIST_DIRECTORY,
    "collection_name": COLLECTION_NAME,
    "embedding_model": EMBEDDING_MODEL
}


@lru_cache(maxsize=1)
def get_document_embedder() -> DocumentEmbedder:
    """
    DocumentEmbedder의 싱글톤 인스턴스를 반환합니다.
    
    캐싱된 인스턴스를 반환하여 임베딩 모델 및 벡터 저장소의 중복 초기화를 방지합니다.

    Returns:
        DocumentEmbedder 인스턴스
    """
    global _document_embedder, _config
    
    if _document_embedder is None:
        logger.info(f"DocumentEmbedder 초기화 중... (컬렉션: {_config['collection_name']})")
        _document_embedder = DocumentEmbedder(
            persist_directory=_config["persist_directory"],
            collection_name=_config["collection_name"],
            embedding_model=_config["embedding_model"]
        )
        
        # 컬렉션 통계 로깅
        try:
            stats = _document_embedder.get_collection_stats()
            logger.info(f"벡터 저장소 로드 완료: {stats['document_count']} 문서")
        except Exception as e:
            logger.warning(f"컬렉션 통계 조회 실패: {str(e)}")
    
    return _document_embedder


@lru_cache(maxsize=1)
def get_vectorstore() -> Chroma:
    """
    벡터 저장소 인스턴스를 반환합니다.
    
    캐싱된 인스턴스를 반환하여 벡터 저장소의 중복 초기화를 방지합니다.

    Returns:
        Chroma 벡터 저장소 인스턴스
    """
    global _vectorstore
    
    if _vectorstore is None:
        logger.debug("벡터 저장소 인스턴스 초기화")
        embedder = get_document_embedder()
        _vectorstore = embedder.get_vectorstore()
    
    return _vectorstore

def search_documents(query: str, top_k: Optional[int] = None) -> List[Document]:
    """
    주어진 쿼리에 대해 관련 문서를 검색합니다.

    Args:
        query: 검색 쿼리
        top_k: 반환할 최대 문서 수 (기본값: 전역 설정값)

    Returns:
        검색된 문서 목록
        
    Raises:
        Exception: 검색 중 오류 발생 시
    """
    if not query.strip():
        logger.warning("빈 쿼리로 검색이 요청되었습니다.")
        return []
    
    if top_k is None:
        top_k = _config["top_k"]
    
    try:
        logger.debug(f"문서 검색 중: 쿼리='{query}', top_k={top_k}")
        vectorstore = get_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        results = retriever.get_relevant_documents(query)
        logger.debug(f"검색 결과: {len(results)}개 문서 찾음")
        return results
    except Exception as e:
        logger.error(f"문서 검색 중 오류 발생: {str(e)}", exc_info=True)
        raise


def set_top_k(value: int) -> None:
    """
    검색 결과 수를 설정합니다.

    Args:
        value: 반환할 최대 문서 수
    """
    global _config
    if value <= 0:
        logger.warning(f"유효하지 않은 top_k 값: {value}, 기본값 사용")
        value = DEFAULT_TOP_K
    
    logger.info(f"top_k 값 변경: {_config['top_k']} → {value}")
    _config["top_k"] = value


def clear_cache() -> None:
    """
    싱글톤 인스턴스 캐시를 초기화합니다.
    주로 테스트 목적으로 사용됩니다.
    """
    global _document_embedder, _vectorstore
    _document_embedder = None
    _vectorstore = None
    
    # lru_cache 초기화
    get_document_embedder.cache_clear()
    get_vectorstore.cache_clear()
    
    logger.info("RAG 서비스 캐시가 초기화되었습니다.")


def get_config() -> Dict[str, Any]:
    """
    현재 RAG 서비스 구성을 반환합니다.
    
    Returns:
        현재 구성 사전
    """
    global _config
    return _config.copy() 