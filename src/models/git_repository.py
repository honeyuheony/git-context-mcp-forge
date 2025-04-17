from typing import Annotated

from pydantic import BaseModel, Field


class RepositoryInfo(BaseModel):
    """저장소 정보"""
    repo_url: Annotated[str, Field(description="저장소 URL")]
    owner: Annotated[str, Field(default="", description="저장소 소유자")]
    repo_name: Annotated[str, Field(default="", description="저장소 이름")]
    branch: Annotated[str, Field(default="", description="브랜치 이름")]


class CodeMetadata(BaseModel):
    """코드 메타데이터"""

    repo_url: Annotated[str, Field(description="저장소 URL")]
    path: Annotated[str, Field(default="", description="파일 경로")]
    filename: Annotated[str, Field(default="", description="파일 이름")]
    extension: Annotated[str, Field(default="", description="파일 확장자")]
    file_size: Annotated[int, Field(default=0, description="파일 크기")]


class ParsedCode(BaseModel):
    """GitHub 저장소에서 파싱한 코드 문서"""

    path: Annotated[str, Field(description="파일 경로")]
    name: Annotated[str, Field(description="파일 이름")]
    type: Annotated[str, Field(description="파일 타입")]
    text: Annotated[str, Field(description="파일 내용")]
    metadata: Annotated[CodeMetadata, Field(description="파일 메타데이터")]
