from typing import List, Any, Union
from langgraph.graph.state import CompiledStateGraph
from langchain_core.documents import Document
from src.models.git_repository import RepositoryInfo
from src.llm_workflows.state import RepositoryToVectorDBState, RagToContextState
from src.llm_workflows.graphs.repo_to_vectordb_graph import create_repo_to_vectordb_graph
from src.llm_workflows.graphs.rag_to_context_graph import create_rag_to_context_graph
from src.config.log_config import Logger


logger = Logger()


async def repo_to_rag(repo_url: str) -> RepositoryInfo:
    """
    GITHUB Repository ⇒ Embedding and Store in VectorDB
    주어진 GitHub 저장소의 소스 코드를 임베딩하여 VectorDB에 저장합니다.
    이 과정은 벡터 기반 코드 검색 및 검색 기반 질문 응답을 가능하게 합니다.

    Parameters:
        repo_url: GitHub 저장소 URL
    """
    state = RepositoryToVectorDBState(
        repo_info=RepositoryInfo(repo_url=repo_url)
    )
    workflow: CompiledStateGraph = create_repo_to_vectordb_graph()
    finish_state: dict[str, Any] = workflow.invoke(state)
    result: RepositoryToVectorDBState = RepositoryToVectorDBState.model_validate(finish_state)
    repo_info: RepositoryInfo = result.repo_info
    logger.debug(f"repo_to_rag result: {repo_info}")

    return result


async def rag_to_context(query: str) -> str:
    """
    Embedding Search ⇒ Generate Answer
    질문을 받아 임베딩 기반 유사성 검색을 수행하고, VectorDB에서 가장 관련성 높은 문서를 기반으로 응답을 생성합니다.
    """
    state = RagToContextState(query=query)
    workflow: CompiledStateGraph = create_rag_to_context_graph()
    finish_state: dict[str, Any] = workflow.invoke(state)
    result: RagToContextState = RagToContextState.model_validate(finish_state)
    retrieved_documents: List[Document] = result.retrieved_documents
    for i, result in enumerate(retrieved_documents):
        logger.debug(f"{i+1}번째 문서: \n내용 :\n{result.page_content[:100]}\n참조 경로:\n{result.metadata.get('path')}")

    return result
    
    
async def test_repo_to_rag():
    """
    Test the repo_to_rag function with a sample GitHub repository URL.
    """
    repo_url = "https://github.com/honeyuheony/git-context-mcp-forge"
    result = await repo_to_rag(repo_url)


async def test_rag_to_context():
    """
    Test the rag_to_context function with a sample query.
    """
    query = "git-context-mcp-forge mcp 도구에서 제공하고 있는 기능을 설명해줘"
    result = await rag_to_context(query)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_repo_to_rag())
    asyncio.run(test_rag_to_context())
