from __future__ import annotations

import argparse
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from fastembed import TextEmbedding


load_dotenv()


PROJECT_DIR = Path(__file__).resolve().parents[1]

DEFAULT_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DEFAULT_COLLECTION = "rag_kaggle_local_embed_sandbox_k3"


def getenv(key: str, default: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        return default

    return value.strip()


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)

    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()

    return path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query a K3 local-embedding Chroma sandbox collection."
    )
    parser.add_argument("query", nargs="+", help="Query text.")
    parser.add_argument(
        "--collection",
        default=None,
        help="Collection name. Default from LOCAL_EMBED_COLLECTION or K3 default.",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Embedding model. Default from LOCAL_EMBED_MODEL or MiniLM.",
    )
    parser.add_argument(
        "--chroma-path",
        default=None,
        help="Chroma path. Default from CHROMA_PATH or ./chroma_db.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Jumlah hasil retrieval.",
    )

    args = parser.parse_args()

    query = " ".join(args.query).strip()

    embedding_model = (
        args.embedding_model
        or os.getenv("LOCAL_EMBED_MODEL")
        or DEFAULT_MODEL
    )

    collection_name = (
        args.collection
        or os.getenv("LOCAL_EMBED_COLLECTION")
        or DEFAULT_COLLECTION
    )

    chroma_raw = args.chroma_path or getenv("CHROMA_PATH", "./chroma_db")
    chroma_path = resolve_path(chroma_raw)

    print(f"Query       : {query}")
    print(f"Model       : {embedding_model}")
    print(f"Collection  : {collection_name}")
    print(f"Chroma path : {chroma_path}")

    embedder = TextEmbedding(model_name=embedding_model)
    query_embedding = list(embedder.embed([query]))[0].tolist()

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=args.top_k,
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
