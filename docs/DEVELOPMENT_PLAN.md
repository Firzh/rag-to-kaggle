# DEVELOPMENT PLAN — rag-to-kaggle

Tanggal update: 2026-05-09
Target repo: `Firzh/rag-to-kaggle`

Dokumen ini menggantikan rencana lama sebagai source of truth pengembangan jangka pendek. Jika masih ada file `DEVELOPMENT_PLANT.md`, file tersebut dianggap legacy/archived setelah isi pentingnya dipindahkan ke sini.

## 1. Prinsip pengembangan

1. `rag-to-kaggle` adalah pipeline adapter dan evaluator.
2. `rag-to-kaggle` bukan pemilik Chroma utama.
3. Semua output harus masuk sandbox/report terlebih dahulu.
4. Promote hanya boleh dilakukan di `ai-rag-local` setelah local compare dan regression.
5. Semua perubahan schema harus punya test.
6. Setiap 9 commit implementasi, commit ke-10 wajib dokumentasi.

## 2. Status saat ini

Implemented:

```text
K1 — Kaggle smoke test
K2 — Kaggle output contract + schema validation
K3 — explicit import modes
K4 — local retrieval benchmark
K5 — rag-lc / ai-rag-local L1 chunking_v2 handoff integration
```

Pending:

```text
K6 — L2 HTML Parser Handoff Adapter
K7 — Mini Scraper Staging Adapter
K8 — Metadata-Aware Embedding Text
K9 — Chroma Export Adapter
K10 — Collection Compare
K11 — Promotion Gate Handoff Report
```

## 3. K6 — L2 HTML Parser Handoff Adapter

### Tujuan

Menerima output `ai-rag-local` dari parser HTML + chunking, lalu menormalisasi menjadi output K2-compatible.

### Input

```text
data/l2_html_incoming/html_chunks.jsonl
```

### Output

```text
data/l2_html_import/cleaned_chunks.parquet
data/l2_html_import/metadata.jsonl
data/l2_html_import/retrieval_score.csv
data/l2_html_import/evaluation_report.md
```

### Collection sandbox

```text
rag_kaggle_l2_html_sandbox
```

### File rencana

```text
docs/rag_l2_html_handoff.md
configs/rag_l2_html_schema.json
configs/local_retrieval_eval_html.jsonl
scripts/normalize_rag_l2_html.py
```

### Acceptance criteria

1. `normalize_rag_l2_html.py` bisa membaca `html_chunks.jsonl`.
2. Output lolos `validate_kaggle_outputs.py`.
3. `source_type = web` tetap terbawa.
4. metadata `url`, `domain`, `parser`, `section_title`, `heading_path`, dan `chunk_hash` tidak hilang.
5. Import `local-embedding` ke `rag_kaggle_l2_html_sandbox` berhasil.
6. Benchmark HTML retrieval menghasilkan CSV dan MD report.
7. Tidak ada write ke Chroma utama.

## 4. K7 — Mini Scraper Staging Adapter

### Tujuan

Menyambungkan output mini scraper ke pipeline staging. Mini scraper belum boleh langsung masuk Chroma utama.

### Alur

```text
mini scraper
  -> web_raw
  -> web_parsed
  -> web_sanitized
  -> web_export_for_kaggle.jsonl
  -> rag-to-kaggle normalize
  -> validate
  -> local embedding
  -> Chroma web sandbox
  -> benchmark
```

### Folder rencana

```text
data/web_staging/raw/
data/web_staging/parsed/
data/web_staging/sanitized/
data/web_staging/quarantine/
data/web_staging/export/
registry/source_registry.jsonl
registry/crawl_log.jsonl
```

### Acceptance criteria

1. Setiap source punya status lifecycle.
2. Data rahasia dan `.env` tidak ikut export.
3. Quarantine berjalan untuk parser warning.
4. Output tetap K2-compatible.
5. Tidak ada direct import ke Chroma utama.

## 5. K8 — Metadata-Aware Embedding Text

### Tujuan

Menguji apakah embedding text yang menyertakan metadata ringan meningkatkan retrieval.

### Kandidat format

```text
title: ...
source: ...
section: ...
content: ...
```

### Trade-off

Benefit: query yang menyebut judul, section, atau sumber lebih mudah cocok.

Risiko: metadata bisa mendominasi embedding dan membuat chunk dengan konten berbeda tampak terlalu dekat.

### Acceptance criteria

1. Ada benchmark baseline vs metadata-aware.
2. Tidak boleh menjadi default tanpa local regression.
3. Metadata tidak boleh mengganti teks asli.
4. Query angka/nama/tanggal harus diuji khusus.

## 6. K9 — Chroma Export Adapter

### Tujuan

Membaca export Chroma existing dari `ai-rag-local` untuk audit dan compare.

### Batas

Adapter ini hanya membaca dan mengubah format untuk evaluasi. Ia tidak boleh melakukan promote.

### Acceptance criteria

1. Bisa membaca JSONL export Chroma.
2. Validasi dimensi embedding jika tersedia.
3. Metadata collection dan model embedding masuk manifest.
4. Output compare-ready.

## 7. K10 — Collection Compare

### Tujuan

Membandingkan baseline vs candidate/sandbox collection.

### Metrik minimal

```text
recall@k
MRR
source match
metadata preservation
failed query count
score distribution
latency smoke
```

### Output

```text
reports/collection_compare_summary.json
reports/collection_compare_by_query.jsonl
reports/failed_queries.jsonl
reports/recommendation.md
```

### Batas

K10 hanya menghasilkan report. Keputusan final tetap di `ai-rag-local`.

## 8. K11 — Promotion Gate Handoff Report

### Tujuan

Membuat report yang bisa dibaca `ai-rag-local` sebagai bahan promote gate.

### Output

```text
reports/promotion_handoff_report.json
reports/promotion_handoff_report.md
```

### Status yang diizinkan

```text
pass_for_local_review
blocked
needs_more_tests
regression_detected
metadata_risk
```

Tidak boleh ada status `promoted`.

## 9. Runtime guard bukan scope utama

Parser Guard, Graph Guard, Compressor Guard, dan Evidence Sufficiency Gate adalah scope utama `ai-rag-local`. `rag-to-kaggle` hanya boleh menguji dan memberi report terkait guard tersebut.

## 10. Dokumentasi 9+1 commit

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumentasi.

Dokumen minimal yang dicek pada commit dokumentasi:

- `IMPLEMENTATION_STATUS.md`
- `DEVELOPMENT_PLAN.md`
- `KAGGLE_BOUNDARY.md`
- `RAG_HANDOFF_CONTRACT.md`
- `PIPELINE_SCOPE.md`
- `TEST_PLAN.md`
- `README.md`
