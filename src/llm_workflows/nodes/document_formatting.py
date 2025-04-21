from src.llm_workflows.mcp.formatters import format_search_results
from src.llm_workflows.state import RagToContextState


def format_documents(state: RagToContextState) -> RagToContextState:
    """
    검색된 문서를 포맷팅합니다.
    """
    documents = state.retrieved_documents
    formatted_context = format_search_results(documents)
    state.formatted_context = formatted_context
    return state