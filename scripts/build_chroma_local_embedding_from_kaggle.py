from __future__ import annotations

from pathlib import Path
import json
import hashlib
import os

import chromadb
import pandas as pd
from fastembed import TextEmbedding
from dotenv import load_dotenv

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
IMPORT_DIR = PROJECT_DIR / "data" / "import"

CHUNKS_FILE = IMPORT_DIR / "cleaned_chunks.parquet"
METADATA_FILE = IMPORT_DIR / "metadata.jsonl"


def getenv(key: str, default: str) -> str:
    value = os.getenv(key)
    if value is None or value.strip() == "":
        return default
    return value.strip()


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def clean_chroma_metadata(meta: dict) -> dict:
    clean = {}

    for key, value in meta.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = value
        else:
            clean[key] = json.dumps(value, ensure_ascii=False)

    return clean


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)

    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()

    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {CHUNKS_FILE}")

    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {METADATA_FILE}")

    chunks_df = pd.read_parquet(CHUNKS_FILE)
    metadata_rows = read_jsonl(METADATA_FILE)

    if "text" not in chunks_df.columns:
        raise ValueError("cleaned_chunks.parquet wajib memiliki kolom 'text'.")

    if len(chunks_df) != len(metadata_rows):
        raise ValueError(
            f"Jumlah chunk dan metadata tidak sama: "
            f"chunks={len(chunks_df)}, metadata={len(metadata_rows)}"
        )

    embedding_model_name = getenv(
        "LOCAL_EMBED_MODEL",
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    )

    collection_name = getenv(
        "LOCAL_EMBED_COLLECTION",
        "rag_kaggle_local_embed_sandbox",
    )

    chroma_path = resolve_chroma_path()

    print("Loading local embedding model...")
    print(f"Model: {embedding_model_name}")

    embedder = TextEmbedding(model_name=embedding_model_name)

    texts = chunks_df["text"].fillna("").astype(str).tolist()

    print(f"Embedding {len(texts)} chunks...")
    embeddings = [vec.tolist() for vec in embedder.embed(texts)]

    ids = []
    metadatas = []

    for i, row in chunks_df.iterrows():
        doc_id = str(row.get("doc_id", "doc"))
        chunk_index = int(row.get("chunk_index", i))
        text = str(row.get("text", ""))
        chunk_hash = sha256_text(text)

        chunk_id = f"{doc_id}_{chunk_index:04d}_{chunk_hash[:12]}"
        ids.append(chunk_id)

        meta = dict(metadata_rows[i])
        meta.setdefault("doc_id", doc_id)
        meta.setdefault("title", str(row.get("title", "")))
        meta.setdefault("source", str(row.get("source", "")))
        meta.setdefault("chunk_index", chunk_index)
        meta.setdefault("char_count", int(row.get("char_count", len(text))))
        meta["chunk_hash"] = chunk_hash
        meta["origin"] = "kaggle_cleaning_local_embedding"
        meta["embedding_model"] = embedding_model_name
        meta["collection_stage"] = "sandbox"

        metadatas.append(clean_chroma_metadata(meta))

    client = chromadb.PersistentClient(path=str(chroma_path))

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": embedding_model_name,
            "description": "Kaggle-cleaned chunks embedded locally with FastEmbed",
        },
    )

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("OK: Chroma sandbox lokal berhasil dibuat dari hasil Kaggle cleaning/chunking.")
    print(f"Chunks imported : {len(ids)}")
    print(f"Embedding dims  : {len(embeddings[0]) if embeddings else 0}")
    print(f"Chroma path     : {chroma_path}")
    print(f"Collection      : {collection_name}")


if __name__ == "__main__":
    main()
