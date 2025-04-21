from typing import Iterator, Optional, List

from langchain_core.document_loaders import Blob
from langchain_core.document_loaders import BlobLoader
from src.models.git_repository import ParsedCode

import mimetypes


class GitHubBlobLoader(BlobLoader):
    """GitHub 파일을 로드하는 BlobLoader"""
    
    def __init__(self, parsed_codes: List[ParsedCode]):
        """
        GitHub Blob Loader 초기화
        
        Args:
            parsed_code: 파일 내용
        """
        self.parsed_codes = parsed_codes
    
    def yield_blobs(self) -> Iterator[Blob]:
        """
        GitHub 파일 내용에서 Blob 객체 생성
        
        Args:
            parsed_codes: 파일 내용 목록
        
        Yields:
            Blob: 생성된 Blob 객체
        """
        for parsed_code in self.parsed_codes:
            path = parsed_code.path
            content = parsed_code.text
            
            if not path or content is None:
                return
            
            # 파일 확장자 확인 및 MIME 타입 추측
            mimetype = mimetypes.guess_type(path)[0]
            
            # 메타데이터 구성
            metadata = {
                'repo_url': parsed_code.metadata.repo_url,
                'path': '/' + parsed_code.path.replace(f"/{parsed_code.name}", ""),
                'filename': parsed_code.name,
                'extension': parsed_code.metadata.extension
                # "file_size": len(content),
            }
            
            yield Blob.from_data(
                data=content,
                mime_type=mimetype,
                path=path,
                metadata=metadata
            )