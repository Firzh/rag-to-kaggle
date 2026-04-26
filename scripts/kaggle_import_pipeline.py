from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import chromadb
import numpy as np
import pandas as pd
from dotenv import load_dotenv


load_dotenv()


PROJECT_DIR = Path(__file__).resolve().parents[1]


DEFAULT_LOCAL_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

DEFAULT_COLLECTIONS = {
    "smoke-kaggle-embedding": "rag_kaggle_tfidf_smoke_k3",
    "local-embedding": "rag_kaggle_local_embed_sandbox_k3",
}


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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}: {exc}") from exc

            if not isinstance(item, dict):
                raise ValueError(f"JSONL row must be object at {path}:{line_no}")

            rows.append(item)

    return rows


def clean_chroma_metadata(meta: dict[str, Any]) -> dict[str, str | int | float | bool]:
    clean: dict[str, str | int | float | bool] = {}

    for key, value in meta.items():
        if value is None:
            clean[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = json.dumps(value, ensure_ascii=False)

    return clean


def validate_required_files(input_dir: Path, mode: str) -> None:
    required = ["cleaned_chunks.parquet", "metadata.jsonl"]

    if mode == "smoke-kaggle-embedding":
        required.append("embeddings.npy")

    missing = [name for name in required if not (input_dir / name).exists()]

    if missing:
        raise FileNotFoundError(
            "File input belum lengkap untuk mode "
            f"{mode}: {', '.join(missing)}"
        )


def load_chunks_and_metadata(input_dir: Path) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    chunks_path = input_dir / "cleaned_chunks.parquet"
    metadata_path = input_dir / "metadata.jsonl"

    chunks_df = pd.read_parquet(chunks_path)
    metadata_rows = read_jsonl(metadata_path)

    required_columns = [
        "chunk_id",
        "doc_id",
        "title",
        "source",
        "source_type",
        "chunk_index",
        "text",
        "char_count",
        "token_estimate",
        "chunking_method",
        "sanitized",
        "origin_pipeline",
        "content_hash",
    ]

    missing_columns = [col for col in required_columns if col not in chunks_df.columns]

    if missing_columns:
        raise ValueError(
            "cleaned_chunks.parquet belum mengikuti schema K2. "
            "Kolom hilang: " + ", ".join(missing_columns)
        )

    if len(chunks_df) != len(metadata_rows):
        raise ValueError(
            f"Jumlah chunk dan metadata tidak sama: "
            f"chunks={len(chunks_df)}, metadata={len(metadata_rows)}"
        )

    if len(chunks_df) == 0:
        raise ValueError("cleaned_chunks.parquet kosong.")

    return chunks_df, metadata_rows


def load_kaggle_embeddings(input_dir: Path, expected_count: int) -> list[list[float]]:
    embeddings_path = input_dir / "embeddings.npy"
    embeddings = np.load(embeddings_path)

    if len(embeddings) != expected_count:
        raise ValueError(
            f"Jumlah embedding tidak sama dengan chunk: "
            f"embeddings={len(embeddings)}, chunks={expected_count}"
        )

    return embeddings.astype("float32").tolist()


def build_local_embeddings(texts: list[str], model_name: str) -> list[list[float]]:
    from fastembed import TextEmbedding

    print("Loading local embedding model...")
    print(f"Model: {model_name}")

    embedder = TextEmbedding(model_name=model_name)

    print(f"Embedding {len(texts)} chunks...")
    vectors = [vec.tolist() for vec in embedder.embed(texts)]

    return vectors


def delete_collection_if_exists(client: chromadb.PersistentClient, collection_name: str) -> None:
    try:
        client.delete_collection(collection_name)
        print(f"Deleted existing sandbox collection: {collection_name}")
    except Exception:
        pass


def build_records(
    chunks_df: pd.DataFrame,
    metadata_rows: list[dict[str, Any]],
    *,
    mode: str,
    embedding_model: str,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for i, row in chunks_df.iterrows():
        row_dict = row.to_dict()
        meta = dict(metadata_rows[i])

        chunk_id = str(row_dict["chunk_id"])
        text = str(row_dict["text"])

        ids.append(chunk_id)
        documents.append(text)

        combined = {}
        combined.update(meta)
        combined.update({
            "chunk_id": chunk_id,
            "doc_id": str(row_dict["doc_id"]),
            "title": str(row_dict["title"]),
            "source": str(row_dict["source"]),
            "source_type": str(row_dict["source_type"]),
            "chunk_index": int(row_dict["chunk_index"]),
            "char_count": int(row_dict["char_count"]),
            "token_estimate": int(row_dict["token_estimate"]),
            "chunking_method": str(row_dict["chunking_method"]),
            "sanitized": bool(row_dict["sanitized"]),
            "origin_pipeline": str(row_dict["origin_pipeline"]),
            "content_hash": str(row_dict["content_hash"]),
            "k3_import_mode": mode,
            "embedding_model": embedding_model,
            "collection_stage": "sandbox",
        })

        metadatas.append(clean_chroma_metadata(combined))

    return ids, documents, metadatas


def upsert_batches(
    collection,
    *,
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, Any]],
    batch_size: int = 500,
) -> None:
    total = len(ids)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)

        collection.upsert(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=embeddings[start:end],
            metadatas=metadatas[start:end],
        )

        print(f"Upserted {end}/{total}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import Kaggle cleaned chunks into Chroma using explicit K3 import modes."
    )
    parser.add_argument(
        "--mode",
        choices=["smoke-kaggle-embedding", "local-embedding"],
        required=True,
        help="Import mode.",
    )
    parser.add_argument(
        "--input-dir",
        default="data/import",
        help="Folder hasil Kaggle yang sudah mengikuti schema K2.",
    )
    parser.add_argument(
        "--chroma-path",
        default=None,
        help="Path ChromaDB. Default memakai CHROMA_PATH dari .env atau ./chroma_db.",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Nama collection tujuan.",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Model embedding lokal untuk mode local-embedding.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Hapus collection tujuan sebelum import. Gunakan hanya untuk sandbox.",
    )

    args = parser.parse_args()

    input_dir = resolve_path(args.input_dir)
    validate_required_files(input_dir, args.mode)

    chunks_df, metadata_rows = load_chunks_and_metadata(input_dir)

    texts = chunks_df["text"].fillna("").astype(str).tolist()

    if args.mode == "smoke-kaggle-embedding":
        embeddings = load_kaggle_embeddings(input_dir, expected_count=len(chunks_df))
        embedding_model = "kaggle_embeddings_npy"
    else:
        embedding_model = (
            args.embedding_model
            or os.getenv("LOCAL_EMBED_MODEL")
            or DEFAULT_LOCAL_MODEL
        )
        embeddings = build_local_embeddings(texts, embedding_model)

    if not embeddings:
        raise ValueError("Embedding kosong.")

    embedding_dim = len(embeddings[0])

    collection_name = (
        args.collection
        or os.getenv("LOCAL_EMBED_COLLECTION")
        or DEFAULT_COLLECTIONS[args.mode]
    )

    chroma_raw = args.chroma_path or getenv("CHROMA_PATH", "./chroma_db")
    chroma_path = resolve_path(chroma_raw)
    chroma_path.mkdir(parents=True, exist_ok=True)

    ids, documents, metadatas = build_records(
        chunks_df,
        metadata_rows,
        mode=args.mode,
        embedding_model=embedding_model,
    )

    client = chromadb.PersistentClient(path=str(chroma_path))

    if args.reset:
        delete_collection_if_exists(client, collection_name)

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine",
            "k3_import_mode": args.mode,
            "embedding_model": embedding_model,
            "collection_stage": "sandbox",
        },
    )

    upsert_batches(
        collection,
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print("")
    print("OK: K3 import selesai.")
    print(f"Mode          : {args.mode}")
    print(f"Chunks        : {len(ids)}")
    print(f"Embedding dim : {embedding_dim}")
    print(f"Chroma path   : {chroma_path}")
    print(f"Collection    : {collection_name}")


if __name__ == "__main__":
    main()
