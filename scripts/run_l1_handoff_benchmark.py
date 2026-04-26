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
DEFAULT_COLLECTION = "rag_kaggle_l1_chunking_sandbox"


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path)

    if not path.is_absolute():
        path = (PROJECT_DIR / path).resolve()

    return path


def getenv(key: str, default: str) -> str:
    value = os.getenv(key)

    if value is None or value.strip() == "":
        return default

    return value.strip()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()

            if not line:
                continue

            row = json.loads(line)

            if not isinstance(row, dict):
                raise ValueError(f"Row {line_no} must be JSON object.")

            if not str(row.get("query", "")).strip():
                raise ValueError(f"Row {line_no} missing query.")

            rows.append(row)

    if not rows:
        raise ValueError(f"Eval file kosong: {path}")

    return rows


def norm(value: Any) -> str:
    return " ".join(str(value).lower().split())


def term_score(text: str, terms: list[str]) -> tuple[int, int, float, list[str]]:
    if not terms:
        return 0, 0, 0.0, []

    text_norm = norm(text)
    hits = []

    for term in terms:
        if norm(term) in text_norm:
            hits.append(str(term))

    total = len(terms)
    ratio = len(hits) / total if total else 0.0

    return len(hits), total, ratio, hits


def meta_equals(meta: dict[str, Any], key: str, expected: Any) -> bool:
    if expected is None:
        return False

    return str(meta.get(key, "")).strip() == str(expected).strip()


