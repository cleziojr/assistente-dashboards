from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from src.schemas import AgentState
from src.nodes.input_guard import guardrail_entrada_node
from src.nodes.skill_loader import carrega_skills_node
from src.nodes.rag_search import agentic_rag_node
from src.nodes.rag_evaluator import evaluate_rag_node, roteador_rag
from src.nodes.assistant import assistente_node
from src.nodes.output_guard import guardrail_saida_node
from src.nodes.summarizer import resume_conversa_node, roteador_resumo

def roteador_guardrail(state: AgentState) -> Literal["resumir_mensagens", "carregar_skills", "__end__"]:
    if not state.get("is_safe", True):
        return END
    return roteador_resumo(state)

def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("guardrail_entrada", guardrail_entrada_node)
    builder.add_node("resumir_mensagens", resume_conversa_node)
    builder.add_node("carregar_skills", carrega_skills_node)
    builder.add_node("rag_search", agentic_rag_node)
    builder.add_node("rag_evaluator", evaluate_rag_node)
    builder.add_node("assistente", assistente_node)
    builder.add_node("guardrail_saida", guardrail_saida_node)

    builder.set_entry_point("guardrail_entrada")

    builder.add_conditional_edges("guardrail_entrada", roteador_guardrail, {END: END, "resumir_mensagens": "resumir_mensagens", "carregar_skills": "carregar_skills"})
    builder.add_edge("resumir_mensagens", "carregar_skills")
    builder.add_edge("carregar_skills", "rag_search")
    builder.add_edge("rag_search", "rag_evaluator")
    builder.add_conditional_edges("rag_evaluator", roteador_rag, {"rag_search": "rag_search", "assistant": "assistente"})
    builder.add_edge("assistente", "guardrail_saida")
    builder.add_edge("guardrail_saida", END)

    checkpointer = InMemorySaver()
    return builder.compile(checkpointer=checkpointer)