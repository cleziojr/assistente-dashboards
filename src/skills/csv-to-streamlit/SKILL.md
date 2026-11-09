---
name: csv-to-streamlit
description: Transforma CSV em dashboard Streamlit. Use quando o usuário mencionar csv, upload, gráfico ou dashboard.
---

# CSV para Streamlit

## Procedimento

1. **Validar o arquivo**: chame "upload_csv(path)" e confirme "ok: true". Apresente ao usuário as colunas encontradas e seus tipos.

2. **Classificar as colunas**
   - Numérica contínua → candidata a métrica (eixo Y, cartão)
   - Categórica → candidata a dimensão (eixo X, agrupamento)

3. **Escolher o tipo de visualização**
   - Comparação entre categorias → "estrutura_dados_barras_verticais"
   - Ranking decrescente → "estrutura_dados_barras_horizontais"
   - Valor único agregado → "efetua_agregacao_dados"
   - Em caso de dúvida sobre a escolha, leia "src/skills/design-rules/SKILL.md"

4. **Chamar a ferramenta de estruturação**: passe "csv_path" e as colunas identificadas no passo 2.
   - Para "efetua_agregacao_dados", informe também a "agregacao" desejada (total, media, contagem, maximo, minimo).
   - O assistente Streamlit renderizará o gráfico automaticamente a partir do resultado retornado pela ferramenta.

5. **Confirmar com o usuário**: apresente o resultado e pergunte se deseja outro tipo de visualização ou exportar como app independente.

6. **Gerar app independente (opcional)**: se o usuário solicitar um dashboard fora do chat ou um link de acesso, chame "gerar_app_streamlit" com os parâmetros:
   - "csv_path": caminho do arquivo
   - "tipo_grafico": "barras_verticais", "barras_horizontais" ou "cartao"
   - "eixo_x": coluna categórica
   - "eixo_y": coluna numérica
   - "titulo": título do dashboard (opcional)
   - "agregacao": apenas para cartao (total, media, contagem, maximo, minimo)
   - "session_id": identificador da sessão para reutilizar a porta se atualizar o dashboard
   - Retorne o link "url" ao usuário.

## Restrições
- Nunca gere código Python diretamente na resposta.
- Nunca acesse colunas que não constem no resumo retornado pelo "upload_csv".

---