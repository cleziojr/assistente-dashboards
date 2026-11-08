from typing import Literal

from src.schemas import AgentState, AvaliacaoRAG
from src.nodes.rag_search import _extrair_texto
from src.llm import llm
from src.prompts.rag_evaluator import PROMPT_AVALIACAO


avaliador = PROMPT_AVALIACAO | llm.with_structured_output(AvaliacaoRAG)

def evaluate_rag_node(state: AgentState) -> dict:
    """Avalia se o rag_context basta ou se precisa reformular a query e rodar em loop."""
    pergunta_original = _extrair_texto(state["messages"][-1])
    contexto_atual = state.get("rag_context", "")
    tentativas = state.get("rag_attempts", 0)

    resultado: AvaliacaoRAG = avaliador.invoke({
        "question": pergunta_original,
        "context": contexto_atual,
    })

    print(f"⚖️ [rag_evaluator] Status: {resultado.status.upper()} | Motivo: {resultado.justificativa}")

    if resultado.status == "incompleto" and tentativas < 3:
        print(f"🔄 [rag_evaluator] Reformulando query para: '{resultado.nova_query_ingles}'")
        return {
            "rag_is_complete": False,
            "search_query": resultado.nova_query_ingles,
        }

    return {"rag_is_complete": True, "search_query": ""}

def roteador_rag(state: AgentState) -> Literal["rag_search", "assistant"]:
    """Aresta condicional: decide se volta para rag_search ou devolve para o assistant."""
    if not state.get("rag_is_complete", False) and state.get("rag_attempts", 0) < 3:
        return "rag_search"
    return "assistant"