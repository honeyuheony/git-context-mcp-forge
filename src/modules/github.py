from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
from dotenv import load_dotenv
import logging
import os
import re
import time
import requests
from urllib.parse import urlparse

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logger = logging.getLogger(__name__)

# 전역 상수 
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"

@dataclass
class RepositoryInfo:
    """GitHub 저장소 정보를 저장하는 클래스"""
    owner: str
    repo: str
    branch: str

class GitHubClient:
    """GitHub REST API와 상호작용하는 클라이언트 클래스"""
    
    def __init__(self, token: str = None):
        """
        GitHubClient 초기화
        
        Args:
            token: GitHub API 토큰 (없으면 환경 변수에서 가져옴)
        """
        self.token = token or GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub 토큰이 필요합니다. 환경 변수 GITHUB_TOKEN을 설정하세요.")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # API 요청 제한을 위한 속도 조절 설정
        self.request_interval = 0.5  # 초 단위
        self.last_request_time = 0
    
    def _throttle_request(self):
        """API 요청 속도 제한을 위한 메서드"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()
    
    def parse_repo_url(self, repo_url: str) -> RepositoryInfo:
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
        
        owner, repo = path_parts[0], path_parts[1]
        
        # 기본 브랜치 이름 가져오기
        api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
        
        self._throttle_request()
        response = requests.get(api_url, headers=self.headers)
        response.raise_for_status()
        
        data = response.json()
        branch = data.get("default_branch", "main")
        
        return RepositoryInfo(owner=owner, repo=repo, branch=branch)
    
    def get_directory_contents(self, repo_info: RepositoryInfo, path: str = "") -> List[Dict[str, Any]]:
        """
        GitHub REST API를 사용하여 디렉토리 내용을 가져옵니다.
        
        Args:
            repo_info: 저장소 정보
            path: 가져올 디렉토리 경로 (비어있으면 루트)
            
        Returns:
            List[Dict[str, Any]]: 디렉토리 내용 목록
        """
        api_url = f"{GITHUB_API_BASE}/repos/{repo_info.owner}/{repo_info.repo}/contents/{path}"
        if path:
            api_url += f"?ref={repo_info.branch}"
        else:
            api_url = f"{api_url}?ref={repo_info.branch}"
        
        logger.info(f"디렉토리 내용 조회: {path or '/'}")
        
        self._throttle_request()
        response = requests.get(api_url, headers=self.headers)
        
        if response.status_code == 404:
            logger.warning(f"디렉토리를 찾을 수 없음: {path}")
            return []
        
        response.raise_for_status()
        return response.json()
    
    def get_file_content(self, repo_info: RepositoryInfo, path: str) -> Optional[str]:
        """
        GitHub REST API를 사용하여 파일 내용을 가져옵니다.
        
        Args:
            repo_info: 저장소 정보
            path: 파일 경로
            
        Returns:
            Optional[str]: 파일 내용 또는 None
        """
        import base64
        
        api_url = f"{GITHUB_API_BASE}/repos/{repo_info.owner}/{repo_info.repo}/contents/{path}?ref={repo_info.branch}"
        
        self._throttle_request()
        response = requests.get(api_url, headers=self.headers)
        
        if response.status_code == 404:
            logger.warning(f"파일을 찾을 수 없음: {path}")
            return None
        
        response.raise_for_status()
        data = response.json()
        
        # 파일이 너무 큰 경우 (GitHub API는 일정 크기 이상의 파일에 대해 다른 URL을 제공)
        if "content" not in data and "download_url" in data:
            self._throttle_request()
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
    
    def process_repository(self, repo_url: str) -> List[Dict[str, Any]]:
        """
        저장소의 파일들을 처리하고 가치 있는 텍스트 파일을 반환합니다.
        
        Args:
            repo_url: GitHub 저장소 URL
            
        Returns:
            List[Dict[str, Any]]: 처리된 파일 정보 목록
        """
        try:
            start_time = time.time()
            logger.info(f"저장소 처리 시작: {repo_url}")
            
            # 저장소 정보 가져오기
            repo_info = self.parse_repo_url(repo_url)
            
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
                contents = self.get_directory_contents(repo_info, current_dir)
                
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
                        file_content = self.get_file_content(repo_info, item_path)
                        
                        # 유효한 텍스트이고 가치 있는 내용인 경우 추가
                        if file_content and self._is_valuable_text(file_content, item_path):
                            all_files.append({
                                'path': item_path,
                                'name': os.path.basename(item_path),
                                'type': 'file',
                                'text': file_content,
                                'metadata': {
                                    'file_size': len(file_content),
                                    'extension': ext if ext else ''
                                }
                            })
                
                # 로깅
                if len(all_files) % 20 == 0 and all_files:
                    logger.info(f"처리 진행: {len(all_files)}개 파일, {len(processed_dirs)}개 디렉토리, 남은 디렉토리: {len(dirs_queue)}개")
            
            elapsed_time = time.time() - start_time
            logger.info(f"저장소 처리 완료: {len(all_files)}개 파일 추출 (소요 시간: {elapsed_time:.2f}초)")
            
            return all_files
            
        except Exception as e:
            logger.error(f"저장소 처리 중 오류 발생: {e}")
            return []
    
    def _is_valuable_text(self, text: str, file_path: str) -> bool:
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


def main(repo_url: str = None, verbose: bool = False):
    """
    메인 함수 - 저장소 처리 및 결과 출력
    
    Args:
        repo_url: GitHub 저장소 URL (없으면 기본값 사용)
        file_types: 처리할 파일 확장자 목록 (없으면 모든 파일 처리)
        verbose: 상세 정보 출력 여부
    
    Returns:
        List[Dict[str, Any]]: 처리된 파일 정보 목록
    """
    # 로깅 레벨 설정
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 기본 저장소 URL 설정
    repo_url = repo_url or "https://github.com/honeyuheony/git-context-mcp-forge"
    
    logger.info(f"GitHub 저장소 처리 시작: {repo_url}")
    
    try:
        # GitHub 클라이언트 생성
        client = GitHubClient()
        
        # 저장소 처리
        processed_files = client.process_repository(repo_url)
        
        # 결과 출력
        logger.info(f"총 처리된 파일: {len(processed_files)}개")
        
        # 파일 확장자별 통계
        extensions = {}
        for file in processed_files:
            ext = file.get('metadata', {}).get('extension', '')
            extensions[ext] = extensions.get(ext, 0) + 1
        
        logger.info("파일 확장자별 통계:")
        for ext, count in sorted(extensions.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  - {ext or '확장자 없음'}: {count}개")
        
        # 상세 정보 출력 (verbose 모드)
        if verbose and processed_files:
            logger.debug("처리된 파일 목록:")
            for file in processed_files:
                logger.debug(f"  - {file['path']} ({file['metadata']['file_size']} bytes)")
        
        return processed_files
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
        if verbose:
            import traceback
            logger.debug(traceback.format_exc())
        return []


if __name__ == "__main__":
    import argparse
    
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description='GitHub 저장소 파일 처리 도구')
    parser.add_argument('--repo', type=str, help='GitHub 저장소 URL')
    parser.add_argument('--verbose', action='store_true', help='상세 정보 출력')
    
    args = parser.parse_args()
    
    # 명령행 인자로 main 함수 호출
    main(
        repo_url=args.repo,
        verbose=args.verbose
    )

