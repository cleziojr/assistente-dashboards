import sys
from pathlib import Path

# Garante que a pasta raiz do projeto está no PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parents[1]))

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

from src.schemas import AgentState, init_graph_state
from src.rag.agentic_rag import (
    agetic_rag_node,
    evaluate_rag_node,
    roteador_rag,
    llm,
    _extrair_texto,
)


def assistant_mock_node(state: AgentState) -> dict:
    """Simula o nó assistant gerando a resposta final baseada no rag_context."""
    pergunta = _extrair_texto(state["messages"][-1])
    contexto = state.get("rag_context", "")

    prompt_final = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um assistente especialista em visualização de dados baseado na obra de Tamara Munzner.\n"
         "Responda à pergunta do usuário em português utilizando APENAS o contexto abaixo.\n"
         "Sempre cite as páginas de onde tirou cada recomendação no formato (Munzner, pág. X)."),
        ("human", "Contexto:\n{context}\n\nPergunta: {question}")
    ])

    resposta = (prompt_final | llm).invoke({"context": contexto, "question": pergunta})
    return {"messages": [resposta]}


def montar_grafo_teste():
    workflow = StateGraph(AgentState)
    workflow.add_node("rag_search", agetic_rag_node)
    workflow.add_node("rag_evaluator", evaluate_rag_node)
    workflow.add_node("assistant", assistant_mock_node)

    workflow.add_edge(START, "rag_search")
    workflow.add_edge("rag_search", "rag_evaluator")
    workflow.add_conditional_edges(
        "rag_evaluator",
        roteador_rag,
        {"rag_search": "rag_search", "assistant": "assistant"},
    )
    workflow.add_edge("assistant", END)
    return workflow.compile()


if __name__ == "__main__":
    app = montar_grafo_teste()

    casos_de_teste = [
        {
            "id": "Caso de Teste 03 - RAG Básico",
            "pergunta": "Quais são as melhores práticas para escolher cores em um dashboard, segundo o guia?",
            "query_inicial": "",  # Deixa vazio para testar a busca direta + tradução automática se precisar
        },
        {
            "id": "Caso de Teste 08 - (Desafiador) RAG Agêntico Iterativo",
            "pergunta": "Compare as regras de gráficos de dispersão e gráficos de pizza do documento.",
            "query_inicial": "scatterplots rules point marks",  # Simula busca inicial parcial para forçar o loop
        },
    ]

    for teste in casos_de_teste:
        print("\n" + "=" * 80)
        print(f"🚀 EXECUTANDO: {teste['id']}")
        print(f"💬 Entrada: \"{teste['pergunta']}\"")
        print("=" * 80)

        estado = init_graph_state()
        estado["messages"] = [HumanMessage(content=teste["pergunta"])]
        estado["search_query"] = teste["query_inicial"]

        resultado = app.invoke(estado)
        resposta_limpa = _extrair_texto(resultado["messages"][-1])

        print(f"\n✅ RESPOSTA FINAL ({teste['id']} | Tentativas de RAG: {resultado['rag_attempts']}):\n")
        print(resposta_limpa)
        print("\n" + "-" * 80)