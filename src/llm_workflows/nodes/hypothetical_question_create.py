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

    question_prompt = ChatPromptTemplate.from_template(
        """
    다음 코드를 분석하고, 이 코드에 대해 다른 개발자들이 물어볼 만한 3개의 질문을 생성해주세요.
    질문은 코드의 구현 방식, 설계 패턴, 최적화 방법, 오류 가능성 등에 초점을 맞춰주세요.

    코드:
    ```{language}
    {code}
    ```
    """
    )

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
