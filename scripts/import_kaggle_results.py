from __future__ import annotations

import os
from pathlib import Path

import chromadb
import numpy as np
import pandas as pd

from common import getenv, project_path, read_jsonl

IMPORT_DIR = project_path("data", "import")

CHUNKS_FILE = IMPORT_DIR / "cleaned_chunks.parquet"
EMBEDDINGS_FILE = IMPORT_DIR / "embeddings.npy"
METADATA_FILE = IMPORT_DIR / "metadata.jsonl"


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)
    if not path.is_absolute():
        path = (project_path() / path).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def main() -> None:
    missing = [p.name for p in [CHUNKS_FILE, EMBEDDINGS_FILE, METADATA_FILE] if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "File hasil Kaggle belum lengkap di data/import/: " + ", ".join(missing)
        )

    chunks_df = pd.read_parquet(CHUNKS_FILE)
    embeddings = np.load(EMBEDDINGS_FILE)
    metadata_rows = read_jsonl(METADATA_FILE)

    if len(chunks_df) != len(embeddings) or len(chunks_df) != len(metadata_rows):
        raise ValueError(
            f"Jumlah data tidak sama: chunks={len(chunks_df)}, embeddings={len(embeddings)}, metadata={len(metadata_rows)}"
        )

    required_cols = {"chunk_id", "text"}
    if not required_cols.issubset(chunks_df.columns):
        raise ValueError(f"cleaned_chunks.parquet harus punya kolom: {sorted(required_cols)}")

    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_local_corpus")

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(name=collection_name, metadata={"hnsw:space": "cosine"})

    ids = chunks_df["chunk_id"].astype(str).tolist()
    documents = chunks_df["text"].astype(str).tolist()
    metadatas = []

    for i, meta in enumerate(metadata_rows):
        clean_meta = {}
        for k, v in meta.items():
            # Chroma metadata hanya menerima str/int/float/bool/None.
            if isinstance(v, (str, int, float, bool)) or v is None:
                clean_meta[k] = v
            else:
                clean_meta[k] = str(v)
        metadatas.append(clean_meta)

    # Upsert agar aman saat import ulang.
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.astype("float32").tolist(),
        metadatas=metadatas,
    )

    print(f"OK: {len(ids)} chunks berhasil di-upsert")
    print(f"Chroma path     : {chroma_path}")
    print(f"Collection name : {collection_name}")


if __name__ == "__main__":
    main()
