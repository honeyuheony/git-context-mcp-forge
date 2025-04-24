from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.config.log_config import Logger

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
            cls.instance.code_documents_vectorstore = Chroma(
                collection_name="code_documents",
                embedding_function=cls.instance.embeddings,
                persist_directory="chroma_db/code_documents"
            )
            cls.instance.hypothetical_questions_vectorstore = Chroma(
                collection_name="hypothetical_questions",
                embedding_function=cls.instance.embeddings,
                persist_directory="chroma_db/hypothetical_questions"
            )
        return cls.instance
    
    def get_code_documents_vectorstore(self) -> Chroma:
        return self.code_documents_vectorstore
    
    def get_hypothetical_questions_vectorstore(self) -> Chroma:
        return self.hypothetical_questions_vectorstore