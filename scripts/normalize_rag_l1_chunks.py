from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
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

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_no}: {exc}") from exc

            if not isinstance(row, dict):
                raise ValueError(f"Row at {path}:{line_no} must be a JSON object.")

            rows.append(row)

    if not rows:
        raise ValueError(f"Input file kosong: {path}")

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


def normalize_metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)

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


def as_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value

    if value is None:
        return default

    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "ok"}

    return bool(value)


def guess_source_type(source: str, metadata: dict[str, Any]) -> str:
    source_type = metadata.get("source_type")

    if isinstance(source_type, str) and source_type.strip():
        return source_type.strip()

    source_lower = str(source).lower()

    if source_lower.startswith("http://") or source_lower.startswith("https://"):
        return "web"

    if source_lower.endswith((".txt", ".md", ".pdf", ".docx", ".html", ".htm")):
        return "local_file"

    return "unknown"


def normalize_row(row: dict[str, Any], index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    metadata = normalize_metadata(row.get("metadata", {}))

    text = str(row.get("text", "")).strip()

    if not text:
        raise ValueError(f"Chunk index {index} memiliki text kosong.")

    doc_id = str(
        row.get("doc_id")
        or metadata.get("doc_id")
        or f"doc_{index:04d}"
    ).strip()

    if not doc_id:
        raise ValueError(f"Chunk index {index} memiliki doc_id kosong.")

    title = str(
        row.get("title")
        or metadata.get("title")
        or doc_id
    ).strip()

    source = str(
        row.get("source")
        or metadata.get("source")
        or title
    ).strip()

    if not source:
        raise ValueError(f"Chunk index {index} memiliki source kosong.")

    chunk_index = int(row.get("chunk_index", metadata.get("chunk_index", index)))

    content_hash = str(
        row.get("content_hash")
        or metadata.get("content_hash")
        or metadata.get("chunk_hash")
        or sha256_text(text)
    )

    chunk_id = str(
        row.get("chunk_id")
        or metadata.get("chunk_id")
        or f"{doc_id}_{chunk_index:04d}_{content_hash[:12]}"
    )

    source_type = str(
        row.get("source_type")
        or metadata.get("source_type")
        or guess_source_type(source, metadata)
    )

    char_count = int(row.get("char_count", metadata.get("char_count", len(text))))

    token_count = int(
        row.get("token_estimate", metadata.get("token_estimate", token_estimate(text)))
    )

    chunking_method = str(
        row.get("chunking_method")
        or metadata.get("chunking_method")
        or metadata.get("chunker")
        or "chunking_v2"
    )

    sanitized = as_bool(
        row.get("sanitized", metadata.get("sanitized", True)),
        default=True,
    )

    origin_pipeline = str(
        row.get("origin_pipeline")
        or metadata.get("origin_pipeline")
        or "rag_lc_l1_chunking_v2"
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

    normalized_metadata = dict(metadata)
    normalized_metadata.update({
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

    # Simpan metadata L1 yang umum dipakai chunking_v2.
    for optional_key in [
        "section_title",
        "section_index",
        "heading",
        "heading_path",
        "page",
        "start_char",
        "end_char",
        "overlap_with_previous",
        "parser",
        "parser_version",
        "chunking_version",
        "document_hash",
        "chunk_hash",
        "chunker",
    ]:
        if optional_key in row and optional_key not in normalized_metadata:
            normalized_metadata[optional_key] = row[optional_key]

    return normalized, normalized_metadata


def write_placeholder_retrieval_score(path: Path, total_chunks: int) -> None:
    df = pd.DataFrame([
        {
            "stage": "rag_l1_normalized",
            "total_chunks": total_chunks,
            "note": "Placeholder. Run local retrieval benchmark after Chroma import."
        }
    ])

    df.to_csv(path, index=False)


def write_report(path: Path, *, input_file: Path, total_chunks: int) -> None:
    content = f"""# RAG L1 Chunking Integration Report

## Input

- Input file: `{input_file}`
- Total chunks: {total_chunks}
- Output schema: K2-compatible

## Notes

This output was normalized from rag-lc L1 chunking_v2 handoff.

Next steps:

1. Run validate_kaggle_outputs.py on this output folder.
2. Import using kaggle_import_pipeline.py with local-embedding mode.
3. Run local retrieval benchmark.
"""

    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize rag-lc L1 chunking_v2 JSONL handoff into K2-compatible output."
    )
    parser.add_argument(
        "--input-file",
        default="data/l1_incoming/l1_chunks.jsonl",
        help="JSONL file hasil export L1 dari rag-lc.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/l1_import",
        help="Output folder K2-compatible.",
    )

    args = parser.parse_args()

    input_file = Path(args.input_file)
    output_dir = Path(args.output_dir)

    if not input_file.exists():
        raise FileNotFoundError(f"Input L1 tidak ditemukan: {input_file}")

    output_dir.mkdir(parents=True, exist_ok=True)

    raw_rows = read_jsonl(input_file)

    normalized_rows: list[dict[str, Any]] = []
    metadata_rows: list[dict[str, Any]] = []

    for i, row in enumerate(raw_rows):
        normalized, meta = normalize_row(row, i)
        normalized_rows.append(normalized)
        metadata_rows.append(meta)

    df = pd.DataFrame(normalized_rows)
    df = df[REQUIRED_COLUMNS]

    chunks_path = output_dir / "cleaned_chunks.parquet"
    metadata_path = output_dir / "metadata.jsonl"
    score_path = output_dir / "retrieval_score.csv"
    report_path = output_dir / "evaluation_report.md"

    df.to_parquet(chunks_path, index=False)
    write_jsonl(metadata_path, metadata_rows)
    write_placeholder_retrieval_score(score_path, len(df))
    write_report(report_path, input_file=input_file, total_chunks=len(df))

    print("OK: L1 chunks berhasil dinormalisasi ke schema K2.")
    print(f"Input        : {input_file}")
    print(f"Output dir   : {output_dir}")
    print(f"Total chunks : {len(df)}")
    print(f"Chunks file  : {chunks_path}")
    print(f"Metadata     : {metadata_path}")
    print(f"Report       : {report_path}")


if __name__ == "__main__":
    main()
