from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Aponta sempre para a raiz do repositório (assistente-dashboards/)
BASE_DIR = Path(__file__).resolve().parents[1]
PDF_PATH = BASE_DIR / "data" / "docs" / "[Tamara_Munzner]_Visualization_Analysis_and_Design(b-ok.org).pdf"
PERSIST_DIR = str(BASE_DIR / "chroma_munzner")
COLLECTION_NAME = "munzner_vis_design"


def build_vector_store():
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Arquivo não encontrado em: {PDF_PATH}")

    print("1. Carregando o livro com PyPDFLoader...")
    loader = PyPDFLoader(str(PDF_PATH))
    docs = loader.load()
    print(f"Total de páginas carregadas: {len(docs)}")

    docs_limpos = []
    for doc in docs:
        texto = " ".join(doc.page_content.split())
        if len(texto) > 50:
            doc.page_content = texto
            doc.metadata["page"] = doc.metadata.get("page", 0) + 1
            docs_limpos.append(doc)

    print("2. Cortando em chunks (RecursiveCharacterTextSplitter)...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(docs_limpos)
    print(f"Total de chunks gerados: {len(chunks)}")

    print("3. Inicializando modelo de Embeddings local...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )

    print("4. Indexando no ChromaDB em lotes (persistindo em disco)...")
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
        collection_metadata={"hnsw:space": "cosine"},
    )

    batch_size = 500
    for i in range(0, len(chunks), batch_size):
        lote = chunks[i : i + batch_size]
        ids = [f"munzner-chunk-{j}" for j in range(i, i + len(lote))]
        vector_store.add_documents(documents=lote, ids=ids)
        print(f"Indexados {min(i + batch_size, len(chunks))}/{len(chunks)} chunks...")

    print("Indexação concluída com sucesso!")


if __name__ == "__main__":
    build_vector_store()