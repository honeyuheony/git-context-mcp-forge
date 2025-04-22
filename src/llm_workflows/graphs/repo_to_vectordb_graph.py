from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from src.llm_workflows.state import RepositoryToVectorDBState
from src.llm_workflows.nodes.code_loader import repo_to_documents
from src.llm_workflows.nodes.code_splitter import split_documents
from src.llm_workflows.nodes.embedder import add_documents
from src.llm_workflows.nodes.hypothetical_question_create import hypothetical_question_create
from src.config.log_config import Logger

logger = Logger()


def create_repo_to_vectordb_graph() -> CompiledStateGraph:
    workflow = StateGraph(RepositoryToVectorDBState)

    workflow.add_node("저장소 로드", repo_to_documents)
    workflow.add_node("문서 분할", split_documents)
    workflow.add_node("문서 추가", add_documents)
    workflow.add_node("가설 질문 생성", hypothetical_question_create)

    workflow.add_edge(START, "저장소 로드")
    workflow.add_edge("저장소 로드", "문서 분할")
    workflow.add_edge("문서 분할", "가설 질문 생성")
    workflow.add_edge("가설 질문 생성", "문서 추가")
    workflow.add_edge("문서 추가", END)

    return workflow.compile()

