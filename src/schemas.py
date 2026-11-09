from typing import Annotated, TypedDict, Literal
from pydantic import BaseModel, Field

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
    skill_catalog: str


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
        "skill_catalog": "",
    }

class AvaliacaoRAG(BaseModel):
    status: Literal["completo", "incompleto"] = Field(
        description="Retorne 'completo' se o contexto já permite responder toda a pergunta do usuário, ou 'incompleto' se faltar alguma parte."
    )
    justificativa: str = Field(
        description="Breve explicação do que já foi encontrado e do que ainda falta."
    )
    nova_query_ingles: str = Field(
        description="Se 'incompleto', escreva uma nova query de busca em inglês (ex: 'color palettes luminance saturation rules') focada APENAS no que faltou."
    )