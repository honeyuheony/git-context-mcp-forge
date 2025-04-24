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
        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={"k": top_k, "score_threshold": 0.5}
        )
        code_results: List[Document] = retriever.invoke(query)
        logger.debug(f"코드 검색 결과: {len(code_results)}개 문서 찾음")
        if len(code_results) == 0:
            logger.debug(f"코드 검색 결과가 없습니다. 가설 질문 검색 시도")
            vectorstore: Chroma = ChromaUtils().get_hypothetical_questions_vectorstore()
            retriever = vectorstore.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": top_k, "score_threshold": 0.5}
            )
            hypothetical_results: List[Document] = retriever.invoke(query)
            logger.debug(f"가설 질문 검색 결과: {len(hypothetical_results)}개 문서 찾음")

            if len(hypothetical_results) > 0:
                search_path_list = []
                for result in hypothetical_results:
                    search_path_list.append(result.metadata["path"])

                vectorstore: Chroma = ChromaUtils().get_code_documents_vectorstore()
                retriever = vectorstore.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={"k": top_k, "score_threshold": 0.5, "filter": {"path": {"in": search_path_list}}}
                )
                code_results: List[Document] = retriever.invoke(query)
                logger.debug(f"코드 검색 재수행 결과: {len(code_results)}개 문서 찾음")

        state.retrieved_documents = code_results + hypothetical_results
        return state
    
    except Exception as e:
        logger.error(f"문서 검색 중 오류 발생: {str(e)}")
        raise