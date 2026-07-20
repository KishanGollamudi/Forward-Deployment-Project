import chromadb
import os

CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))
TOP_K = 5


def get_relevant_context(query: str) -> str:
    chroma = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = chroma.get_or_create_collection("products")

    results = collection.query(query_texts=[query], n_results=TOP_K)
    docs = results.get("documents", [[]])[0]
    return "\n\n".join(docs)
