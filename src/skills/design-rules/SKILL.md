---
name: design-rules
description: Aplica técnicas de storytelling. Use quando o usuário mencionar cor, escala, canal visual ou design.
---

# Regras de Design Visual

## Procedimento

1. **Identificar o tipo de dado de cada coluna**
   - Se a coluna for numérica contínua (ex: vendas, temperatura): use posição como canal visual principal, ou seja, coloque no eixo
   - Se a coluna for categórica (ex: cidade, categoria de produto): use cor discreta para diferenciar grupos; nunca use uma escala de cor contínua para dados categóricos
   - Se a coluna for ordenada mas não numérica (ex: baixo, médio, alto): use uma escala de cor sequencial, do tom mais claro (menor) ao mais escuro (maior)

2. **Escolher o canal visual mais eficaz**
   - Para a métrica principal, prefira sempre o canal mais alto nesta hierarquia: posição no eixo > comprimento da barra > ângulo > área > cor
   - Exemplo: para comparar vendas por categoria, barras (comprimento) são mais eficazes que um gráfico de pizza

3. **Consultar o RAG quando necessário**
   - Se a dúvida não for resolvida pelos passos anteriores, formule uma query em inglês e aguarde o contexto recuperado antes de responder
   - Exemplos de queries: "color encoding categorical data", "sequential color scale ordered data"

4. **Justificar a escolha ao usuário**
   - Explique qual tipo de dado foi identificado, qual canal visual foi escolhido e por quê ele é mais adequado para esse caso
   - Exemplo: "Escolhi barras verticais porque você tem uma variável categórica no eixo X e uma numérica no eixo Y, e o comprimento da barra é o canal mais eficaz para comparar magnitudes entre categorias com base no material de referência (páginas: ...)"

5. **Verificar acessibilidade** — evite vermelho e verde juntos; prefira paletas uniformes.

## Restrições
- Baseie-se apenas no contexto recuperado pelo RAG ou no que está nesta skill.
- Não repita o que a ferramenta já faz. Esta skill trata do *porquê* da escolha, não do *como* executar.

---