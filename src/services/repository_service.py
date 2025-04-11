"""
저장소 서비스 모듈: GitHub 저장소 클론 및 처리 관련 서비스를 제공합니다.

이 모듈은 GitHub 저장소 클론, 분석 및 임베딩을 처리하기 위한 기능을 제공합니다.
"""

from typing import Dict, Any, Optional, List
import logging
import uuid
import os
import asyncio
from dotenv import load_dotenv

from src.modules.code_loaders import MultiLanguageDocumentLoader
from src.modules.code_splitter import MultiLanguageDocumentSplitter
from src.modules.repo_manage import clone_repo_url, remove_repository
from src.services.rag_service import get_document_embedder

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 상수 
TEMP_REPO_PATH = os.getenv("TEMP_REPO_PATH", "/tmp/repo_data")
MAX_CONCURRENT_CLONES = int(os.getenv("MAX_CONCURRENT_CLONES", "3"))

# 동시성 제한을 위한 세마포어
_clone_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CLONES)


def analyze_repository(repo_path: str) -> Dict[str, Any]:
    """
    레포지토리의 구조를 분석합니다.
    
    Args:
        repo_path: 분석할 저장소 경로
        
    Returns:
        저장소 구조 정보를 담은 사전
    """
    structure = {
        "directories": [],
        "languages": set(),
        "file_count": 0
    }
    
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')
        
        rel_path = os.path.relpath(root, repo_path)
        if rel_path != '.':
            structure["directories"].append(rel_path)
        
        for file in files:
            structure["file_count"] += 1
            ext = os.path.splitext(file)[1].lower()
            if ext:
                structure["languages"].add(ext[1:])  # 점(.) 제거
    
    structure["languages"] = list(structure["languages"])
    return structure


def get_readme_content(repo_path: str) -> str:
    """
    README 파일의 내용을 반환합니다.
    
    Args:
        repo_path: README 파일을 찾을 저장소 경로
        
    Returns:
        README 파일 내용 또는 "README not found" 메시지
    """
    readme_paths = ['README.md', 'README.rst', 'README.txt', 'README']
    
    for path in readme_paths:
        full_path = os.path.join(repo_path, path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"README 파일 읽기 오류: {str(e)}")
                return f"README 파일을 읽는 중 오류 발생: {str(e)}"
    
    return "README not found"


def repository_clone(repo_url: str) -> Dict[str, Any]:
    """
    GitHub 레포지토리를 RAG에 저장하고 분석 결과를 반환합니다.
    (agent1.py에서 가져온 함수, 비동기 버전은 clone_repository 사용)
    
    Args:
        repo_url: GitHub 저장소 URL
        
    Returns:
        저장소 분석 결과를 담은 사전
    
    Raises:
        RuntimeError: 저장소 클론 실패 시 발생
    """
    # 1. 리포지토리 클론
    repo_path = f"/tmp/repo_data/{uuid.uuid4()}"
    repo = clone_repo_url(repo_url, repo_path)
    if repo is None:
        raise RuntimeError(f"Failed to clone repository: returned None :: ❌ 클론 실패: {repo_url}")
    
    try:
        # 2. 리포지토리 분석
        analysis = {
            "repository_url": repo_url,
            "structure": analyze_repository(repo.working_dir),
            "readme": get_readme_content(repo.working_dir),
            "summary": {
                "total_files": 0,
                "languages": set(),
                "main_directories": []
            }
        }
        
        # 3. 리포지토리 내 모든 파일 로드
        loader = MultiLanguageDocumentLoader(repo.working_dir)
        documents = loader.load_documents()
        
        # 4. 파일 분할
        splitter = MultiLanguageDocumentSplitter()
        chunks = splitter.split_documents(documents)
        
        # 5. 분할된 파일 임베딩
        embedder = get_document_embedder()
        embedder.add_documents(chunks)
        
        # 6. 통계 정보 업데이트
        analysis["summary"]["total_files"] = len(documents)
        analysis["summary"]["document_chunks"] = len(chunks)
        
        return analysis
        
    finally:
        # 7. 레포지토리 클론 데이터 삭제
        remove_repository(repo_path)


async def clone_repository(repo_url: str) -> Dict[str, Any]:
    """
    GitHub 저장소를 클론하고 RAG에 저장한 후 분석 결과를 반환합니다.

    Args:
        repo_url: GitHub 저장소 URL

    Returns:
        저장소 분석 결과를 담은 사전
    
    Raises:
        RuntimeError: 저장소 클론 실패 시 발생
    """
    # GitHub URL 정규화
    repo_url = normalize_github_url(repo_url)
    
    # 임시 저장소 경로 생성
    os.makedirs(TEMP_REPO_PATH, exist_ok=True)
    repo_path = f"{TEMP_REPO_PATH}/{uuid.uuid4()}"
    
    # 세마포어를 사용한 동시성 제한
    async with _clone_semaphore:
        logger.info(f"저장소 클론 시작: {repo_url} -> {repo_path}")
        
        # 1. 저장소 클론
        repo = clone_repo_url(repo_url, repo_path)
        if repo is None:
            raise RuntimeError(f"저장소 클론 실패: {repo_url}")
        
        try:
            # 2. 저장소 분석
            logger.info(f"저장소 분석 중: {repo_url}")
            analysis = {
                "repository_url": repo_url,
                "structure": analyze_repository(repo.working_dir),
                "readme": get_readme_content(repo.working_dir),
                "summary": {
                    "total_files": 0,
                    "document_chunks": 0,
                    "languages": set(),
                    "main_directories": []
                }
            }
            
            # 3. 저장소 내 모든 파일 로드
            logger.info(f"저장소 파일 로드 중: {repo_url}")
            loader = MultiLanguageDocumentLoader(repo.working_dir)
            documents = loader.load_documents()
            
            # 4. 파일 분할
            logger.info(f"문서 분할 중: {len(documents)}개 파일")
            splitter = MultiLanguageDocumentSplitter()
            chunks = splitter.split_documents(documents)
            logger.info(f"분할 완료: {len(chunks)}개 청크")
            
            # 5. 분할된 파일 임베딩
            logger.info(f"문서 임베딩 중: {len(chunks)}개 청크")
            embedder = get_document_embedder()
            embedder.add_documents(chunks)
            
            # 6. 통계 정보 업데이트
            analysis["summary"]["total_files"] = len(documents)
            analysis["summary"]["document_chunks"] = len(chunks)
            analysis["summary"]["languages"] = analysis["structure"]["languages"]
            
            # 주요 디렉토리 추출 (최대 5개)
            main_dirs = sorted(
                analysis["structure"]["directories"], 
                key=lambda d: len(d.split('/'))
            )[:5]
            analysis["summary"]["main_directories"] = main_dirs
            
            logger.info(f"저장소 처리 완료: {repo_url}")
            return analysis
            
        finally:
            # 7. 저장소 클론 데이터 삭제
            logger.info(f"임시 저장소 삭제 중: {repo_path}")
            remove_repository(repo_path)
            logger.debug(f"임시 저장소 삭제 완료: {repo_path}")


def normalize_github_url(url: str) -> str:
    """
    GitHub URL을 정규화합니다.
    
    Args:
        url: 정규화할 GitHub URL
        
    Returns:
        정규화된 GitHub URL
    """
    # 기본 검증
    if not url:
        return url
        
    # 후행 슬래시 제거
    url = url.rstrip('/')
    
    # .git 확장자 제거
    if url.endswith('.git'):
        url = url[:-4]
        
    return url 