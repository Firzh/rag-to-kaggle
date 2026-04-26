from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import chromadb
import pandas as pd
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

            if "query" not in row or not str(row["query"]).strip():
                raise ValueError(f"Row at {path}:{line_no} must contain non-empty query.")

            rows.append(row)

    if not rows:
        raise ValueError(f"Evaluation file is empty: {path}")

    return rows


def normalize_text(text: str) -> str:
    return " ".join(str(text).lower().split())


def expected_terms_score(document_text: str, expected_terms: list[str]) -> tuple[int, int, float, list[str]]:
    if not expected_terms:
        return 0, 0, 0.0, []

    doc = normalize_text(document_text)
    hits: list[str] = []

    for term in expected_terms:
        term_norm = normalize_text(term)

        if term_norm and term_norm in doc:
            hits.append(term)

    total = len(expected_terms)
    ratio = len(hits) / total if total else 0.0

    return len(hits), total, ratio, hits


def any_meta_matches(metas: list[dict[str, Any]], key: str, expected: str | None) -> bool:
    if not expected:
        return False

    expected_norm = str(expected).strip()

    for meta in metas:
        if str(meta.get(key, "")).strip() == expected_norm:
            return True

    return False


def first_meta_matches(meta: dict[str, Any] | None, key: str, expected: str | None) -> bool:
    if not expected or not meta:
        return False

    return str(meta.get(key, "")).strip() == str(expected).strip()


