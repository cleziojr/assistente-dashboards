from dotenv import load_dotenv
load_dotenv()

from langchain.chat_models import init_chat_model

# Fiz a substituição do modelo por que apenas projetos antigos possuem acesso ao 2.5-flash-lite
llm = init_chat_model("google_genai:gemini-3.5-flash-lite")