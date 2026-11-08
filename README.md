# Assistente de Engenharia e Design de Dashboards

**Participantes:**
- Arthur Ferreira de Holanda (`@Arthur-Holanda`)
- Clezio (`@cleziojr`)

---

## 1. Objetivo
Assistente especializado em engenharia e design de dashboards. Destinado a analistas de dados que precisam converter arquivos brutos (CSVs) em aplicações Streamlit interativas baseadas em regras de design pré-estabelecidas.

---

## 2. Arquitetura e Diagrama do Grafo (LangGraph)

O sistema opera sobre uma arquitetura de grafo de estado explícito e iterativo (`StateGraph`), composta pelos seguintes nós:

```mermaid
graph TD
    START((START)) --> guardrail_entrada[1. guardrail_entrada]
    guardrail_entrada -- "is_safe == False" --> END((END))
    guardrail_entrada -- "mensagens > 10" --> resumir[2. resumir]
    guardrail_entrada -- "is_safe == True" --> carregar_skills[3. carregar_skills]

    resumir --> carregar_skills

    carregar_skills --> rag_search[4. rag_search]

    rag_search --> rag_evaluator[5. rag_evaluator]
    rag_evaluator -- "incompleto (rag_attempts < 3)" --> rag_search
    rag_evaluator -- "completo" --> assistente[6. assistente]

    assistente --> guardrail_saida[7. guardrail_saida]
    guardrail_saida -- "Seguro" --> END((END))