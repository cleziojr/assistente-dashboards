from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

BASE_DIR = Path(__file__).resolve().parents[2]
PERSIST_DIR = str(BASE_DIR / "chroma_munzner")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vector_store = Chroma(collection_name="munzner_vis_design", embedding_function=embeddings, persist_directory=PERSIST_DIR)
retriever = vector_store.as_retriever(search_kwargs={"k": 4})