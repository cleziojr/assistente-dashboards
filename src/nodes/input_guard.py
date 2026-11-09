import re
from src.schemas import AgentState
from src.llm import llm
from langchain_core.messages import AIMessage

PADROES_ALERTA = {
    r"ignore\s+(previous|all)\s+instructions",
    r"you\s+are\s+now",
    r"new\s+persona",
    r"system\s*:",
    r"esqueça\s+(tudo|as instruções)",
    r"ignore\s+as\s+instruções"
}

TERMOS_ESCOPO = [
    "csv", "dashboard", "gráfico", "visualização", "dados",
    "coluna", "planilha", "design", "cor", "escala", "munzner",
    "streamlit", "barras", "cartão", "métrica",
]

MAXIMO_CARACTERES = 300

def verifica_prompt_invalido(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(re.search(padrao, texto_lower) for padrao in PADROES_ALERTA)

def verifica_escopo(texto: str) -> bool:
    texto_lower = texto.lower()
    return any(termo in texto_lower for termo in TERMOS_ESCOPO)

def verifica_prompt_entrada(state: AgentState) -> bool:
    ultima_msg = state["messages"][-1].content
    if isinstance(ultima_msg, list):
        ultima_msg = " ".join(bloco.get("text", "") for bloco in ultima_msg if isinstance(bloco, dict))

    if len(ultima_msg) > MAXIMO_CARACTERES:
        ultima_msg = ultima_msg[:MAXIMO_CARACTERES] + "... [mensagem truncada]"

    if verifica_prompt_invalido(ultima_msg):
        return {"is_safe": False, "messages": [AIMessage(content="Sua mensagem contém padrões não permitidos e não pode ser processada.")]}

    if verifica_escopo(ultima_msg):
        return {"is_safe": True, "messages": []}

    return {"is_safe": False, "messages": [AIMessage(content="Sou especializado em dashboards e visualização de dados. Posso ajudar com CSVs, gráficos e design visual")]}

def guardrail_entrada_node(state: AgentState) -> dict:
    return verifica_prompt_entrada(state)