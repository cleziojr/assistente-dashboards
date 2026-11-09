TEMPLATE_STREAMLIT = '''import streamlit as st
import pandas as pd

st.set_page_config(page_title="{titulo}")
st.title("{titulo}")

dados = {dados_json}
df = pd.DataFrame(dados).set_index("{eixo_x}")

{codigo_grafico}
'''

TEMPLATE_BARRAS_VERTICAIS = 'st.bar_chart(df["{eixo_y}"], x_label="{eixo_x}", y_label="{eixo_y}")'
TEMPLATE_BARRAS_HORIZONTAIS = 'st.bar_chart(df["{eixo_y}"], horizontal=True, x_label="{eixo_y}", y_label="{eixo_x}")'
TEMPLATE_CARTAO = 'st.metric(label="{label}", value={valor})'
