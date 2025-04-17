from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from src.llm_workflows.state import RepositoryToVectorDBState
from src.config.log_config import Logger

logger = Logger()

def add_documents(state: RepositoryToVectorDBState) -> RepositoryToVectorDBState:
    """문서들을 벡터 저장소에 추가합니다."""
    try:
        if state.split_documents:
            # 문서 임베딩
            embedding = OpenAIEmbeddings(
                model="text-embedding-3-small",
                dimensions=1536,
            )
            chroma = Chroma(
                collection_name="code_documents",
                embedding_function=embedding,
                persist_directory="chroma_db"
            )
            chroma.add_documents(state.split_documents)
            logger.info(f"문서 추가 완료: {len(state.split_documents)}개")

        return state

    except Exception as e:
        logger.error(f"문서 추가 중 오류 발생: {e}")
        raise