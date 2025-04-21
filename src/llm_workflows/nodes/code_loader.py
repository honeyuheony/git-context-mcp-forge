from src.llm_workflows.state import RepositoryToVectorDBState
from src.utils.git_repository_utils import GitHubRepositoryUtils
from src.models.git_repository import ParsedCode
from typing import List, Dict, Any, Optional
from collections import defaultdict
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser

import os
import tempfile
import traceback
import logging

logger = logging.getLogger(__name__)

# 전역 상수 
EXTENSION_LANGUAGE_MAP = {
    'py': 'PYTHON',
    'js': 'JS',
    'jsx': 'JS',
    'mjs': 'JS',
    'ts': 'TS',
    'tsx': 'TS',
    'java': 'JAVA',
    'cpp': 'CPP',
    'hpp': 'CPP',
    'cc': 'CPP',
    'h': 'C',
    'cxx': 'CPP',
    'hxx': 'CPP',
    'go': 'GO',
    'rb': 'RUBY',
    'rake': 'RUBY',
    'gemspec': 'RUBY',
    'rs': 'RUST',
    'php': 'PHP',
    'proto': 'PROTO',
    'rst': 'RST',
    'scala': 'SCALA',
    'md': 'MARKDOWN',
    'markdown': 'MARKDOWN',
    'tex': 'LATEX',
    'html': 'HTML',
    'htm': 'HTML',
    'sol': 'SOL',
    'cs': 'CSHARP',
    'cob': 'COBOL',
    'cbl': 'COBOL',
    'c': 'C',
    'lua': 'LUA',
    'pl': 'PERL',
    'pm': 'PERL',
    'ex': 'ELIXIR',
    'exs': 'ELIXIR',
    '': 'UNKNOWN'  # 빈 확장자에 대한 처리 추가
}

def repo_to_documents(state: RepositoryToVectorDBState) -> RepositoryToVectorDBState:
    """저장소 컨텐츠를 Document 객체로 변환하는 노드"""
    parsed_code_list: List[ParsedCode] = GitHubRepositoryUtils.fetch_repo_contents(state.repo_info.repo_url)
    documents: Dict[str, List] = load_documents(parsed_code_list)
    state.documents_by_language = documents
    return state

def _create_language_parser(extension: str) -> Optional[LanguageParser]:
    """
    언어별 파서를 생성합니다. 파서가 지원되지 않는 경우 기본 파서를 반환합니다.
    
    Args:
        extension: 파일 확장자
        
    Returns:
        LanguageParser 객체
    """
    try:
        # 파서가 지원되는 언어와 해당 값 매핑
        SUPPORTED_PARSER_LANGUAGES = {
            'PYTHON': 'python',
            'JS': 'js',
            'TS': 'ts',
            'JAVA': 'java',
            'CPP': 'cpp',
            'C': 'c',
            'CSHARP': 'csharp',
            'COBOL': 'cobol',
            'ELIXIR': 'elixir',
            'GO': 'go',
            'KOTLIN': 'kotlin',
            'LUA': 'lua',
            'PERL': 'perl',
            'RUBY': 'ruby',
            'RUST': 'rust',
            'SCALA': 'scala'
        }
        
        # 확장자에서 언어 결정
        lang = EXTENSION_LANGUAGE_MAP.get(extension, "UNKNOWN")
        
        # UNKNOWN이거나 지원되지 않는 언어는 기본 파서 사용
        if lang not in SUPPORTED_PARSER_LANGUAGES or lang == 'UNKNOWN':
            logger.debug(f"확장자 {extension}에 대한 언어 매핑이 없어 기본 파서로 처리됩니다.")
            return LanguageParser()
            
        parser_value = SUPPORTED_PARSER_LANGUAGES[lang]
        return LanguageParser(language=parser_value)
    except Exception as e:
        logger.error(
            f"{extension} 확장자 파서 생성 중 오류 발생\n"
            f"Error: {str(e)}\n"
            f"Traceback:\n{traceback.format_exc()}"
        )
        # 오류 발생 시에도 기본 파서 반환
        return LanguageParser()
    

def load_documents(processed_files: List[Dict[str, Any]]) -> Dict[str, List]:
    """
    처리된 파일 목록을 받아 파일확장자별로 LangChain Document 객체로 변환합니다.
    
    Args:
        processed_files: 처리된 파일 목록
        {
            'path': path_id,
            'name': entry.name,
            'type': 'file',
            'text': text,
            'metadata': {
                'extension': ext.lstrip('.').lower() if ext else '',
                'repo_url': repo_url
            }
        }   
        
    Returns:
        파일확장자별로 LangChain Document 객체로 변환된 목록
    """
    documents_by_language = defaultdict(list)
    
    for file in processed_files:
        extension = file.metadata.extension
        lang = EXTENSION_LANGUAGE_MAP.get(extension, "UNKNOWN")
        
        try:
            # 임시 파일을 생성하여 텍스트 저장
            with tempfile.NamedTemporaryFile(mode='w+', suffix=f'.{extension}', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(file.text)
                temp_path = temp_file.name
            
            # 파서 생성
            parser = _create_language_parser(extension)
            
            # GenericLoader 생성
            loader = GenericLoader.from_filesystem(
                path=temp_path,
                parser=parser
            )
            
            # 문서 로드
            documents = loader.load()
            # 기존 메타데이터 보존하면서 GitHub 정보 추가
            for document in documents:
                document.metadata.update({
                    **file.metadata.__dict__,
                    'repo_url': file.metadata.repo_url,
                    'path': '/' + file.path.replace(f"/{file.name}", ""),
                    'filename': file.name,
                    'extension': extension
                })
                document.metadata.pop('source')
            
            documents_by_language[lang] = documents_by_language[lang] + documents
            
            # 임시 파일 삭제
            os.unlink(temp_path)
            
        except Exception as e:
            logger.error(f"문서 로드 중 오류 발생: {file['path']}, 오류: {str(e)}")
            # 오류가 발생해도 계속 진행
            continue
    for lang, documents in documents_by_language.items():
        logger.debug(f"{lang} 언어 문서 개수: {len(documents)}")
        for document in documents:
            logger.debug(f"문서 내용: {document.page_content[:100]}")
            logger.debug(f"문서 메타데이터: {document.metadata}")

    return documents_by_language