from abc import ABC, abstractmethod
from src.models.git_repository import RepositoryInfo, ParsedCode
from typing import List, Dict, Any, Optional

import os
import requests
from urllib.parse import urlparse
import time
import re
from src.config.log_config import Logger

logger = Logger()

class GitRepositoryUtils(ABC):
    @classmethod
    @abstractmethod
    def parse_repo_url(cls, repo_url: str) -> RepositoryInfo:
        pass

    @classmethod
    @abstractmethod
    def fetch_repo_contents(cls, repo_url: str) -> List[ParsedCode]:
        pass
    
    @staticmethod
    @abstractmethod
    def _is_valuable_text(text: str, file_path: str) -> bool:
        """
        텍스트가 가치 있는지 판단합니다.
        
        Args:
            text: 텍스트 내용
            file_path: 파일 경로
            
        Returns:
            bool: 가치 있는 텍스트이면 True
        """
        # 빈 텍스트는 가치 없음
        if not text or text.strip() == "":
            return False
        
        # 바이너리 데이터로 보이는 텍스트는 제외
        if '\0' in text[:1000]:
            return False
        
        # 파일 확장자 확인
        _, ext = os.path.splitext(file_path.lower())
        
        # 무시할 파일 확장자
        ignore_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.ogg',
            '.zip', '.tar', '.gz', '.rar', '.7z',
            '.pyc', '.class', '.o', '.obj', '.dll', '.so', '.dylib',
            '.min.js', '.min.css',
            '.lock', '.log', '.tmp', '.temp',
            '.db', '.sqlite', '.sqlite3',
        }
        
        if ext in ignore_extensions:
            return False
        
        # 무시할 경로 패턴
        ignore_patterns = [
            r'node_modules/', r'\.git/', r'__pycache__/',
            r'\.venv/', r'venv/', r'env/', r'\.env/',
            r'\.DS_Store', r'Thumbs\.db',
            r'dist/', r'build/', r'out/',
            r'\.pytest_cache/', r'\.ruff_cache/',
            r'\.next/', r'\.nuxt/',
            r'\.vscode/', r'\.idea/', r'\.vs/',
            r'package-lock\.json', r'yarn\.lock', r'pnpm-lock\.yaml',
        ]
        
        for pattern in ignore_patterns:
            if re.search(pattern, file_path):
                return False
        
        # 최대 크기 제한
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        if len(text) > MAX_FILE_SIZE:
            return False
        
        # 텍스트 길이가 너무 짧으면 가치 없음
        if len(text.strip()) < 10:
            return False
        
        # 코드 파일인지 판단
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
            '.cs', '.go', '.rb', '.php', '.swift', '.kt', '.rs', '.sh', '.pl',
            '.scala', '.m', '.lua', '.ex', '.exs', '.erl', '.hs', '.dart',
        }
        
        # 문서 파일인지 판단
        doc_extensions = {
            '.md', '.txt', '.rst', '.html', '.htm', '.xml', '.json', '.yaml', '.yml'
        }
        
        # 코드 파일은 대부분 가치 있음
        if ext in code_extensions and text.count('\n') > 5:
            return True
            
        # 문서 파일은 충분히 길면 가치 있음
        if ext in doc_extensions and len(text.strip()) > 100:
            return True
        
        # 기타 파일은 길이로 판단
        return len(text.strip()) > 200


