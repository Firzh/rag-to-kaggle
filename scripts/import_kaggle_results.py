from __future__ import annotations

from pathlib import Path
import json

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


def clean_chroma_metadata(meta: dict) -> dict:
    clean = {}

    for key, value in meta.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            clean[key] = value
        else:
            clean[key] = json.dumps(value, ensure_ascii=False)

    return clean


def build_ids(chunks_df: pd.DataFrame) -> list[str]:
    if "chunk_id" in chunks_df.columns:
        return chunks_df["chunk_id"].astype(str).tolist()

    ids = []

    for i, row in chunks_df.iterrows():
        doc_id = str(row.get("doc_id", "doc"))
        chunk_index = int(row.get("chunk_index", i))
        ids.append(f"{doc_id}_{chunk_index:04d}")

    return ids


def main() -> None:
    missing = [
        p.name
        for p in [CHUNKS_FILE, EMBEDDINGS_FILE, METADATA_FILE]
        if not p.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "File hasil Kaggle belum lengkap di data/import/: " + ", ".join(missing)
        )

    chunks_df = pd.read_parquet(CHUNKS_FILE)
    embeddings = np.load(EMBEDDINGS_FILE)
    metadata_rows = read_jsonl(METADATA_FILE)

    if "text" not in chunks_df.columns:
        raise ValueError("cleaned_chunks.parquet wajib memiliki kolom 'text'.")

    if len(chunks_df) != len(embeddings) or len(chunks_df) != len(metadata_rows):
        raise ValueError(
            f"Jumlah data tidak sama: "
            f"chunks={len(chunks_df)}, "
            f"embeddings={len(embeddings)}, "
            f"metadata={len(metadata_rows)}"
        )

    ids = build_ids(chunks_df)
    documents = chunks_df["text"].astype(str).tolist()

    metadatas = []

    for i, meta in enumerate(metadata_rows):
        row_meta = dict(meta)

        if "doc_id" in chunks_df.columns:
            row_meta.setdefault("doc_id", str(chunks_df.iloc[i].get("doc_id", "")))

        if "title" in chunks_df.columns:
            row_meta.setdefault("title", str(chunks_df.iloc[i].get("title", "")))

        if "source" in chunks_df.columns:
            row_meta.setdefault("source", str(chunks_df.iloc[i].get("source", "")))

        if "chunk_index" in chunks_df.columns:
            row_meta.setdefault("chunk_index", int(chunks_df.iloc[i].get("chunk_index", i)))

        row_meta.setdefault("origin", "kaggle_import")
        row_meta.setdefault("import_mode", "sandbox")

        metadatas.append(clean_chroma_metadata(row_meta))

    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_kaggle_sandbox")

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings.astype("float32").tolist(),
        metadatas=metadatas,
    )

    print("OK: import hasil Kaggle ke ChromaDB selesai")
    print(f"Chunks imported : {len(ids)}")
    print(f"Embedding shape : {embeddings.shape}")
    print(f"Chroma path     : {chroma_path}")
    print(f"Collection name : {collection_name}")


if __name__ == "__main__":
    main()
