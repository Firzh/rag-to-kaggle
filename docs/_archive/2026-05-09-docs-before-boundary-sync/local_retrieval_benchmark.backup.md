# K4 — Local Retrieval Benchmark

## Tujuan

K4 membuat benchmark retrieval lokal untuk collection hasil pipeline Kaggle.

Benchmark ini dipakai untuk mengecek apakah collection sandbox dapat mengembalikan chunk yang tepat berdasarkan query evaluasi.

## Posisi dalam Pipeline

Alur K4:

Kaggle cleaned chunks
→ local embedding
→ ChromaDB sandbox
→ local retrieval benchmark
→ CSV report
→ Markdown report

## Collection Utama yang Diuji

Default collection:

rag_kaggle_local_embed_sandbox_k3

Collection ini dibuat dari:

- cleaned_chunks.parquet
- metadata.jsonl
- embedding lokal menggunakan FastEmbed

## File Input

Benchmark memakai file:

configs/local_retrieval_eval.jsonl

Setiap baris berisi satu query evaluasi.

Format minimal:

{
  "query": "Apa fungsi Kaggle dalam pipeline RAG lokal?",
  "expected_terms": ["Kaggle", "eksperimen", "chunking"],
  "expected_doc_id": "c12989af53c14ef0",
  "expected_source": "contoh_rag.txt"
}

## File Output

Script benchmark menghasilkan:

outputs/local_retrieval_benchmark.csv
outputs/local_retrieval_report.md

## Metrik Awal

Metrik yang dicatat:

- top1_distance
- hit_expected_doc_top1
- hit_expected_doc_topk
- hit_expected_source_top1
- hit_expected_source_topk
- expected_terms_hit
- expected_terms_total
- expected_terms_ratio

## Catatan

K4 belum mengukur kualitas jawaban LLM. K4 hanya mengukur kualitas retrieval.

Evaluasi jawaban RAG baru dilakukan pada patch berikutnya setelah retrieval benchmark stabil.
