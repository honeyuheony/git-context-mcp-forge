from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
from src.llm_workflows.state import RepositoryToVectorDBState

from src.config.log_config import Logger

logger = Logger()
DEFAULT_CHUNK_SIZE: int = 1000
DEFAULT_CHUNK_OVERLAP: int = 200
        
# 언어별 청크 크기 및 중복 설정
LANGUAGE_SPECIFIC_CHUNKS: dict = {
    # 복잡한 문법 구조를 가진 언어들
    'JAVA': {'chunk_size': 1500, 'chunk_overlap': 300},
    'CPP': {'chunk_size': 1500, 'chunk_overlap': 300},
    'CSHARP': {'chunk_size': 1500, 'chunk_overlap': 300},
    'GO': {'chunk_size': 1500, 'chunk_overlap': 300},
    'RUST': {'chunk_size': 1500, 'chunk_overlap': 300},
    
    # 스크립트 언어들
    'PYTHON': {'chunk_size': 1000, 'chunk_overlap': 200},
    'JS': {'chunk_size': 1000, 'chunk_overlap': 200},
    'TS': {'chunk_size': 1000, 'chunk_overlap': 200},
    'RUBY': {'chunk_size': 1000, 'chunk_overlap': 200},
    'PHP': {'chunk_size': 1000, 'chunk_overlap': 200},
    'PERL': {'chunk_size': 1000, 'chunk_overlap': 200},
    
    # 마크업/문서 언어들
    'HTML': {'chunk_size': 800, 'chunk_overlap': 150},
    'MARKDOWN': {'chunk_size': 800, 'chunk_overlap': 150},
    'RST': {'chunk_size': 800, 'chunk_overlap': 150},
    'LATEX': {'chunk_size': 800, 'chunk_overlap': 150},
    
    # 기타 언어들
    'PROTO': {'chunk_size': 600, 'chunk_overlap': 100}  # 프로토콜 정의도 비교적 작은 단위
}
        
# 언어별 파서 매핑
LANGUAGE_PARSERS: dict = {
    'PYTHON': Language.PYTHON,
    'JS': Language.JS,
    'TS': Language.TS,
    'JAVA': Language.JAVA,
    'CPP': Language.CPP,
    'GO': Language.GO,
    'RUBY': Language.RUBY,
    'RUST': Language.RUST,
    'PHP': Language.PHP,
    'PROTO': Language.PROTO,
    'RST': Language.RST,
    'SCALA': Language.SCALA,
    'MARKDOWN': Language.MARKDOWN,
    'LATEX': Language.LATEX,
    'HTML': Language.HTML,
    'SOL': Language.SOL,
    'CSHARP': Language.CSHARP,
    'COBOL': Language.COBOL,
    'C': Language.C,
    'LUA': Language.LUA,
    'PERL': Language.PERL, # 현재 지원 안함
    'ELIXIR': Language.ELIXIR
}


def split_documents(state: RepositoryToVectorDBState) -> RepositoryToVectorDBState:
    """
    언어별 문서를 분할합니다.
    
    Args:
        documents_by_language: 언어별 문서 목록을 담은 딕셔너리
        
    Returns:
        List: 분할된 전체 문서 목록
    """
    all_split_documents = []
    
    for language, documents in state.documents_by_language.items():

        try:
            splitter = _create_language_splitter(language)
            split_docs = splitter.split_documents(documents)
            
            logger.info(f"{language}: {len(documents)}개 문서를 {len(split_docs)}개로 분할 완료")
            all_split_documents = all_split_documents + split_docs
            
        except Exception as e:
            logger.error(f"{language} 문서 분할 중 오류 발생: {str(e)}", exc_info=True)
            continue
    
    logger.info(f"총 {len(all_split_documents)}개의 분할된 문서 생성 완료")
    state.split_documents = all_split_documents
    return state
def _get_language_specific_params(language: str) -> tuple[int, int]:
    """
    언어별 특화된 청크 크기와 중복 값을 반환합니다.
    
    Args:
        language: 프로그래밍 언어
        
    Returns:
        tuple[int, int]: (chunk_size, chunk_overlap)
    """
    if language in LANGUAGE_SPECIFIC_CHUNKS:
        params = LANGUAGE_SPECIFIC_CHUNKS[language]
        return params['chunk_size'], params['chunk_overlap']
    return DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

def _create_language_splitter(language: str) -> RecursiveCharacterTextSplitter:
    """
    언어별 TextSplitter를 생성합니다.
    
    Args:
        language: 프로그래밍 언어
        
    Returns:
        RecursiveCharacterTextSplitter: 해당 언어에 맞는 텍스트 분할기
    """
    try:
        chunk_size, chunk_overlap = _get_language_specific_params(language)
        
        if language in LANGUAGE_PARSERS:
            logger.info(f"{language} 언어용 분할기 생성 (chunk_size: {chunk_size}, overlap: {chunk_overlap})")
            return RecursiveCharacterTextSplitter.from_language(
                language=LANGUAGE_PARSERS[language],
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            logger.warning(f"{language}는 지원되지 않는 언어입니다. 기본 분할기를 사용합니다.")
            return RecursiveCharacterTextSplitter(
                chunk_size=DEFAULT_CHUNK_SIZE,
                chunk_overlap=DEFAULT_CHUNK_OVERLAP
            )
    except Exception as e:
        logger.error(f"{language} 분할기 생성 중 오류 발생: {str(e)}")
        return RecursiveCharacterTextSplitter(
            chunk_size=DEFAULT_CHUNK_SIZE,
            chunk_overlap=DEFAULT_CHUNK_OVERLAP
        )