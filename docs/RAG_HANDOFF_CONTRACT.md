# RAG HANDOFF CONTRACT — rag-to-kaggle

Dokumen ini menjelaskan kontrak handoff antara `ai-rag-local` dan `rag-to-kaggle`.

## 1. Prinsip utama

`ai-rag-local` mengirim artifact aman ke `rag-to-kaggle`.

`rag-to-kaggle` mengembalikan report, risk label, rekomendasi, dan candidate artifact.

`rag-to-kaggle` tidak melakukan promote ke Chroma utama.

## 2. Input dari `ai-rag-local`

Input yang boleh diterima:

```text
data/incoming/
  approved_chunks.jsonl
  chroma_existing_export.jsonl
  benchmark_queries.jsonl
  baseline_metrics.json
  manifest.json
```

## 3. Manifest wajib

`manifest.json` wajib membawa informasi asal data:

```json
{
  "source_project": "ai-rag-local",
  "export_type": "approved_chunks",
  "schema_version": "rag_jsonl_contract_v1",
  "collection_name": "rag_multilingual_minilm_l12_v2_384",
  "embedding_model": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
  "chunker": "chunking_v2",
  "created_at": "2026-05-09T00:00:00Z"
}
```

## 4. Minimal JSONL input

Minimal:

```json
{
  "doc_id": "...",
  "text": "..."
}
```

Disarankan:

```json
{
  "doc_id": "hash_dokumen_web",
  "title": "Judul Halaman",
  "source": "https://example.com/artikel",
  "source_type": "web",
  "parser": "html_parser_v1",
  "page": null,
  "chunk_index": 0,
  "text": "Isi chunk",
  "metadata": {
    "url": "https://example.com/artikel",
    "domain": "example.com",
    "section_title": "Pendahuluan",
    "section_index": 0,
    "heading_path": "Pendahuluan",
    "char_count": 850,
    "token_estimate": 210,
    "document_hash": "...",
    "chunk_hash": "...",
    "chunker": "chunking_v2"
  }
}
```

## 5. Metadata yang tidak boleh hilang

Metadata berikut harus dipertahankan jika tersedia:

```text
doc_id
title
source
source_type
parser
page
chunk_index
metadata.url
metadata.domain
metadata.section_title
metadata.section_index
metadata.heading_path
metadata.char_count
metadata.token_estimate
metadata.document_hash
metadata.chunk_hash
metadata.chunker
```

## 6. Output kembali ke `ai-rag-local`

Output yang boleh dikembalikan:

```text
reports/
  kaggle_eval_summary.json
  retrieval_eval_by_query.jsonl
  chunk_risk_labels.jsonl
  geometry_audit_summary.json
  recommended_runtime_policy.json
  failed_cases.jsonl
  candidate_chunking_config.json
  candidate_embedding_config.json
```

Candidate artifact boleh dikembalikan, tetapi harus diberi status:

```text
candidate_only
not_promoted
requires_local_compare
```

## 7. Output yang tidak boleh dikembalikan sebagai final

Output berikut tidak boleh dianggap production-ready:

- Chroma collection final;
- centroid sebagai pengganti chunk asli;
- hasil GAC sebagai evidence final;
- parameter embedding baru tanpa local benchmark;
- hasil Kaggle tanpa manifest;
- hasil Kaggle tanpa validation report;
- hasil Kaggle tanpa failed cases.

## 8. Jalur aman

```text
ai-rag-local approved export
  -> rag-to-kaggle normalize
  -> validate schema
  -> optional Kaggle experiment
  -> local embedding/sandbox import
  -> benchmark/report
  -> return report to ai-rag-local
  -> ai-rag-local local compare
  -> ai-rag-local promote gate
```

## 9. Acceptance criteria kontrak

Handoff dianggap valid jika:

1. semua JSONL lolos schema validation;
2. metadata penting tidak hilang;
3. output report menyebut manifest input;
4. failed query dicatat;
5. collection sandbox tidak memakai nama collection utama;
6. tidak ada direct write ke Chroma utama;
7. hasil akhir ditandai sebagai report/candidate, bukan promoted collection.

## 10. Aturan dokumentasi

Perubahan schema input/output harus memperbarui dokumen ini dan `TEST_PLAN.md`. Dalam siklus normal, setiap 9 commit implementasi diikuti commit ke-10 untuk dokumentasi.
