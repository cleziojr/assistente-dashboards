from langchain_core.prompts import ChatPromptTemplate

PROMPT_AVALIACAO = ChatPromptTemplate.from_messages([
        ("system",
         "Você é um avaliador de recuperação de informação (RAG Evaluator).\n"
         "Analise a pergunta original do usuário e o contexto já recuperado do livro 'Visualization Analysis and Design' (Tamara Munzner).\n"
         "Se o contexto ainda não trouxer regras específicas suficientes ou se faltar algum dos itens pedidos na comparação, "
         "marque como 'incompleto' e gere uma nova query em inglês focada especificamente no que faltou."),
        ("human", "Pergunta do usuário: {question}\n\nContexto recuperado até agora:\n{context}")
])