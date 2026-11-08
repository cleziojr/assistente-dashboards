from src.schemas import AgentState
from src.rag.retriever import retriever

def _extrair_texto(mensagem) -> str:
    """Extrai string limpa mesmo quando o modelo retorna lista de blocos."""
    if hasattr(mensagem, "text") and mensagem.text:
        return mensagem.text
    if isinstance(mensagem.content, str):
        return mensagem.content
    if isinstance(mensagem.content, list):
        return "\n".join(
            bloco.get("text", "") for bloco in mensagem.content if isinstance(bloco, dict)
        )
    return str(mensagem.content)

def agentic_rag_node(state: AgentState) -> dict:
    """Executa a busca vetorial no livro da Munzner e acumula em rag_context."""
    ultima_msg = _extrair_texto(state["messages"][-1])

    # Se já havia finalizado um RAG em um turno anterior da conversa, reseta contadores
    if state.get("rag_is_complete", False):
        tentativa_atual = 1
        contexto_anterior = ""
        query = state.get("search_query") or ultima_msg
    else:
        tentativa_atual = state.get("rag_attempts", 0) + 1
        contexto_anterior = state.get("rag_context", "")
        query = state.get("search_query") or ultima_msg

    print(f"\n🔍 [rag_search | Tentativa {tentativa_atual}] Buscando por: '{query}'")
    docs = retriever.invoke(query)

    trechos_formatados = "\n\n".join(
        f"[Fonte: Tamara Munzner, Pág. {d.metadata.get('page', '?')}] {d.page_content}"
        for d in docs
    )

    novo_contexto = (
        f"{contexto_anterior}\n\n--- Resultados para '{query}' ---\n{trechos_formatados}"
        if contexto_anterior
        else f"--- Resultados para '{query}' ---\n{trechos_formatados}"
    )

    return {
        "rag_context": novo_contexto,
        "rag_attempts": tentativa_atual,
        "rag_is_complete": False,
    }