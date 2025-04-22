from typing import List
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from src.llm_workflows.state import RagToContextState
from src.config.log_config import Logger
from src.utils.chroma_utils import ChromaUtils
# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = Logger()


def search_documents(state: RagToContextState) -> RagToContextState:
    """
    주어진 쿼리에 대해 관련 문서를 검색합니다.
    """
    query = state.query
    top_k = 5
    
    try:
        logger.debug(f"문서 검색 중: 쿼리='{query}', top_k={top_k}")
        vectorstore: Chroma = ChromaUtils().get_code_documents_vectorstore()
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        results: List[Document] = retriever.invoke(query)
        logger.debug(f"검색 결과: {len(results)}개 문서 찾음")

        state.retrieved_documents = results
        return state
    
    except Exception as e:
        logger.error(f"문서 검색 중 오류 발생: {str(e)}", exc_info=True)
        raise