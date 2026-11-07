import warnings
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from src.schemas import AgentState

warnings.filterwarnings("ignore", category=SyntaxWarning, module="google.genai")
load_dotenv()

# Caminho seguro para a raiz do projeto (independente de onde o scrip   t for chamado)
BASE_DIR = Path(__file__).resolve().parents[2]
PERSIST_DIR = str(BASE_DIR / "chroma_munzner")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vector_store = Chroma(
    collection_name="munzner_vis_design",
    embedding_function=embeddings,
    persist_directory=PERSIST_DIR,
)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})

llm = init_chat_model("google_genai:gemini-3.5-flash-lite")


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


def agetic_rag_node(state: AgentState) -> dict:
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


def evaluate_rag_node(state: AgentState) -> dict:
    """Avalia se o rag_context basta ou se precisa reformular a query e rodar em loop."""
    pergunta_original = _extrair_texto(state["messages"][-1])
    contexto_atual = state.get("rag_context", "")
    tentativas = state.get("rag_attempts", 0)

    prompt_avaliacao = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um avaliador de recuperação de informação (RAG Evaluator).\n"
         "Analise a pergunta original do usuário e o contexto já recuperado do livro 'Visualization Analysis and Design' (Tamara Munzner).\n"
         "Se o contexto ainda não trouxer regras específicas suficientes ou se faltar algum dos itens pedidos na comparação, "
         "marque como 'incompleto' e gere uma nova query em inglês focada especificamente no que faltou."),
        ("human", "Pergunta do usuário: {question}\n\nContexto recuperado até agora:\n{context}")
    ])

    avaliador = prompt_avaliacao | llm.with_structured_output(AvaliacaoRAG)
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