def any_meta_equals(metas: list[dict[str, Any]], key: str, expected: Any) -> bool:
    if expected is None:
        return False

    return any(meta_equals(meta, key, expected) for meta in metas)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark L1 handoff retrieval at chunk/section level."
    )
    parser.add_argument(
        "--eval-file",
        default="configs/local_retrieval_eval_l1.jsonl",
    )
    parser.add_argument(
        "--collection",
        default=None,
    )
    parser.add_argument(
        "--embedding-model",
        default=None,
    )
    parser.add_argument(
        "--chroma-path",
        default=None,
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--out-csv",
        default="outputs/l1_handoff_benchmark.csv",
    )
    parser.add_argument(
        "--out-md",
        default="outputs/l1_handoff_report.md",
    )

    args = parser.parse_args()

    eval_file = resolve_path(args.eval_file)
    out_csv = resolve_path(args.out_csv)
    out_md = resolve_path(args.out_md)

    collection_name = args.collection or DEFAULT_COLLECTION
    embedding_model = args.embedding_model or os.getenv("LOCAL_EMBED_MODEL") or DEFAULT_MODEL
    chroma_path = resolve_path(args.chroma_path or getenv("CHROMA_PATH", "./chroma_db"))

    eval_rows = read_jsonl(eval_file)

    print(f"Eval file   : {eval_file}")
    print(f"Collection  : {collection_name}")
    print(f"Model       : {embedding_model}")
    print(f"Top-K       : {args.top_k}")

    embedder = TextEmbedding(model_name=embedding_model)

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    rows = []

    for i, item in enumerate(eval_rows, start=1):
        query = str(item["query"]).strip()
        expected_terms = [str(x) for x in item.get("expected_terms", [])]

        expected_doc_id = item.get("expected_doc_id")
        expected_source = item.get("expected_source")
        expected_chunk_index = item.get("expected_chunk_index")
        expected_section_title = item.get("expected_section_title")

        q_emb = list(embedder.embed([query]))[0].tolist()

        result = collection.query(
            query_embeddings=[q_emb],
            n_results=args.top_k,
            include=["documents", "metadatas", "distances"],
        )

        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]

        top1_id = ids[0] if ids else ""
        top1_doc = docs[0] if docs else ""
        top1_meta = metas[0] if metas else {}
        top1_distance = distances[0] if distances else None

        top1_terms_hit, top1_terms_total, top1_terms_ratio, top1_matched_terms = term_score(
            top1_doc,
            expected_terms,
        )

        topk_text = "\n".join(docs)
        topk_terms_hit, topk_terms_total, topk_terms_ratio, topk_matched_terms = term_score(
            topk_text,
            expected_terms,
        )

        row = {
            "case_no": i,
            "query": query,
            "top_k": args.top_k,
            "top1_id": top1_id,
            "top1_distance": top1_distance,
            "expected_doc_id": expected_doc_id or "",
            "expected_source": expected_source or "",
            "expected_chunk_index": "" if expected_chunk_index is None else expected_chunk_index,
            "expected_section_title": expected_section_title or "",
            "top1_doc_id": top1_meta.get("doc_id", ""),
            "top1_source": top1_meta.get("source", ""),
            "top1_chunk_index": top1_meta.get("chunk_index", ""),
            "top1_section_title": top1_meta.get("section_title", ""),
            "hit_doc_top1": meta_equals(top1_meta, "doc_id", expected_doc_id),
            "hit_doc_topk": any_meta_equals(metas, "doc_id", expected_doc_id),
            "hit_source_top1": meta_equals(top1_meta, "source", expected_source),
            "hit_source_topk": any_meta_equals(metas, "source", expected_source),
            "hit_chunk_index_top1": meta_equals(top1_meta, "chunk_index", expected_chunk_index),
            "hit_chunk_index_topk": any_meta_equals(metas, "chunk_index", expected_chunk_index),
            "hit_section_title_top1": meta_equals(top1_meta, "section_title", expected_section_title),
            "hit_section_title_topk": any_meta_equals(metas, "section_title", expected_section_title),
            "expected_terms_ratio_top1": round(top1_terms_ratio, 4),
            "expected_terms_ratio_topk": round(topk_terms_ratio, 4),
            "matched_terms_top1": json.dumps(top1_matched_terms, ensure_ascii=False),
            "matched_terms_topk": json.dumps(topk_matched_terms, ensure_ascii=False),
            "top1_preview": top1_doc[:300].replace("\n", " "),
        }

        rows.append(row)

    df = pd.DataFrame(rows)

    out_csv.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(out_csv, index=False)

    total = len(df)
    section_top1 = df["hit_section_title_top1"].mean() if total else 0
    section_topk = df["hit_section_title_topk"].mean() if total else 0
    chunk_top1 = df["hit_chunk_index_top1"].mean() if total else 0
    chunk_topk = df["hit_chunk_index_topk"].mean() if total else 0
    term_top1 = df["expected_terms_ratio_top1"].mean() if total else 0
    term_topk = df["expected_terms_ratio_topk"].mean() if total else 0

    lines = [
        "# L1 Handoff Retrieval Benchmark",
        "",
        "## Summary",
        "",
        f"- Collection: `{collection_name}`",
        f"- Embedding model: `{embedding_model}`",
        f"- Top-K: {args.top_k}",
        f"- Total cases: {total}",
        f"- Hit section @1: {section_top1:.2f}",
        f"- Hit section @{args.top_k}: {section_topk:.2f}",
        f"- Hit chunk index @1: {chunk_top1:.2f}",
        f"- Hit chunk index @{args.top_k}: {chunk_topk:.2f}",
        f"- Expected terms ratio @1: {term_top1:.2f}",
        f"- Expected terms ratio @{args.top_k}: {term_topk:.2f}",
        "",
        "## Cases",
        "",
    ]

    for _, row in df.iterrows():
        lines.extend([
            f"### Case {row['case_no']}",
            "",
            f"- Query: {row['query']}",
            f"- Top1 ID: {row['top1_id']}",
            f"- Top1 section: {row['top1_section_title']}",
            f"- Expected section: {row['expected_section_title']}",
            f"- Hit section @1: {row['hit_section_title_top1']}",
            f"- Hit section @{args.top_k}: {row['hit_section_title_topk']}",
            f"- Terms ratio @1: {row['expected_terms_ratio_top1']}",
            f"- Terms ratio @{args.top_k}: {row['expected_terms_ratio_topk']}",
            "",
            "Preview:",
            "",
            str(row["top1_preview"]),
            "",
        ])

    out_md.write_text("\n".join(lines), encoding="utf-8")

    print("")
    print("OK: L1 handoff benchmark selesai.")
    print(f"CSV report : {out_csv}")
    print(f"MD report  : {out_md}")
    print("")
    print(df[[
        "case_no",
        "hit_section_title_top1",
        "hit_section_title_topk",
        "hit_chunk_index_top1",
        "hit_chunk_index_topk",
        "expected_terms_ratio_top1",
        "expected_terms_ratio_topk",
    ]])


if __name__ == "__main__":
    main()
