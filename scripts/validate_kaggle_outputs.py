from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Any

import pandas as pd


REQUIRED_FILES = [
    "cleaned_chunks.parquet",
    "metadata.jsonl",
    "retrieval_score.csv",
    "evaluation_report.md",
]

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

ALLOWED_SOURCE_TYPE = {
    "local_file",
    "web",
    "chroma_export",
    "dummy",
    "unknown",
}


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
                raise ValueError(
                    f"metadata.jsonl invalid JSON pada baris {line_no}: {exc}"
                ) from exc

            if not isinstance(row, dict):
                raise ValueError(f"metadata.jsonl baris {line_no} bukan object JSON.")

            rows.append(row)

    return rows


def fail(errors: list[str]) -> None:
    print("FAILED: Kaggle output belum valid untuk schema K2.")
    print("")

    for i, err in enumerate(errors, start=1):
        print(f"{i}. {err}")

    raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "import_dir",
        nargs="?",
        default="data/import",
        help="Folder hasil Kaggle yang akan divalidasi.",
    )

    args = parser.parse_args()

    import_dir = Path(args.import_dir)
    errors: list[str] = []

    if not import_dir.exists():
        fail([f"Folder tidak ditemukan: {import_dir}"])

    for file_name in REQUIRED_FILES:
        path = import_dir / file_name

        if not path.exists():
            errors.append(f"File wajib tidak ditemukan: {file_name}")

    if errors:
        fail(errors)

    chunks_path = import_dir / "cleaned_chunks.parquet"
    metadata_path = import_dir / "metadata.jsonl"

    try:
        chunks_df = pd.read_parquet(chunks_path)
    except Exception as exc:
        errors.append(f"Gagal membaca cleaned_chunks.parquet: {exc}")
        fail(errors)

    try:
        metadata_rows = read_jsonl(metadata_path)
    except Exception as exc:
        errors.append(str(exc))
        fail(errors)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in chunks_df.columns
    ]

    if missing_columns:
        errors.append(
            "Kolom wajib belum ada di cleaned_chunks.parquet: "
            + ", ".join(missing_columns)
        )

    if len(chunks_df) == 0:
        errors.append("cleaned_chunks.parquet kosong.")

    if len(metadata_rows) != len(chunks_df):
        errors.append(
            f"Jumlah baris metadata.jsonl tidak sama dengan chunks: "
            f"metadata={len(metadata_rows)}, chunks={len(chunks_df)}"
        )

    if not errors:
        if chunks_df["chunk_id"].isna().any():
            errors.append("Ada chunk_id kosong.")

        if chunks_df["chunk_id"].astype(str).str.strip().eq("").any():
            errors.append("Ada chunk_id string kosong.")

        if chunks_df["chunk_id"].duplicated().any():
            duplicated = chunks_df[
                chunks_df["chunk_id"].duplicated()
            ]["chunk_id"].tolist()

            errors.append(f"Ada chunk_id duplikat, contoh: {duplicated[:5]}")

        for col in ["doc_id", "source", "text", "content_hash"]:
            if chunks_df[col].isna().any():
                errors.append(f"Ada nilai kosong/NaN pada kolom {col}.")

            if chunks_df[col].astype(str).str.strip().eq("").any():
                errors.append(f"Ada string kosong pada kolom {col}.")

        invalid_source_type = sorted(
            set(chunks_df["source_type"].astype(str)) - ALLOWED_SOURCE_TYPE
        )

        if invalid_source_type:
            errors.append(
                "Ada source_type tidak dikenal: "
                + ", ".join(invalid_source_type)
            )

        if not chunks_df["sanitized"].astype(bool).all():
            errors.append("Ada chunk dengan sanitized != true.")

        if (chunks_df["char_count"].astype(int) <= 0).any():
            errors.append("Ada char_count <= 0.")

        if (chunks_df["token_estimate"].astype(int) <= 0).any():
            errors.append("Ada token_estimate <= 0.")

        for i, meta in enumerate(metadata_rows):
            chunk_id_df = str(chunks_df.iloc[i]["chunk_id"])
            chunk_id_meta = str(meta.get("chunk_id", ""))

            if chunk_id_meta != chunk_id_df:
                errors.append(
                    f"Urutan metadata tidak cocok pada index {i}: "
                    f"parquet={chunk_id_df}, metadata={chunk_id_meta}"
                )
                break

    if errors:
        fail(errors)

    print("OK: Kaggle output valid untuk schema K2.")
    print(f"Folder       : {import_dir}")
    print(f"Total chunks : {len(chunks_df)}")
    print("Columns      :")

    for col in chunks_df.columns:
        print(f"- {col}")


if __name__ == "__main__":
    main()
