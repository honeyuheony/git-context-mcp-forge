"""
MCP 서버 애플리케이션의 시작점

이 모듈은 Model Context Protocol(MCP) 서버를 생성하고 실행합니다.
GitHub 저장소 분석 및 RAG 기반 질문 응답 기능을 제공합니다.
"""

import logging
import sys
import os
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from src.mcp.tools import repo_to_rag, rag_to_context

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# MCP 서버 도움말 메시지
HELP_MESSAGE = """
MCP 도구를 사용하기 위해서는 다음과 같이 질문하시면 됩니다:

GitHub 저장소를 검색하고 싶으시다면:
"https://github.com/사용자명/저장소명 저장소에 대해 알려주세요"
"https://github.com/tensorflow/tensorflow 코드를 분석해주세요"

저장된 저장소에 대해 질문하고 싶으시다면:
"이 코드는 어떤 기능을 하나요?"
"이 라이브러리의 주요 특징은 무엇인가요?"
"이 코드에서 ~부분은 어떻게 작동하나요?"
"""

def create_mcp_app(
    name: str = "git-context-mcp-forge",
    version: str = "0.1.0",
    description: str = "GitHub 저장소 분석 및 RAG 기반 질문 응답 서비스"
) -> FastMCP:
    """
    MCP 서버 인스턴스를 생성합니다.

    Args:
        name: MCP 서버 이름
        version: MCP 서버 버전
        description: MCP 서버 설명

    Returns:
        FastMCP 인스턴스
    """
    # MCP 서버 인스턴스 생성
    mcp = FastMCP(
        name=name,
        version=version,
        description=description
    )

    # 도구 등록 - 데코레이터 방식 대신 직접 등록 방식 사용
    mcp.add_tool(repo_to_rag)
    mcp.add_tool(rag_to_context)

    return mcp


def main():
    """애플리케이션 시작점"""
    try:
        logger.info("MCP 서버 시작 중...")
        logger.info(HELP_MESSAGE)

        # MCP 서버 생성 및 실행
        app = create_mcp_app()
        
        # 환경 변수에서 전송 방식을 가져오거나 기본값으로 "sse" 사용
        transport = os.getenv("FASTMCP_TRANSPORT", "sse")
        host = os.getenv("FASTMCP_HOST", "localhost")
        port = os.getenv("FASTMCP_PORT", "8000")
        debug = os.getenv("FASTMCP_DEBUG", "false").lower() == "true"
        
        # 서버 실행
        logger.info(f"MCP {host}:{port} 서버를 {transport} 모드로 실행합니다. 디버그 모드: {debug}")
        app.run()
    except Exception as e:
        logger.error(f"MCP 서버 실행 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 