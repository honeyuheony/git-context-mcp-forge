from langgraph.graph import END, StateGraph, START
from langgraph.graph.state import CompiledStateGraph
from src.llm_workflows.state import RagToContextState
from src.llm_workflows.nodes.retriever import search_documents
from src.config.log_config import Logger

logger = Logger()

def create_rag_to_context_graph() -> CompiledStateGraph:
    workflow = StateGraph(RagToContextState)
    
    workflow.add_node("검색", search_documents)
    
    workflow.add_edge(START, "검색")
    workflow.add_edge("검색", END)
    
    return workflow.compile()
