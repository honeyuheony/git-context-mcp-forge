"""
MCP 도구 모듈: ModelContextProtocol(MCP)의 도구를 정의합니다.

이 모듈은 FastMCP 서버에 등록할 도구 함수를 제공합니다:
- repo_to_rag: GitHub 저장소 클론 및 임베딩
- rag_to_context: 벡터 검색을 통한 질문 응답
"""

from typing import Dict, Any, List
import logging
from src.application.rag_service import search_documents
from src.mcp.formatters import format_repo_context, format_search_results
from src.modules.code_loader import load_documents
from src.modules.github import GitHubClient
from src.modules.code_splitter import MultiLanguageDocumentSplitter
from src.modules.rag import DocumentEmbedder

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 변수
client = GitHubClient()
embedder = DocumentEmbedder()
splitter = MultiLanguageDocumentSplitter()

async def repo_to_rag(repo_url: str) -> str:
    """
    GITHUB Repository ⇒ Embedding and Store in VectorDB
    주어진 GitHub 저장소의 소스 코드를 임베딩하여 VectorDB에 저장합니다.
    이 과정은 벡터 기반 코드 검색 및 검색 기반 질문 응답을 가능하게 합니다.

    Parameters:
        repo_url: GitHub 저장소 URL
    """
    logger.info(f"저장소 클론 및 임베딩 요청: {repo_url}")
    try:
        # 저장소 처리
        processed_files = client.process_repository(repo_url)
        documents = load_documents(repo_url, processed_files)
        split_documents = splitter.split_documents(documents)
        # 문서 저장
        embedder.add_documents(split_documents)
        # result = format_repo_context(repo_url)
        logger.info(f"저장소 처리 완료: {repo_url}")
        return "저장소 처리 완료"
    except Exception as e:
        logger.error(f"저장소 처리 중 오류 발생: {str(e)}", exc_info=True)
        return f"저장소 처리 중 오류가 발생했습니다: {str(e)}"


async def rag_to_context(query: str) -> str:
    """
    Embedding Search ⇒ Generate Answer
    질문을 받아 임베딩 기반 유사성 검색을 수행하고, VectorDB에서 가장 관련성 높은 문서를 기반으로 응답을 생성합니다.

    Parameters:
        query: 사용자의 입력 질문
    """
    logger.info(f"RAG 질의 요청: {query}")
    try:
        results = search_documents(query)
        response = format_search_results(results)
        logger.info(f"RAG 질의 응답 생성 완료 (결과 {len(results)}개)")
        return response
    except Exception as e:
        logger.error(f"응답 생성 중 오류 발생: {str(e)}", exc_info=True)
        return f"응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    
async def test_repo_to_rag():
    """
    Test the repo_to_rag function with a sample GitHub repository URL.
    """
    repo_url = "https://github.com/honeyuheony/git-context-mcp-forge"
    result = await repo_to_rag(repo_url)
    print(result)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_repo_to_rag())
