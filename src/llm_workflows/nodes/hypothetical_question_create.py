from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers.openai_functions import JsonKeyOutputFunctionsParser
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from src.llm_workflows.state import RepositoryToVectorDBState
from src.config.log_config import Logger

logger = Logger()

def hypothetical_question_create(state: RepositoryToVectorDBState):

    from typing import List, Dict

    functions = [
        {
            "name": "hypothetical_questions",
            "description": "Generate hypothetical questions for a given code snippet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "questions": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A hypothetical question about the code."
                        },
                        "description": "List of hypothetical questions."
                    }
                },
                "required": ["questions"],
            },
        }
    ]

    question_prompt = ChatPromptTemplate.from_template("""
        당신은 코드 분석 전문가입니다. 주어진 코드를 분석하고, 개발자들이 이 코드에 대해 물어볼 만한 다양한 질문을 생성해주세요.
        
        코드:
        ```{language}
        {code}
        ```
        
        다음과 같은 다양한 카테고리의 질문을 5-8개 생성해주세요:
        1. 구현방식: 코드가 어떻게 구현되었는지에 대한 질문
        2. 설계패턴: 코드에 사용된 설계 패턴이나 아키텍처에 대한 질문
        3. 최적화: 성능 최적화나 효율성에 대한 질문
        4. 버그가능성: 잠재적인 버그나 오류 가능성에 대한 질문
        5. 사용법: 코드를 어떻게 사용하는지에 대한 질문
        6. 기능설명: 코드가 어떤 기능을 수행하는지에 대한 질문
        """)

    hypothetical_query_chain = (
        {
            "language": lambda x: x.metadata.get("language"),
            "code": lambda x: x.page_content,
        }
        | question_prompt
        | ChatOpenAI(max_retries=0, model="gpt-4o-mini").bind(
            functions=functions, function_call={"name": "hypothetical_questions"}
        )
        | JsonKeyOutputFunctionsParser(key_name="questions")
    )

    hypothetical_questions: List[List[str]] = hypothetical_query_chain.batch(
        state.split_documents, config={"configurable": {"max_concurrency": 10}}
    )

    hypothetical_questions_docs: List[Document] = []
    for i, doc in enumerate(state.split_documents):
        path = doc.metadata.get("path")
        if path:
            for question in hypothetical_questions[i]:
                hypothetical_questions_docs.append(Document(page_content=question, metadata=doc.metadata))
        else:
            logger.warning(f"Document at index {i} has no path in metadata.")

    state.hypothetical_questions = hypothetical_questions_docs

    logger.debug(f"Generated hypothetical questions: {hypothetical_questions_docs}")

    return state
