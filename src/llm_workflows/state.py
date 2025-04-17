from typing import Dict, List, Any, TypedDict, Optional, Annotated
from langchain_core.documents import Document
from src.models.git_repository import ParsedCode, CodeMetadata, RepositoryInfo
from pydantic import BaseModel, Field
from langgraph.graph import add_messages

# class CodeDocument(Document):
#     page_content: str
#     metadata: CodeMetadata
    

class RepositoryToVectorDBState(BaseModel):
    repo_info: Annotated[RepositoryInfo, Field(..., description="저장소 정보")]
    documents_by_language: Annotated[Dict[str, List[Document]], Field(default_factory=dict, description="언어별 문서")]
    split_documents: Annotated[List[Document], add_messages, Field(default_factory=list, description="분할된 문서")]

    
class RAGState(TypedDict):
    """RAG 그래프 상태"""
    # 입력
    query: Optional[str]         # 사용자 쿼리
    repo_url: Optional[str]      # 저장소 URL
    
    # 저장소 코드 파싱
    parsed_code: Optional[List[ParsedCode]]  # 파싱된 코드

    # 코드 문서 생성
    code_documents: Optional[List[Document]]  # 코드 문서
    split_documents: Optional[List[Document]]  # 분할된 문서
    
    # 검색 상태
    retrieved_documents: Optional[List[Document]]  # 검색된 문서
    
    # 응답 상태
    formatted_context: Optional[str]   # 포맷팅된 컨텍스트
    response: Optional[str]            # 최종 응답
    
    # 메타데이터
    metadata: Dict[str, Any]