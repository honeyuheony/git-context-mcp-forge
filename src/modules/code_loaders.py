from langchain_text_splitters import Language
from langchain_community.document_loaders.generic import GenericLoader
from langchain_community.document_loaders.parsers import LanguageParser
from typing import Dict, List, Optional
import os
import chardet
from glob import glob
import traceback
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,  # ✅ MCP 안전하게 처리
    format='%(asctime)s [%(levelname)s] %(message)s',
    # handlers=[
    #     logging.StreamHandler(sys.stdout)
    # ]
)
logger = logging.getLogger(__name__)

class MultiLanguageDocumentLoader:
    def __init__(self, root_path: str):
        """
        여러 프로그래밍 언어의 문서를 로드하는 클래스를 초기화합니다.
        
        Args:
            root_path: 문서를 검색할 루트 디렉토리 경로
        """
        self.root_path = root_path
        self.logger = logger
        self.logger = logger
        # 기본 인코딩 후보 목록
        self.encoding_candidates = ['utf-8', 'cp949', 'euc-kr', 'ascii']
        
        # 언어별 파일 확장자 매핑
        self.language_extensions = {
            'PYTHON': ['.py'],
            'JS': ['.js', '.jsx', '.mjs'],
            'TS': ['.ts', '.tsx'],
            'JAVA': ['.java'],
            'CPP': ['.cpp', '.hpp', '.cc', '.h', '.cxx', '.hxx'],
            'GO': ['.go'],
            'RUBY': ['.rb', '.rake', '.gemspec'],
            'RUST': ['.rs'],
            'PHP': ['.php'],
            'PROTO': ['.proto'],
            'RST': ['.rst'],
            'SCALA': ['.scala'],
            'MARKDOWN': ['.md', '.markdown'],
            'LATEX': ['.tex'],
            'HTML': ['.html', '.htm'],
            'SOL': ['.sol'],
            'CSHARP': ['.cs'],
            'COBOL': ['.cob', '.cbl'],
            'C': ['.c', '.h'],
            'LUA': ['.lua'],
            'PERL': ['.pl', '.pm'],
            'ELIXIR': ['.ex', '.exs']
        }

    def _detect_file_encoding(self, file_path: str) -> str:
        """
        파일의 인코딩을 감지합니다.
        
        Args:
            file_path: 인코딩을 감지할 파일 경로
            
        Returns:
            감지된 인코딩 또는 기본값으로 'utf-8'
        """
        try:
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                if raw_data.startswith(b'\xff\xfe') or raw_data.startswith(b'\xfe\xff'):
                    return 'utf-16'
                result = chardet.detect(raw_data)
                if result['confidence'] > 0.7:
                    return result['encoding']
        except Exception as e:
            self.logger.warning(
                f"인코딩 감지 중 오류 발생 ({file_path})\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
        return 'utf-8'

    def _load_file_with_encoding(self, file_path: str) -> Optional[str]:
        """
        다양한 인코딩을 시도하여 파일을 로드합니다.
        
        Args:
            file_path: 로드할 파일 경로
            
        Returns:
            로드된 파일 내용 또는 None
        """
        # 먼저 감지된 인코딩으로 시도
        detected_encoding = self._detect_file_encoding(file_path)
        encodings_to_try = [detected_encoding] + [enc for enc in self.encoding_candidates if enc != detected_encoding]
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                self.logger.info(f"성공: {file_path} 파일을 {encoding} 인코딩으로 로드했습니다.")
                return content
            except UnicodeDecodeError:
                self.logger.debug(f"{encoding} 인코딩으로 {file_path} 로드 시도 실패")
                continue
            except Exception as e:
                self.logger.warning(
                    f"{encoding} 인코딩으로 {file_path} 로드 중 오류 발생\n"
                    f"Error: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                continue
        return None

    def _create_language_parser(self, lang_enum: Language) -> Optional[LanguageParser]:
        """
        언어별 파서를 생성합니다. 파서가 지원되지 않는 경우 None을 반환합니다.
        
        Args:
            lang_enum: 언어 Enum
            
        Returns:
            LanguageParser 객체 또는 None
        """
        try:
            # 파서가 지원되는 언어와 해당 값 매핑
            SUPPORTED_PARSER_LANGUAGES = {
                'C': 'c',
                'CPP': 'cpp',
                'CSHARP': 'csharp',
                'COBOL': 'cobol',
                'ELIXIR': 'elixir',
                'GO': 'go',
                'JAVA': 'java',
                'JS': 'js',
                'KOTLIN': 'kotlin',
                'LUA': 'lua',
                'PERL': 'perl',
                'PYTHON': 'python',
                'RUBY': 'ruby',
                'RUST': 'rust',
                'SCALA': 'scala',
                'TS': 'ts'
            }
            
            if lang_enum.name not in SUPPORTED_PARSER_LANGUAGES:
                self.logger.info(f"{lang_enum.name}는 파서를 지원하지 않아 기본 파서로 처리됩니다.")
                return LanguageParser()
                
            parser_value = SUPPORTED_PARSER_LANGUAGES[lang_enum.name]
            return LanguageParser(language=parser_value)
        except Exception as e:
            self.logger.error(
                f"{lang_enum.name} 파서 생성 중 오류 발생\n"
                f"Error: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            return None

    def load_documents(self, languages: Optional[List[str]] = None) -> Dict[str, List]:
        """
        지정된 언어들의 문서를 로드합니다.
        
        Args:
            languages: 로드할 언어 목록. None인 경우 모든 지원 언어를 로드합니다.
            
        Returns:
            언어별 문서 목록을 담은 딕셔너리
        """
        if languages is None:
            languages = list(self.language_extensions.keys())
        
        documents_by_language = {}
        
        for lang in languages:
            lang = lang.upper()
            if lang not in self.language_extensions:
                self.logger.warning(f"{lang}는 지원되지 않는 언어입니다.")
                continue
                
            try:
                # 해당 언어의 Language enum 가져오기
                lang_enum = getattr(Language, lang)
                extensions = self.language_extensions[lang]
                
                documents = []
                for ext in extensions:
                    # 해당 확장자를 가진 모든 파일 경로 찾기
                    file_pattern = os.path.join(self.root_path, f"**/*{ext}")
                    matching_files = glob(file_pattern, recursive=True)
                    
                    for file_path in matching_files:
                        try:
                            # 파일별로 적절한 인코딩 감지 및 로드
                            content = self._load_file_with_encoding(file_path)
                            if content is None:
                                self.logger.warning(f"{file_path} 파일을 로드할 수 없습니다.")
                                continue
                            
                            # 언어별 파서 생성
                            parser = self._create_language_parser(lang_enum)
                            
                            loader = GenericLoader.from_filesystem(
                                path=os.path.dirname(file_path),
                                glob=os.path.basename(file_path),
                                suffixes=[ext],
                                parser=parser
                            )
                            
                            try:
                                loaded_docs = loader.load()
                                documents.extend(loaded_docs)
                                self.logger.info(f"{lang} {ext} 파일 로드 완료: {file_path}")
                            except UnicodeDecodeError as e:
                                self.logger.error(
                                    f"{file_path} 파일 인코딩 문제 발생\n"
                                    f"Error: {str(e)}\n"
                                    f"Traceback:\n{traceback.format_exc()}"
                                )
                                continue
                            except Exception as e:
                                self.logger.error(
                                    f"{file_path} 파일 로드 중 오류 발생\n"
                                    f"Error: {str(e)}\n"
                                    f"Traceback:\n{traceback.format_exc()}"
                                )
                                continue
                                
                        except Exception as e:
                            self.logger.error(
                                f"파일 처리 중 오류 발생 {file_path}\n"
                                f"Error: {str(e)}\n"
                                f"Traceback:\n{traceback.format_exc()}"
                            )
                            continue
                    
                if documents:
                    documents_by_language[lang] = documents
                    self.logger.info(f"{lang}: 총 {len(documents)}개 문서 로드 완료")
                    
            except Exception as e:
                self.logger.error(
                    f"{lang} 처리 중 오류 발생\n"
                    f"Error: {str(e)}\n"
                    f"Traceback:\n{traceback.format_exc()}"
                )
                continue
        
        return documents_by_language

    def get_supported_languages(self) -> Dict[str, List[str]]:
        """
        지원되는 언어 목록과 각 언어의 파일 확장자를 반환합니다.
        
        Returns:
            Dict[str, List[str]]: 언어별 지원되는 파일 확장자 목록
        """
        return self.language_extensions

def main():
    # 로깅 레벨 설정
    logger.setLevel(logging.INFO)
    
    # test_code 디렉토리 경로 설정
    test_dir = os.path.join(os.getcwd(), 'test_code')
    loader = MultiLanguageDocumentLoader(test_dir)
    
    logger.info("\n지원되는 언어 목록 및 파일 확장자:")
    logger.info("==============================")
    for lang, extensions in loader.get_supported_languages().items():
        logger.info(f"- {lang}: {', '.join(extensions)}")
    
    logger.info("\n각 언어별 테스트 파일 로드 시작...")
    logger.info("==============================")
    
    # 모든 언어에 대해 테스트 실행
    documents = loader.load_documents()
    
    # 결과 출력
    logger.info("\n테스트 결과:")
    logger.info("===============")
    
    total_files = 0
    successful_files = 0
    failed_languages = []
    
    for lang, docs in documents.items():
        logger.info(f"\n[{lang}]")
        if docs:
            total_files += len(docs)
            successful_files += len(docs)
            logger.info(f"상태: 성공 ✓")
            logger.info(f"로드된 문서 수: {len(docs)}개")
            logger.info(f"첫 번째 문서 미리보기 (200자):")
            logger.info("-" * 40)
            logger.info(docs[0].page_content[:200] + "..." if len(docs[0].page_content) > 200 else docs[0].page_content)
            logger.info("-" * 40)
        else:
            failed_languages.append(lang)
            logger.warning(f"상태: 실패 ✗")
            logger.warning("문서를 로드하지 못했습니다.")
    
    # 최종 통계 출력
    logger.info("\n최종 테스트 결과 통계:")
    logger.info("=====================")
    logger.info(f"총 지원 언어 수: {len(loader.get_supported_languages())}")
    logger.info(f"성공한 언어 수: {len(loader.get_supported_languages()) - len(failed_languages)}")
    logger.info(f"실패한 언어 수: {len(failed_languages)}")
    if failed_languages:
        logger.warning(f"실패한 언어 목록: {', '.join(failed_languages)}")
    logger.info(f"총 처리된 파일 수: {total_files}")
    logger.info(f"성공적으로 로드된 파일 수: {successful_files}")
    
    success_rate = (len(loader.get_supported_languages()) - len(failed_languages)) / len(loader.get_supported_languages()) * 100
    logger.info(f"\n테스트 성공률: {success_rate:.1f}%")

# if __name__ == "__main__":
#     main()