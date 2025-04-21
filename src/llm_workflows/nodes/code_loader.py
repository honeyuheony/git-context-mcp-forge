from src.llm_workflows.state import RepositoryToVectorDBState
from src.utils.git_repository_utils import GitHubRepositoryUtils
from src.models.git_repository import ParsedCode
from src.config.log_config import Logger
from src.llm_workflows.adapters.blob import GitHubBlobLoader
from src.llm_workflows.adapters.parser import MultiLanguageParser
from typing import List, Dict, Any, Optional
from collections import defaultdict
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser

logger = Logger()

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
    

def load_documents(processed_files: List[ParsedCode]) -> Dict[str, List]:
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

    try:
        blob_loader = GitHubBlobLoader(processed_files)
        parser = MultiLanguageParser()
        loader = GenericLoader(
            blob_loader=blob_loader,
            blob_parser=parser
        )
        documents = loader.load()
        logger.debug(f"총 문서 개수: {len(documents)}")

        for document in documents:
            extension = document.metadata.get("extension")
            lang = EXTENSION_LANGUAGE_MAP.get(extension, "UNKNOWN")
            documents_by_language[lang].append(document)
        
        for lang, documents in documents_by_language.items():
            logger.debug(f"{lang} 언어 문서 개수: {len(documents)}")
            for document in documents:
                logger.debug(f"문서 내용: {document.page_content[:100]}")
                logger.debug(f"문서 메타데이터: {document.metadata}")

    except Exception as e:
        logger.error(f"문서 로드 중 오류 발생: {str(e)}")
        
    return documents_by_language