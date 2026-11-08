from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from src.schemas import AgentState
from src.llm import llm
from src.prompts.assistant import SYSTEM_PROMPT

async def assistente_node(state: AgentState, mcp_client: MultiServerMCPClient) -> dict:
    ferramentas = await mcp_client.get_tools()
    agente = create_react_agent(llm, ferramentas)
    catalogo_skills = state.get("skill_catalog", "")
    contexto_rag = state.get("rag_context", "")

    mensagem_sistema = SystemMessage(content=SYSTEM_PROMPT.format(skill_catalog=catalogo_skills, rag_context=contexto_rag))
    mensagens_com_sistema = [mensagem_sistema] + list(state["messages"])
    resultado = await agente.ainvoke({"messages": mensagens_com_sistema})

    novas_mensagens = resultado["messages"][len(mensagens_com_sistema):]
    return {"messages": novas_mensagens}