def run_benchmark(
    *,
    eval_rows: list[dict[str, Any]],
    collection,
    embedder: TextEmbedding,
    top_k: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    for idx, item in enumerate(eval_rows, start=1):
        query = str(item["query"]).strip()
        expected_terms = item.get("expected_terms", [])

        if expected_terms is None:
            expected_terms = []

        if not isinstance(expected_terms, list):
            raise ValueError(f"expected_terms must be list for query: {query}")

        expected_doc_id = item.get("expected_doc_id")
        expected_source = item.get("expected_source")

        query_embedding = list(embedder.embed([query]))[0].tolist()

        response = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        ids = response.get("ids", [[]])[0]
        documents = response.get("documents", [[]])[0]
        metadatas = response.get("metadatas", [[]])[0]
        distances = response.get("distances", [[]])[0]

        top1_id = ids[0] if ids else ""
        top1_doc = documents[0] if documents else ""
        top1_meta = metadatas[0] if metadatas else {}
        top1_distance = distances[0] if distances else None

        terms_hit, terms_total, terms_ratio, matched_terms = expected_terms_score(
            top1_doc,
            [str(term) for term in expected_terms],
        )

        hit_doc_top1 = first_meta_matches(top1_meta, "doc_id", expected_doc_id)
        hit_source_top1 = first_meta_matches(top1_meta, "source", expected_source)

        hit_doc_topk = any_meta_matches(metadatas, "doc_id", expected_doc_id)
        hit_source_topk = any_meta_matches(metadatas, "source", expected_source)

        row = {
            "case_no": idx,
            "query": query,
            "top_k": top_k,
            "top1_id": top1_id,
            "top1_distance": top1_distance,
            "top1_doc_id": top1_meta.get("doc_id", "") if top1_meta else "",
            "top1_source": top1_meta.get("source", "") if top1_meta else "",
            "expected_doc_id": expected_doc_id or "",
            "expected_source": expected_source or "",
            "hit_expected_doc_top1": bool(hit_doc_top1),
            "hit_expected_doc_topk": bool(hit_doc_topk),
            "hit_expected_source_top1": bool(hit_source_top1),
            "hit_expected_source_topk": bool(hit_source_topk),
            "expected_terms_hit": terms_hit,
            "expected_terms_total": terms_total,
            "expected_terms_ratio": round(terms_ratio, 4),
            "matched_terms": json.dumps(matched_terms, ensure_ascii=False),
            "top1_preview": top1_doc[:300].replace("\n", " "),
        }

        results.append(row)

    return results


def bool_rate(values: list[bool]) -> float:
    if not values:
        return 0.0

    return sum(1 for value in values if value) / len(values)


def write_markdown_report(
    *,
    path: Path,
    rows: list[dict[str, Any]],
    collection_name: str,
    embedding_model: str,
    top_k: int,
) -> None:
    total = len(rows)

    doc_top1 = bool_rate([bool(row["hit_expected_doc_top1"]) for row in rows])
    doc_topk = bool_rate([bool(row["hit_expected_doc_topk"]) for row in rows])
    source_top1 = bool_rate([bool(row["hit_expected_source_top1"]) for row in rows])
    source_topk = bool_rate([bool(row["hit_expected_source_topk"]) for row in rows])

    avg_terms_ratio = (
        sum(float(row["expected_terms_ratio"]) for row in rows) / total
        if total
        else 0.0
    )

    lines = [
        "# Local Retrieval Benchmark Report",
        "",
        "## Summary",
        "",
        f"- Collection: `{collection_name}`",
        f"- Embedding model: `{embedding_model}`",
        f"- Top-K: {top_k}",
        f"- Total cases: {total}",
        f"- Hit expected doc @1: {doc_top1:.2f}",
        f"- Hit expected doc @{top_k}: {doc_topk:.2f}",
        f"- Hit expected source @1: {source_top1:.2f}",
        f"- Hit expected source @{top_k}: {source_topk:.2f}",
        f"- Average expected terms ratio @1: {avg_terms_ratio:.2f}",
        "",
        "## Cases",
        "",
    ]

    for row in rows:
        lines.extend([
            f"### Case {row['case_no']}",
            "",
            f"- Query: {row['query']}",
            f"- Top1 ID: {row['top1_id']}",
            f"- Top1 distance: {row['top1_distance']}",
            f"- Expected doc @1: {row['hit_expected_doc_top1']}",
            f"- Expected source @1: {row['hit_expected_source_top1']}",
            f"- Expected terms ratio @1: {row['expected_terms_ratio']}",
            f"- Matched terms: {row['matched_terms']}",
            "",
            "Preview:",
            "",
            row["top1_preview"],
            "",
        ])

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run local retrieval benchmark for Kaggle local-embedding Chroma collection."
    )
    parser.add_argument(
        "--eval-file",
        default="configs/local_retrieval_eval.jsonl",
        help="JSONL file berisi query evaluasi.",
    )
    parser.add_argument(
        "--collection",
        default=None,
        help="Nama collection. Default dari LOCAL_EMBED_COLLECTION atau K4 default.",
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
        help="Model embedding. Default dari LOCAL_EMBED_MODEL atau MiniLM.",
    )
    parser.add_argument(
        "--chroma-path",
        default=None,
        help="Path ChromaDB. Default dari CHROMA_PATH atau ./chroma_db.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Jumlah hasil retrieval.",
    )
    parser.add_argument(
        "--out-csv",
        default="outputs/local_retrieval_benchmark.csv",
        help="Output CSV.",
    )
    parser.add_argument(
        "--out-md",
        default="outputs/local_retrieval_report.md",
        help="Output Markdown report.",
    )

    args = parser.parse_args()

    eval_file = resolve_path(args.eval_file)
    out_csv = resolve_path(args.out_csv)
    out_md = resolve_path(args.out_md)

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

    eval_rows = read_jsonl(eval_file)

    print(f"Eval file   : {eval_file}")
    print(f"Model       : {embedding_model}")
    print(f"Collection  : {collection_name}")
    print(f"Chroma path : {chroma_path}")
    print(f"Top-K       : {args.top_k}")

    embedder = TextEmbedding(model_name=embedding_model)

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    rows = run_benchmark(
        eval_rows=eval_rows,
        collection=collection,
        embedder=embedder,
        top_k=args.top_k,
    )

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(rows)
    df.to_csv(out_csv, index=False)

    write_markdown_report(
        path=out_md,
        rows=rows,
        collection_name=collection_name,
        embedding_model=embedding_model,
        top_k=args.top_k,
    )

    print("")
    print("OK: local retrieval benchmark selesai.")
    print(f"CSV report : {out_csv}")
    print(f"MD report  : {out_md}")

    print("")
    print("Summary:")
    print(df[[
        "case_no",
        "hit_expected_doc_top1",
        "hit_expected_source_top1",
        "expected_terms_ratio",
        "top1_distance",
    ]])


if __name__ == "__main__":
    main()
