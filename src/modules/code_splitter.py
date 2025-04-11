from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    Language
)
from typing import Dict, List
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # ✅ MCP 안전하게 처리,
    format='%(asctime)s [%(levelname)s] %(message)s',
    # handlers=[
    #     logging.StreamHandler(sys.stdout)
    # ]
)
logger = logging.getLogger(__name__)

class MultiLanguageDocumentSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        여러 프로그래밍 언어의 문서를 분할하는 클래스를 초기화합니다.
        
        Args:
            chunk_size: 분할할 청크의 크기 (기본값: 1000)
            chunk_overlap: 청크 간 중복 크기 (기본값: 200)
        """
        self.default_chunk_size = chunk_size
        self.default_chunk_overlap = chunk_overlap
        self.logger = logger
        
        # 언어별 청크 크기 및 중복 설정
        self.language_specific_chunks = {
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
        self.language_parsers = {
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

    def _get_language_specific_params(self, language: str) -> tuple[int, int]:
        """
        언어별 특화된 청크 크기와 중복 값을 반환합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            tuple[int, int]: (chunk_size, chunk_overlap)
        """
        if language in self.language_specific_chunks:
            params = self.language_specific_chunks[language]
            return params['chunk_size'], params['chunk_overlap']
        return self.default_chunk_size, self.default_chunk_overlap

    def _create_language_splitter(self, language: str) -> RecursiveCharacterTextSplitter:
        """
        언어별 TextSplitter를 생성합니다.
        
        Args:
            language: 프로그래밍 언어
            
        Returns:
            RecursiveCharacterTextSplitter: 해당 언어에 맞는 텍스트 분할기
        """
        try:
            chunk_size, chunk_overlap = self._get_language_specific_params(language)
            
            if language in self.language_parsers:
                self.logger.info(f"{language} 언어용 분할기 생성 (chunk_size: {chunk_size}, overlap: {chunk_overlap})")
                return RecursiveCharacterTextSplitter.from_language(
                    language=self.language_parsers[language],
                    chunk_size=chunk_size,
                    chunk_overlap=chunk_overlap
                )
            else:
                self.logger.warning(f"{language}는 지원되지 않는 언어입니다. 기본 분할기를 사용합니다.")
                return RecursiveCharacterTextSplitter(
                    chunk_size=self.default_chunk_size,
                    chunk_overlap=self.default_chunk_overlap
                )
        except Exception as e:
            self.logger.error(f"{language} 분할기 생성 중 오류 발생: {str(e)}")
            return RecursiveCharacterTextSplitter(
                chunk_size=self.default_chunk_size,
                chunk_overlap=self.default_chunk_overlap
            )

    def split_documents(self, documents_by_language: Dict[str, List]) -> List:
        """
        언어별 문서를 분할합니다.
        
        Args:
            documents_by_language: 언어별 문서 목록을 담은 딕셔너리
            
        Returns:
            List: 분할된 전체 문서 목록
        """
        all_split_documents = []
        
        for language, documents in documents_by_language.items():
            try:
                splitter = self._create_language_splitter(language)
                split_docs = splitter.split_documents(documents)
                
                self.logger.info(f"{language}: {len(documents)}개 문서를 {len(split_docs)}개로 분할 완료")
                all_split_documents.extend(split_docs)
                
            except Exception as e:
                self.logger.error(f"{language} 문서 분할 중 오류 발생: {str(e)}")
                continue
        
        self.logger.info(f"총 {len(all_split_documents)}개의 분할된 문서 생성 완료")
        return all_split_documents

def main():
    # 예시 사용법
    from code_loaders import MultiLanguageDocumentLoader
    import os
    
    # test_code 디렉토리 경로 설정
    test_dir = os.path.join(os.getcwd(), 'test_code')
    
    # 문서 로더 초기화 및 로드
    loader = MultiLanguageDocumentLoader(test_dir)
    documents = loader.load_documents()
    
    # 문서 분할기 초기화 및 분할
    splitter = MultiLanguageDocumentSplitter(chunk_size=1000, chunk_overlap=200)
    split_documents = splitter.split_documents(documents)
    
    # 결과 출력
    logger.info("\n분할 결과:")
    logger.info("==========")
    logger.info(f"총 분할된 문서 수: {len(split_documents)}")
    
    if split_documents:
        logger.info("\n첫 번째 분할 문서 미리보기:")
        logger.info("-" * 40)
        logger.info(split_documents[0].page_content[:200] + "..." if len(split_documents[0].page_content) > 200 else split_documents[0].page_content)
        logger.info("-" * 40)

# if __name__ == "__main__":
#     main()