from langchain_community.document_loaders.parsers import LanguageParser
from langchain_core.documents import Document
from langchain_core.document_loaders import Blob
from typing import Iterator

class MultiLanguageParser(LanguageParser):
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

    def __init__(self):
        super().__init__()

    def lazy_parse(self, blob: Blob) -> Iterator[Document]:
        extension = blob.metadata.get("extension")
        self.language = self.SUPPORTED_PARSER_LANGUAGES.get(extension)
        documents = super().lazy_parse(blob)
        
        # 기존 메타데이터 보존하면서 GitHub 정보 추가
        for document in documents:
            document.metadata.update({
                **document.metadata,
                **blob.metadata,
            })
            document.metadata.pop('source')
            yield document