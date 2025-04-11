"""
응답 포맷 모듈: MCP 도구의 응답을 포맷팅하는 함수를 제공합니다.
"""

from typing import List, Dict, Any
from langchain_core.documents import Document


def format_repo_context(repo_info: Dict[str, Any]) -> str:
    """
    저장소 분석 결과를 마크다운 형식으로 포맷팅합니다.

    Args:
        repo_info: 저장소 분석 정보를 담은 사전

    Returns:
        마크다운 형식의 저장소 분석 결과
    """
    markdown_result = f"""
    ## 저장소 분석 결과

    ### 기본 정보
    - **저장소 URL**: {repo_info['repository_url']}
    - **총 파일 수**: {repo_info['summary']['total_files']}
    - **총 청크 수**: {repo_info['summary']['document_chunks']}

    ### 저장소 구조
    - **디렉토리 수**: {len(repo_info['structure']['directories'])}
    - **사용 언어**: {', '.join(repo_info['structure']['languages'])}

    ### README 내용
    {repo_info['readme']}
    """
    return markdown_result


def format_search_results(docs: List[Document]) -> str:
    """
    검색 결과를 마크다운 형식으로 포맷팅합니다.

    Args:
        docs: 포맷팅할 문서 목록

    Returns:
        마크다운 형식의 검색 결과
    """
    if not docs:
        return "관련 정보를 찾을 수 없습니다."

    markdown_results = "## 검색 결과\n\n"

    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source", "알 수 없는 출처")
        page = doc.metadata.get("page", None)
        page_info = f" (페이지: {page + 1})" if page is not None else ""

        markdown_results += f"### 결과 {i}{page_info}\n\n"
        markdown_results += f"{doc.page_content}\n\n"
        markdown_results += f"출처: {source}\n\n"
        markdown_results += "---\n\n"

    return markdown_results 