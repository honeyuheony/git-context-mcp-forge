from typing import Dict, List, Annotated
from langchain_core.documents import Document
from src.models.git_repository import RepositoryInfo
from pydantic import BaseModel, Field
from langgraph.graph import add_messages


class RepositoryToVectorDBState(BaseModel):
    repo_info: Annotated[RepositoryInfo, Field(..., description="저장소 정보")]
    documents_by_language: Annotated[Dict[str, List[Document]], Field(default_factory=dict, description="언어별 문서")]
    split_documents: Annotated[List[Document], add_messages, Field(default_factory=list, description="분할된 문서")]

    
class RagToContextState(BaseModel):
    query: Annotated[str, add_messages, Field(..., description="사용자 쿼리")]
    retrieved_documents: Annotated[List[Document], add_messages, Field(default_factory=list, description="검색된 문서")]
    formatted_context: Annotated[str, add_messages, Field(default="", description="포맷팅된 컨텍스트")]
    response: Annotated[str, add_messages, Field(default="", description="최종 응답")]