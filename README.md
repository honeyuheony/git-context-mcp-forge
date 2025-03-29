# GIT-CONTEXT-MCP-FORGE

이 프로젝트는 GitHub 저장소의 소스코드를 기반으로 MCP(Model Context Protocol) 에이전트를 구축하는 예제입니다. LangChain을 활용하여 소스코드를 분석하고 이를 기반으로 지식베이스를 구축하여 LLM이 코드베이스를 이해하고 활용할 수 있도록 합니다.

## 주요 기능

다음과 같은 기능을 MCP Server 의 형태로 제공합니다.

1. **소스코드 기반 RAG 구축 (repo_to_rag)**
   - GitHub 저장소의 소스코드를 분석하여 각 언어별 적절한 도구를 통해 Documents 객체 생성
   - 생성된 문서를 기반으로 벡터 데이터베이스 구축

2. **RAG 기반 코드베이스 컨텍스트 제공 (rag_to_context)**
   - 소스코드를 벡터화하여 검색 가능한 지식베이스 구축
   - 코드베이스에 대한 질의응답 기능 제공


## 프로젝트 구조

```
.
├── mcp_server.py         # MCP 서버 구현
├── auto_mcp_json.py      # MCP JSON 자동 생성
├── mcp_config.json       # MCP 설정 파일
├── agent/               # 에이전트 관련 코드
├── modules/             # RAG 구성성 모듈
├── requirements.txt     # Python 패키지 의존성
├── pyproject.toml      # Poetry 프로젝트 설정
├── dockerfile          # Docker 이미지 빌드 설정
├── docker-compose.yml  # Docker 컨테이너 구성
└── .env.example        # 환경 변수 예제
```

## 서버 실행
### venv

```bash
# 저장소 클론
git clone https://github.com/yourusername/github-mcp-agent.git
cd github-mcp-agent

python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 등 설정
```
### poetry

```bash
poetry shell
poetry install
```

### Docker

```bash
docker-compose up --build
```

## 환경 변수

`.env` 파일에 다음 환경 변수를 설정하세요:

- `OPENAI_API_KEY`: OpenAI API 키
- `GITHUB_TOKEN`: GitHub API 토큰 (선택 사항, 비공개 저장소 접근 시 필요)

## 사용 방법

### 1. JSON 파일 생성

각 예제 디렉토리에서 다음 명령을 실행하여 필요한 JSON 파일을 생성합니다:

```bash
# JSON 파일 생성
python auto_mcp_json.py
```

### 2. Claude Desktop/Cursor에 MCP 등록

1. Claude Desktop 또는 Cursor 실행
2. MCP 설정 메뉴 열기
3. 생성된 JSON 내용을 복사하여 붙여넣기
4. 저장 및 `재시작` (윈도우 유저의 경우 작업관리자로 프로세스를 완전히 종료하고 재시작 해주시는 걸 권장합니다.)

> **참고**: Claude Desktop 또는 Cursor를 실행하면 MCP 서버가 자동으로 함께 실행되며, 소프트웨어를 종료하면 MCP 서버도 함께 종료됩니다.

### 3. MCP Tool 호출
MCP Client (Cursor AI or Claude Desktop) 에서 다음과 같은 방식으로 사용 가능합니다.
> **예제**:
>
> MCP Tool 을 사용하기 전에, MCP 서버가 실행 중이어야 합니다.
> Cursor AI 또는 Claude Desktop 에서 MCP 서버 URL 을 정확하게 설정해야 합니다.
> 
> 1. 코드베이스를 RAG 에 저장
> "https://github.com/langchain-ai/langchain" 저장소를 분석하여 RAG 에 저장해줘."
> 
> 2. 코드베이스를 이해하고 질의응답
> "langchain 에서 제공하는 문서를 찾아줘."

## 라이센스

MIT 라이센스