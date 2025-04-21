from langgraph.graph.state import CompiledStateGraph
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
    result: RepositoryInfo = workflow.invoke(state, output_keys=["repo_info"])
    logger.info(f"repo_to_rag result: {result}")

    return result


async def rag_to_context(query: str) -> str:
    """
    Embedding Search ⇒ Generate Answer
    질문을 받아 임베딩 기반 유사성 검색을 수행하고, VectorDB에서 가장 관련성 높은 문서를 기반으로 응답을 생성합니다.
    """
    state = RagToContextState(query=query)
    workflow: CompiledStateGraph = create_rag_to_context_graph()
    result: RagToContextState = workflow.invoke(state, output_keys=["retrieved_documents"])
    logger.info(f"rag_to_context result: {result}")

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
    query = "git-context-mcp-forge 저장소에 대해 설명해줘"
    result = await rag_to_context(query)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_repo_to_rag())
    asyncio.run(test_rag_to_context())
