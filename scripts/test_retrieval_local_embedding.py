from __future__ import annotations

from pathlib import Path
import os

import chromadb
from fastembed import TextEmbedding
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]


def getenv(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)

    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()

    return path


def main() -> None:
    import sys

    query = " ".join(sys.argv[1:]).strip()

    if not query:
        query = "Apa fungsi Kaggle dalam pipeline RAG lokal?"

    embedding_model_name = getenv(
        "LOCAL_EMBED_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    collection_name = getenv(
        "LOCAL_EMBED_COLLECTION",
        "rag_kaggle_local_embed_sandbox",
    )

    chroma_path = resolve_chroma_path()

    print(f"Query      : {query}")
    print(f"Model      : {embedding_model_name}")
    print(f"Collection : {collection_name}")
    print(f"Chroma path: {chroma_path}")

    embedder = TextEmbedding(model_name=embedding_model_name)
    query_embedding = list(embedder.embed([query]))[0].tolist()

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
        include=["documents", "metadatas", "distances"],
    )

    ids = result.get("ids", [[]])[0]
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    print(f"Total result: {len(ids)}")

    for i, item_id in enumerate(ids):
        print("=" * 80)
        print(f"Rank     : {i + 1}")
        print(f"ID       : {item_id}")
        print(f"Distance : {distances[i]}")
        print(f"Metadata : {metas[i]}")
        print("Document :")
        print(docs[i])


if __name__ == "__main__":
    main()
