import sys
from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from src.schemas import AgentState
from src.mcp.config import MCP_CONFIG
from src.llm import llm
from src.prompts.assistant import SYSTEM_PROMPT
from src.rag.tool import consultar_livro_visualizacao

async def assistente_node(state: AgentState, **kwargs) -> dict:
    cfg = MCP_CONFIG["dashboard"]
    params = StdioServerParameters(command=cfg["command"], args=cfg["args"])

    async with stdio_client(params) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()
            ferramentas_mcp = await load_mcp_tools(sessao)
            ferramentas = ferramentas_mcp + [consultar_livro_visualizacao]
            agente = create_agent(llm, ferramentas)
            catalogo_skills = state.get("skill_catalog", "")

            mensagem_sistema = SystemMessage(content=SYSTEM_PROMPT.format(skill_catalog=catalogo_skills))
            mensagens_com_sistema = [mensagem_sistema] + list(state["messages"])
            resultado = await agente.ainvoke({"messages": mensagens_com_sistema})

            novas_mensagens = resultado["messages"][len(mensagens_com_sistema):]
            return {"messages": novas_mensagens}
