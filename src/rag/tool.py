from langchain_core.tools import tool
from src.rag.retriever import retriever
from src.llm import llm
from src.prompts.rag_evaluator import PROMPT_AVALIACAO
from src.schemas import AvaliacaoRAG

MAX_TENTATIVAS = 3

avaliador = PROMPT_AVALIACAO | llm.with_structured_output(AvaliacaoRAG)


@tool
def consultar_livro_visualizacao(query: str) -> str:
    """Consulta o livro 'Visualization Analysis and Design' de Tamara Munzner.
    Use quando precisar de orientações teóricas sobre tipos de gráficos, codificação visual,
    princípios de design ou escolha de marcas e canais visuais.
    Realiza até 3 tentativas refinando a busca automaticamente se o contexto for insuficiente."""

    contexto = ""
    query_atual = query

    for tentativa in range(1, MAX_TENTATIVAS + 1):
        docs = retriever.invoke(query_atual)
        trechos = "\n\n".join(
            f"[Pág. {d.metadata.get('page', '?')}] {d.page_content}"
            for d in docs
        )
        contexto = f"{contexto}\n\n--- Busca {tentativa}: '{query_atual}' ---\n{trechos}" if contexto else f"--- Busca {tentativa}: '{query_atual}' ---\n{trechos}"

        if tentativa == MAX_TENTATIVAS:
            break

        avaliacao: AvaliacaoRAG = avaliador.invoke({"question": query, "context": contexto})

        if avaliacao.status == "completo":
            break

        query_atual = avaliacao.nova_query_ingles

    return contexto
