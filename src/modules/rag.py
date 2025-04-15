from typing import List
import os
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import logging
from dotenv import load_dotenv
import sys
import asyncio

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # ✅ MCP 안전하게 처리
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Semaphore 설정
_clone_semaphore = asyncio.Semaphore()


class DocumentEmbedder:
    """
    문서 임베딩 및 벡터 저장을 처리하는 클래스
    """
    def __init__(
        self,
        persist_directory: str = "chroma_db",
        collection_name: str = "code_documents",
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        문서 임베딩 및 벡터 저장을 처리하는 클래스를 초기화합니다.
        """
        load_dotenv()
        
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        
        self.embeddings = OpenAIEmbeddings(
            model=embedding_model,
            dimensions=1536
        )
        
        self.vectorstore = Chroma(
            persist_directory=persist_directory,
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        
        self.collection_name = collection_name
        self.embedding_model = embedding_model

    def add_documents(self, documents: List[Document]) -> None:
        """문서들을 벡터 저장소에 추가합니다."""
        try:
            self.vectorstore.add_documents(documents)
            logger.info(f"총 {len(documents)}개의 문서가 벡터 저장소에 추가되었습니다.")
        except Exception as e:
            logger.error(f"문서 추가 중 오류 발생: {str(e)}")
            raise
    
    def delete_documents_collection(self, collection_name: str) -> None:
        """문서들을 벡터 저장소에서 삭제합니다."""
        try:
            self.vectorstore.delete_collection(collection_name)
            logger.info(f"{collection_name} 컬렉션이 벡터 저장소에서 삭제되었습니다.")
        except Exception as e:
            logger.error(f"{collection_name} 컬렉션 삭제 중 오류 발생: {str(e)}")
            raise


    def get_vectorstore(self) -> Chroma: 
        """벡터 저장소 인스턴스를 반환합니다."""
        return self.vectorstore

    def get_collection_stats(self) -> dict:
        """현재 컬렉션의 통계 정보를 반환합니다."""
        try:
            collection = self.vectorstore.get()
            return {
                "document_count": len(collection['ids']),
                "collection_name": self.collection_name,
                "embedding_model": self.embedding_model
            }
        except Exception as e:
            logger.error(f"컬렉션 통계 조회 중 오류 발생: {str(e)}")
            raise

def main():
    embedder = DocumentEmbedder(
        persist_directory="chroma_db",
        collection_name="test_collection"
    )
    # 임의 문서
    documents = [
        Document(page_content="Hello, world!")
    ]
    # 문서 추가
    embedder.add_documents(documents)
    
    # 컬렉션 통계 출력
    stats = embedder.get_collection_stats()
    logger.info("\n컬렉션 통계:")
    logger.info("==========")
    for key, value in stats.items():
        logger.info(f"{key}: {value}")

    # 벡터 저장소에서 문서 삭제
    embedder.delete_documents_collection(documents)

if __name__ == "__main__":
    main()