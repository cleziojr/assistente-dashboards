from typing import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    rag_context: str
    active_skills: list[str]
    rag_attempts: int
    is_safe: bool
    search_query: str      # Query atual (permite reescrita pelo avaliador no loop)
    rag_is_complete: bool  # Flag de controle do avaliador do RAG


def init_graph_state() -> AgentState:
    """Inicializa o estado do grafo conforme especificado no PDF."""
    return {
        "messages": [],
        "rag_context": "",
        "active_skills": [],
        "rag_attempts": 0,
        "is_safe": True,
        "search_query": "",
        "rag_is_complete": False,
    }