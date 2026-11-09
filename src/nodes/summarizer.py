from typing import Literal
from langchain_core.messages import RemoveMessage, SystemMessage, HumanMessage, AIMessage
from src.schemas import AgentState
from src.llm import llm

MAXIMO_MENSAGENS = 10

def resume_conversa_node(state: AgentState) -> dict:
    mensagens = state["messages"]
    mensagens_alvo_sumarizacao = mensagens[:-1]

    linhas = []
    for mensagem in mensagens_alvo_sumarizacao:
        if isinstance(mensagem, HumanMessage):
            perfil = "Usuário"
        elif isinstance(mensagem, AIMessage):
            perfil = "Assistente"
        else:
            continue
        texto = mensagem.content if isinstance(mensagem.content, str) else str(mensagem.content)
        linhas.append(f"{perfil}: {texto}")

    prompt_sumarizacao = ("Resuma a conversa abaixo de forma concisa, em até três frases, preservando os fatos importantes: dashboards solicitados, colunas discutidas, escolhas de gráficos. \n\n"
                          + "\n".join(linhas)
    )

    resumo_mensagens_ai_message_object = llm.invoke(prompt_sumarizacao)
    texto_resumo = resumo_mensagens_ai_message_object.content if isinstance(resumo_mensagens_ai_message_object.content, str) else str(resumo_mensagens_ai_message_object.content)

    mensagens_removidas = [RemoveMessage(id=mensagem.id) for mensagem in mensagens_alvo_sumarizacao]
    mensagem_resumo_sistema = SystemMessage(content=f"[Resumo da conversa anterior]: {texto_resumo}")

    return {"messages": mensagens_removidas + [mensagem_resumo_sistema]}

def roteador_resumo(state: AgentState) -> Literal["resumir_mensagens", "carregar_skills"]:
    if len(state["messages"]) > MAXIMO_MENSAGENS:
        return "resumir_mensagens"
    return "carregar_skills"