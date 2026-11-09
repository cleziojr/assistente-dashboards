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

4. **Chamar a ferramenta de estruturação** (padrão — sempre use primeiro):
   - "estrutura_dados_barras_verticais" ou "estrutura_dados_barras_horizontais": passe "csv_path", "eixo_x" e "eixo_y".
   - "efetua_agregacao_dados": passe "csv_path", "coluna" e "agregacao" (total, media, contagem, maximo, minimo).
   - O gráfico será renderizado automaticamente no chat a partir do resultado. NÃO chame "gerar_app_streamlit" neste passo.

5. **Confirmar com o usuário**: apresente o resultado e pergunte se deseja outro tipo de visualização ou um app com link de acesso externo.

6. **Gerar app independente (somente se o usuário pedir explicitamente um link ou app externo)**: chame "gerar_app_streamlit" com os parâmetros:
   - "csv_path": caminho do arquivo
   - "tipo_grafico": "barras_verticais", "barras_horizontais" ou "cartao"
   - "eixo_x": coluna categórica
   - "eixo_y": coluna numérica
   - "titulo": título do dashboard (opcional)
   - "agregacao": apenas para cartao (total, media, contagem, maximo, minimo)
   - "session_id": identificador da sessão para reutilizar a porta se atualizar o dashboard
   - Aguarde o retorno da ferramenta (pode levar até 20 segundos enquanto o servidor sobe).
   - Se "ok: true", retorne o link "url" ao usuário com a mensagem de que o dashboard está pronto.
   - Se "ok: false", informe o erro ao usuário e não envie nenhum link.

## Restrições
- Nunca gere código Python diretamente na resposta.
- Nunca acesse colunas que não constem no resumo retornado pelo "upload_csv".

---