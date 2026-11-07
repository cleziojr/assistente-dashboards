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
    START((START)) --> input_guard[1. input_guard]
    input_guard -- "is_safe == False" --> END((END))
    input_guard -- "is_safe == True" --> skill_loader[2. skill_loader]
    skill_loader --> assistant[3. assistant]
    
    assistant -- "Precisa de regras/design" --> rag_search[4. rag_search]
    assistant -- "Chama Tool MCP" --> mcp_tools[6. mcp_tools]
    assistant -- "Finalizou raciocínio" --> output_guard[7. output_guard]
    
    rag_search --> rag_evaluator[5. rag_evaluator]
    rag_evaluator -- "incompleto (rag_attempts < 3)" --> rag_search
    rag_evaluator -- "completo" --> assistant
    
    mcp_tools --> assistant
    
    output_guard -- "Inseguro (erro)" --> assistant
    output_guard -- "Seguro" --> END