class GitHubRepositoryUtils(GitRepositoryUtils):
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
    GITHUB_API_BASE = "https://api.github.com"
    if not GITHUB_TOKEN:
        raise ValueError("GitHub 토큰이 필요합니다. 환경 변수 GITHUB_TOKEN을 설정하세요.")
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    @classmethod
    def parse_repo_url(cls, repo_url: str) -> RepositoryInfo:
        """
        GitHub 저장소 URL에서 소유자, 저장소 이름, 기본 브랜치를 추출합니다.
        
        Args:
            repo_url: GitHub 저장소 URL
            
        Returns:
            RepositoryInfo: 추출된 저장소 정보
            
        Raises:
            ValueError: URL 형식이 잘못된 경우
        """
        # URL 정규화
        repo_url = repo_url.rstrip('/')
        if repo_url.endswith('.git'):
            repo_url = repo_url[:-4]
        
        # URL 파싱
        parsed_url = urlparse(repo_url)
        if parsed_url.netloc != 'github.com':
            raise ValueError(f"GitHub URL이 아닙니다: {repo_url}")
        
        # 경로에서 소유자와 저장소 이름 추출
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"잘못된 GitHub URL 형식: {repo_url}")
        
        owner, repo_name = path_parts[0], path_parts[1]
        
        # 기본 브랜치 이름 가져오기
        api_url = f"{cls.GITHUB_API_BASE}/repos/{owner}/{repo_name}"
        
        # cls._throttle_request()
        response = requests.get(api_url, headers=cls.headers)
        response.raise_for_status()
        
        data = response.json()
        branch = data.get("default_branch", "main")
        
        return RepositoryInfo(repo_url=repo_url, owner=owner, repo_name=repo_name, branch=branch)


    @classmethod
    def fetch_repo_contents(cls, repo_url: str) -> List[ParsedCode]:
        """
        저장소의 파일들을 처리하고 가치 있는 텍스트 파일을 반환합니다.
        
        Args:
            repo_url: GitHub 저장소 URL
            
        Returns:
            List[ParsedCode]: 처리된 파일 정보 목록
        """
        try:
            start_time = time.time()
            logger.info(f"저장소 처리 시작: {repo_url}")
            
            # 저장소 정보 가져오기
            repo_info = cls.parse_repo_url(repo_url)
            
            # 저장소 내 모든 파일 수집 (BFS 방식)
            all_files = []
            dirs_queue = [""]  # 루트 디렉토리부터 시작
            processed_dirs = set()
            
            while dirs_queue:
                current_dir = dirs_queue.pop(0)
                
                if current_dir in processed_dirs:
                    continue
                processed_dirs.add(current_dir)
                
                # 디렉토리 내용 가져오기
                contents = cls._get_directory_contents(repo_info, current_dir)
                
                for item in contents:
                    item_path = item.get("path", "")
                    item_type = item.get("type", "")
                    
                    # 디렉토리인 경우 큐에 추가
                    if item_type == "dir":
                        dirs_queue.append(item_path)
                    
                    # 파일인 경우 처리
                    elif item_type == "file":
                        # 파일 확장자 체크
                        _, ext = os.path.splitext(item_path)
                        ext = ext.lstrip('.').lower()
                        
                        # 파일 내용 가져오기
                        file_content = cls._get_file_content(repo_info, item_path)
                        
                        # 유효한 텍스트이고 가치 있는 내용인 경우 추가
                        if file_content and cls._is_valuable_text(file_content, item_path):
                            all_files.append(ParsedCode(
                                path=item_path,
                                name=os.path.basename(item_path),
                                type='file',
                                text=file_content,
                                metadata={
                                    'repo_url': repo_info.repo_url,
                                    'extension': ext if ext else ''
                                }
                            ))
                
                # 로깅
                if len(all_files) % 20 == 0 and all_files:
                    logger.info(f"처리 진행: {len(all_files)}개 파일, {len(processed_dirs)}개 디렉토리, 남은 디렉토리: {len(dirs_queue)}개")
            
            elapsed_time = time.time() - start_time
            logger.info(f"저장소 처리 완료: {len(all_files)}개 파일 추출 (소요 시간: {elapsed_time:.2f}초)")
            
            return all_files
            
        except Exception as e:
            logger.error(f"저장소 처리 중 오류 발생: {e}")
            return []

    @classmethod
    def _get_directory_contents(cls, repo_info: RepositoryInfo, path: str = "") -> List[Dict[str, Any]]:
        """
        GitHub REST API를 사용하여 디렉토리 내용을 가져옵니다.
        
        Args:
            repo_info: 저장소 정보
            path: 가져올 디렉토리 경로 (비어있으면 루트)
            
        Returns:
            List[Dict[str, Any]]: 디렉토리 내용 목록
        """
        api_url = f"{cls.GITHUB_API_BASE}/repos/{repo_info.owner}/{repo_info.repo_name}/contents/{path}"
        if path:
            api_url += f"?ref={repo_info.branch}"
        else:
            api_url = f"{api_url}?ref={repo_info.branch}"
        
        logger.info(f"디렉토리 내용 조회: {path or '/'}")
        
        # cls._throttle_request()
        response = requests.get(api_url, headers=cls.headers)
        
        if response.status_code == 404:
            logger.warning(f"디렉토리를 찾을 수 없음: {path}")
            return []
        
        response.raise_for_status()
        return response.json()
    
    @classmethod
    def _get_file_content(cls, repo_info: RepositoryInfo, path: str) -> Optional[str]:
        """
        GitHub REST API를 사용하여 파일 내용을 가져옵니다.
        
        Args:
            repo_info: 저장소 정보
            path: 파일 경로
            
        Returns:
            Optional[str]: 파일 내용 또는 None
        """
        import base64
        
        api_url = f"{cls.GITHUB_API_BASE}/repos/{repo_info.owner}/{repo_info.repo_name}/contents/{path}?ref={repo_info.branch}"
        
        # cls._throttle_request()
        response = requests.get(api_url, headers=cls.headers)
        
        if response.status_code == 404:
            logger.warning(f"파일을 찾을 수 없음: {path}")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # 파일이 너무 큰 경우 (GitHub API는 일정 크기 이상의 파일에 대해 다른 URL을 제공)
        if "content" not in data and "download_url" in data:
            # cls._throttle_request()
            content_response = requests.get(data["download_url"])
            content_response.raise_for_status()
            return content_response.text
        
        # 바이너리 파일 체크 (확장자로 간단히 확인)
        _, ext = os.path.splitext(path.lower())
        binary_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.pdf', '.zip', '.exe'}
        if ext in binary_extensions:
            return None
        
        # 파일 크기 체크
        if data.get("size", 0) > 10 * 1024 * 1024:  # 10MB 초과
            logger.warning(f"파일이 너무 큼: {path} ({data.get('size', 0)} bytes)")
            return None
        
        # Base64 디코딩
        try:
            content = data.get("content", "")
            if content:
                # GitHub API는 Base64로 인코딩된 내용을 줌
                content = content.replace('\n', '')
                decoded_content = base64.b64decode(content).decode('utf-8')
                return decoded_content
            return None
        except Exception as e:
            logger.error(f"파일 내용 디코딩 실패: {path}, 오류: {e}")
            return None