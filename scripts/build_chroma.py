from __future__ import annotations

import uuid
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from common import getenv, project_path, read_jsonl


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)
    if not path.is_absolute():
        path = (project_path() / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def simple_chunks(text: str, chunk_chars: int = 1800, overlap: int = 250) -> list[str]:
    text = text.strip()
    if len(text) <= chunk_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_chars, len(text))
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def main() -> None:
    corpus_path = project_path("data", "export", "corpus_export.jsonl")
    if not corpus_path.exists():
        raise FileNotFoundError("Jalankan dulu sanitize dan export corpus.")

    model_name = getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    passage_prefix = getenv("EMBEDDING_PASSAGE_PREFIX", "passage:")
    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_local_corpus")

    rows = read_jsonl(corpus_path)
    chunk_rows = []
    for row in rows:
        for idx, chunk in enumerate(simple_chunks(row["text"])):
            chunk_rows.append({
                "id": f"{row['doc_id']}_{idx:04d}",
                "text": chunk,
                "metadata": {
                    "doc_id": row["doc_id"],
                    "title": row.get("title", ""),
                    "source": row.get("source", ""),
                    "chunk_index": idx,
                    "origin": "local_build",
                },
            })

    model = SentenceTransformer(model_name)
    texts_for_embedding = [f"{passage_prefix} {r['text']}" for r in chunk_rows]
    embeddings = model.encode(texts_for_embedding, normalize_embeddings=True, show_progress_bar=True)

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})
    collection.upsert(
        ids=[r["id"] for r in chunk_rows],
        documents=[r["text"] for r in chunk_rows],
        embeddings=embeddings.astype("float32").tolist(),
        metadatas=[r["metadata"] for r in chunk_rows],
    )

    print(f"OK: build lokal selesai. chunks={len(chunk_rows)}")
    print(f"Chroma path     : {chroma_path}")
    print(f"Collection name : {collection_name}")


if __name__ == "__main__":
    main()
