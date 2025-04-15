from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from collections import defaultdict 
from src.modules.github import GitHubClient

import logging
import os
import asyncio
import traceback
import tempfile

# 환경 변수 로드
load_dotenv()

# 로깅 설정
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

# 동시성 제한을 위한 세마포어
_clone_semaphore = asyncio.Semaphore(1)

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
            logger.info(f"{lang}는 파서를 지원하지 않아 기본 파서로 처리됩니다.")
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
    

def load_documents(repo_url: str, processed_files: List[Dict[str, Any]]) -> Dict[str, List]:
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
                'file_size': len(text) if text else 0,
                'extension': ext.lstrip('.').lower() if ext else ''
            }
        }   
        
    Returns:
        파일확장자별로 LangChain Document 객체로 변환된 목록
    """
    documents_by_language = defaultdict(list)
    
    for file in processed_files:
        extension = file['metadata']['extension']
        lang = EXTENSION_LANGUAGE_MAP.get(extension, "UNKNOWN")
        
        try:
            # 임시 파일을 생성하여 텍스트 저장
            with tempfile.NamedTemporaryFile(mode='w+', suffix=f'.{extension}', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(file['text'])
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
                    **file['metadata'],
                    'repo_url': repo_url,
                    'path': '/' + file['path'].replace(f"/{file['name']}", ""),
                    'filename': file['name'],
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
    
    return documents_by_language


def main():
    """
    메인 함수 - 저장소 처리 및 결과 출력
    
    Args:
        repo_url: GitHub 저장소 URL (없으면 기본값 사용)
        file_types: 처리할 파일 확장자 목록 (없으면 모든 파일 처리)
        verbose: 상세 정보 출력 여부
    
    Returns:
        List[Dict[str, Any]]: 처리된 파일 정보 목록
    """
    # 성공/실패 통계를 위한 변수
    total_files = 0
    successful_files = 0
    
    # 로깅 레벨 설정
    log_level = logging.DEBUG
    logging.basicConfig(level=log_level, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 기본 저장소 URL 설정
    repo_url = "https://github.com/honeyuheony/git-context-mcp-forge"
    
    logger.info(f"GitHub 저장소 처리 시작: {repo_url}")
    
    try:
        # GitHub 클라이언트 생성
        client = GitHubClient()
        
        # 저장소 처리
        processed_files = client.process_repository(repo_url)

        documents_by_language = load_documents(processed_files)
    
        for lang, docs in documents_by_language.items():
            logger.info(f"\n[{lang}]")
            if docs:
                total_files += len(docs)
                successful_files += len(docs)
                logger.info(f"상태: 성공 ✓")
                logger.info(f"로드된 문서 수: {len(docs)}개")
    
        logger.info(f"\n총 처리 파일: {total_files}개, 성공: {successful_files}개")
    
        for doc_list in documents_by_language["PYTHON"]:
            for doc in doc_list:
                print(doc.metadata)
            
    except Exception as e:
        logger.error(f"오류 발생: {str(e)}")
        logger.error(f"오류 추적: {traceback.format_exc()}")


if __name__ == "__main__":
    main()

