from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from common import getenv, project_path


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)
    if not path.is_absolute():
        path = (project_path() / path).resolve()
    return path


def main() -> None:
    query = " ".join(sys.argv[1:]).strip() or "apa isi utama dokumen ini?"

    model_name = getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    query_prefix = getenv("EMBEDDING_QUERY_PREFIX", "query:")
    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_local_corpus")
    top_k = int(getenv("TOP_K_FINAL", "4"))

    model = SentenceTransformer(model_name)
    query_embedding = model.encode([f"{query_prefix} {query}"], normalize_embeddings=True)[0].astype("float32").tolist()

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    print(f"\nQUERY: {query}\n")
    for rank, (doc, meta, dist) in enumerate(zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ), start=1):
        print("=" * 80)
        print(f"RANK {rank} | distance={dist:.4f}")
        print(f"source={meta.get('source')} | title={meta.get('title')} | chunk={meta.get('chunk_index')}")
        print("-" * 80)
        print(doc[:900].replace("\n", " "))
        print()


if __name__ == "__main__":
    main()
