import re
from langchain_core.messages import AIMessage
from src.schemas import AgentState

PADROES_NAO_PERMITIDOS = [
    r"C:\\Windows",
    r"/etc/passwd",
    r"/proc/",
    r"\.env",
    r"password\s*=",
    r"secret\s*=",
    r"api[_\s]?key\s*="
]

PADROES_RESPOSTA_FORA_DOMINIO = [
    "não sou capaz de ajudar com isso",
    "como modelo de linguagem",
    "não tenho acesso à internet"
]

def verifica_vazamento_informacao(texto: str) -> bool:
    return any(re.search(padrao_nao_permitido, texto, re.IGNORECASE) for padrao_nao_permitido in PADROES_NAO_PERMITIDOS)

def verifica_mencao_intencao_fora_dominio(texto: str) -> bool:
    texto_minusculo = texto.lower()
    return any(padrao_resposta_fora_dominio in texto_minusculo for padrao_resposta_fora_dominio in PADROES_RESPOSTA_FORA_DOMINIO)

def guardrail_saida_node(state: AgentState) -> dict:
    ultima_resposta = state["messages"][-1]
    conteudo_ultima_resposta = ultima_resposta.content if isinstance(ultima_resposta.content, str) else str(ultima_resposta.content)

    if verifica_vazamento_informacao(conteudo_ultima_resposta):
        return {"messages": [AIMessage(content="A resposta foi bloqueada")]}
    
    if verifica_mencao_intencao_fora_dominio(conteudo_ultima_resposta):
        return {"messages": [AIMessage(content="Direcione sua pergunta a gráficos e visualizações de dados")]}

    return {}
