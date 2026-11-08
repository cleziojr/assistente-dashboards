import uuid
import asyncio

import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.graph.dashboard_graph import build_graph

st.set_page_config(page_title="Assistente de Dashboards", layout="wide")
st.title("📊 Assistente de Dashboards")


@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "historico" not in st.session_state:
    st.session_state.historico = []


with st.sidebar:
    st.header("⚙️ Configurações")
    if st.button("🆕 Nova conversa"):
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.historico = []
        st.rerun()
    st.caption(f"Thread: `{st.session_state.thread_id[:8]}…`")


for entrada in st.session_state.historico:
    with st.chat_message(entrada["role"]):
        st.markdown(entrada["content"])
        if entrada.get("ferramentas"):
            with st.expander("🔧 Ferramentas chamadas"):
                for t in entrada["ferramentas"]:
                    st.code(t, language="json")
        if entrada.get("skills"):
            with st.expander("📘 Skills carregadas"):
                for s in entrada["skills"]:
                    st.markdown(f"- `{s}`")


prompt = st.chat_input("Faça uma pergunta sobre dashboards ou visualização de dados...")

if prompt:
    st.session_state.historico.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    config = {"configurable": {"thread_id": st.session_state.thread_id}}

    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            resultado = asyncio.run(
                graph.ainvoke(
                    {"messages": [HumanMessage(content=prompt)]},
                    config=config,
                )
            )

        resposta_texto = ""
        ferramentas_chamadas = []
        skills_carregadas = resultado.get("active_skills", [])

        for msg in reversed(resultado["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                resposta_texto = msg.content if isinstance(msg.content, str) else str(msg.content)
                break

        for msg in resultado["messages"]:
            if isinstance(msg, ToolMessage):
                linha = f"ferramenta: {msg.name}\nresultado: {str(msg.content)[:300]}"
                ferramentas_chamadas.append(linha)

        st.markdown(resposta_texto)

        if ferramentas_chamadas:
            with st.expander("🔧 Ferramentas chamadas"):
                for t in ferramentas_chamadas:
                    st.code(t, language="json")

        if skills_carregadas:
            with st.expander("📘 Skills carregadas"):
                for s in skills_carregadas:
                    st.markdown(f"- `{s}`")

    st.session_state.historico.append({
        "role": "assistant",
        "content": resposta_texto,
        "ferramentas": ferramentas_chamadas,
        "skills": skills_carregadas,
    })
