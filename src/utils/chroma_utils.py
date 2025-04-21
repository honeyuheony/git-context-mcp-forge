from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config.log_config import Logger
from functools import lru_cache
from typing import List, Optional
from langchain.schema import Document

logger = Logger()

class ChromaUtils:
    """
    벡터 저장소 관리 유틸리티 클래스
    """
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(ChromaUtils, cls).__new__(cls)
            cls.instance.embeddings = OpenAIEmbeddings(
                model="text-embedding-3-small",
                dimensions=1536
            )
            cls.instance.vectorstore = Chroma(
                collection_name="code_documents",
                embedding_function=cls.instance.embeddings,
                persist_directory="chroma_db"
            )
        return cls.instance
    
    def get_vectorstore(self) -> Chroma:
        return self.vectorstore

    def add_documents(self, documents: List[Document]) -> None:
        self.vectorstore.add_documents(documents)
    
    def search_documents(self, query: str, top_k: Optional[int] = None) -> List[Document]:
        return self.vectorstore.similarity_search(query, k=top_k)
