from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.llm_workflows.state import RepositoryToVectorDBState
from src.config.log_config import Logger
from src.utils.chroma_utils import ChromaUtils

logger = Logger()

def add_documents(state: RepositoryToVectorDBState) -> RepositoryToVectorDBState:
    """문서들을 벡터 저장소에 추가합니다."""
    try:
        if state.split_documents:
            code_documents_vectorstore = ChromaUtils().get_code_documents_vectorstore()
            code_documents_vectorstore.add_documents(state.split_documents)

            hypothetical_questions_vectorstore = ChromaUtils().get_hypothetical_questions_vectorstore()
            hypothetical_questions_vectorstore.add_documents(state.hypothetical_questions)

            logger.info(f"벡터 DB에 문서 추가 완료: {len(state.split_documents)}개")
            

        return state

    except Exception as e:
        logger.error(f"문서 추가 중 오류 발생: {e}")
        raise