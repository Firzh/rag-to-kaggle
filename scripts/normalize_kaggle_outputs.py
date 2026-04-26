from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import shutil
from typing import Any

import pandas as pd


REQUIRED_COLUMNS = [
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


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    if not path.exists():
        return rows

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                rows.append(json.loads(line))

    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def token_estimate(text: str) -> int:
    if not text.strip():
        return 0

    return max(1, int(len(text.split()) * 1.3))


def as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ok"}

    return bool(value)


def normalize_metadata_cell(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if isinstance(value, str):
        value = value.strip()

        if not value:
            return {}

        try:
            parsed = json.loads(value)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return {"raw_metadata": value}

    return {}


def guess_source_type(source: str, metadata: dict[str, Any]) -> str:
    source_type = metadata.get("source_type")

    if isinstance(source_type, str) and source_type.strip():
        return source_type.strip()

    source_lower = str(source).lower()

    if source_lower.startswith("http://") or source_lower.startswith("https://"):
        return "web"

    if metadata.get("from_chroma") is True:
        return "chroma_export"

    if source_lower.endswith((".txt", ".md", ".pdf", ".docx", ".html", ".htm")):
        return "local_file"

    return "unknown"


def backup_file(path: Path) -> None:
    if path.exists():
        backup_path = path.with_suffix(path.suffix + ".pre_k2.bak")
        shutil.copy2(path, backup_path)
        print(f"Backup dibuat: {backup_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-dir",
        default="data/import",
        help="Folder input hasil Kaggle.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/import",
        help="Folder output hasil normalisasi.",
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Backup file output lama sebelum ditimpa.",
    )

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    chunks_path = input_dir / "cleaned_chunks.parquet"
    metadata_path = input_dir / "metadata.jsonl"

    if not chunks_path.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {chunks_path}")

    if not metadata_path.exists():
        raise FileNotFoundError(f"Tidak ditemukan: {metadata_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    chunks_df = pd.read_parquet(chunks_path)
    metadata_rows = read_jsonl(metadata_path)

    if "text" not in chunks_df.columns:
        raise ValueError("cleaned_chunks.parquet wajib memiliki kolom 'text'.")

    if not metadata_rows:
        metadata_rows = [{} for _ in range(len(chunks_df))]

    if len(metadata_rows) != len(chunks_df):
        raise ValueError(
            f"Jumlah metadata tidak sama dengan chunks: "
            f"metadata={len(metadata_rows)}, chunks={len(chunks_df)}"
        )

    normalized_rows: list[dict[str, Any]] = []
    normalized_metadata: list[dict[str, Any]] = []

    for i, row in chunks_df.iterrows():
        existing_meta = dict(metadata_rows[i])
        embedded_meta = normalize_metadata_cell(row.get("metadata", {}))

        combined_meta = {}
        combined_meta.update(embedded_meta)
        combined_meta.update(existing_meta)

        text = str(row.get("text", "")).strip()

        doc_id = str(
            row.get("doc_id")
            or combined_meta.get("doc_id")
            or f"doc_{i:04d}"
        )

        title = str(
            row.get("title")
            or combined_meta.get("title")
            or doc_id
        )

        source = str(
            row.get("source")
            or combined_meta.get("source")
            or title
        )

        chunk_index = int(
            row.get("chunk_index", combined_meta.get("chunk_index", i))
        )

        content_hash = str(
            row.get("content_hash")
            or combined_meta.get("content_hash")
            or sha256_text(text)
        )

        chunk_id = str(
            row.get("chunk_id")
            or combined_meta.get("chunk_id")
            or f"{doc_id}_{chunk_index:04d}_{content_hash[:12]}"
        )

        source_type = str(
            row.get("source_type")
            or combined_meta.get("source_type")
            or guess_source_type(source, combined_meta)
        )

        char_count = int(row.get("char_count", len(text)))
        token_count = int(row.get("token_estimate", token_estimate(text)))

        chunking_method = str(
            row.get("chunking_method")
            or combined_meta.get("chunking_method")
            or "paragraph_aware_v1"
        )

        sanitized = as_bool(
            row.get("sanitized", combined_meta.get("sanitized", True)),
            default=True,
        )

        origin_pipeline = str(
            row.get("origin_pipeline")
            or combined_meta.get("origin_pipeline")
            or "kaggle_cleaning"
        )

        normalized = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "title": title,
            "source": source,
            "source_type": source_type,
            "chunk_index": chunk_index,
            "text": text,
            "char_count": char_count,
            "token_estimate": token_count,
            "chunking_method": chunking_method,
            "sanitized": sanitized,
            "origin_pipeline": origin_pipeline,
            "content_hash": content_hash,
        }

        normalized_rows.append(normalized)

        meta = dict(combined_meta)
        meta.update({
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "title": title,
            "source": source,
            "source_type": source_type,
            "chunk_index": chunk_index,
            "char_count": char_count,
            "token_estimate": token_count,
            "chunking_method": chunking_method,
            "sanitized": sanitized,
            "origin_pipeline": origin_pipeline,
            "content_hash": content_hash,
        })

        normalized_metadata.append(meta)

    normalized_df = pd.DataFrame(normalized_rows)
    normalized_df = normalized_df[REQUIRED_COLUMNS]

    out_chunks = output_dir / "cleaned_chunks.parquet"
    out_metadata = output_dir / "metadata.jsonl"

    if args.backup:
        backup_file(out_chunks)
        backup_file(out_metadata)

    normalized_df.to_parquet(out_chunks, index=False)
    write_jsonl(out_metadata, normalized_metadata)

    print("OK: output Kaggle berhasil dinormalisasi ke schema K2")
    print(f"Chunks      : {len(normalized_df)}")
    print(f"Output chunk: {out_chunks}")
    print(f"Output meta : {out_metadata}")
    print("Columns:")

    for col in normalized_df.columns:
        print(f"- {col}")


if __name__ == "__main__":
    main()
