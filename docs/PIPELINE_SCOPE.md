# PIPELINE SCOPE — rag-to-kaggle

Dokumen ini merinci batas pipeline `rag-to-kaggle` agar tidak melebar menjadi runtime RAG utama.

## 1. Pipeline utama

Scope `rag-to-kaggle`:

```text
receive JSONL/manifest
  -> normalize
  -> validate
  -> optional cleaning/chunking experiment
  -> optional embedding experiment
  -> sandbox import
  -> retrieval benchmark
  -> report generation
  -> return recommendation
```

## 2. Batas sandbox

Sandbox boleh dibuat untuk:

- validasi import;
- benchmark retrieval;
- compare kandidat;
- smoke test embedding;
- eksperimen chunking.

Sandbox tidak boleh:

- menggantikan Chroma utama;
- memakai nama collection produksi;
- dipromosikan tanpa `ai-rag-local`;
- menjadi sumber jawaban final.

## 3. Import mode

Import mode harus eksplisit.

| Mode | Status | Catatan |
|---|---|---|
| `validate-only` | Aman | Hanya validasi schema |
| `local-embedding` | Aman untuk sandbox | Embedding lokal, collection sandbox |
| `kaggle-output` | Perlu gate | Harus ada manifest dan validation report |
| `main-chroma` | Dilarang | Tidak boleh direct write ke Chroma utama |

## 4. Scope K6–K11

| Kode | Scope | Batas |
|---|---|---|
| K6 | L2 HTML Parser Handoff Adapter | Terima output parser/chunking dari RAG, bukan crawling mandiri penuh |
| K7 | Mini Scraper Staging Adapter | Staging saja, bukan direct Chroma |
| K8 | Metadata-Aware Embedding Text | Eksperimen text construction, bukan default produksi otomatis |
| K9 | Chroma Export Adapter | Membaca export, bukan promote |
| K10 | Collection Compare | Compare/report, bukan keputusan final |
| K11 | Promotion Gate Handoff Report | Memberi bahan keputusan, bukan melakukan promote |

## 5. Larangan scope creep

Jangan menambahkan fitur berikut ke `rag-to-kaggle` tanpa dokumen scope baru:

- RAG chat production;
- automatic promotion;
- direct Chroma main write;
- crawler produksi;
- secret management sebagai fitur utama;
- LLM answer generation produksi;
- long-running server;
- background daemon yang mengubah data RAG.

## 6. Trade-off pipeline

| Pilihan | Benefit | Trade-off |
|---|---|---|
| Sandbox-only import | Aman untuk Chroma utama | Butuh step compare tambahan |
| Report-only return | Boundary jelas | Tidak otomatis memperbaiki RAG |
| Metadata lengkap | Retrieval lebih bisa diaudit | File lebih besar dan validasi lebih ketat |
| Local regression wajib | Mengurangi risiko breakage | Siklus dev lebih lambat |
| Kaggle untuk eksperimen besar | Beban lokal lebih ringan | Hasil tidak boleh dipercaya tanpa re-test lokal |

## 7. Output classification

Setiap output harus diberi salah satu status:

```text
report_only
candidate_only
sandbox_only
requires_local_compare
blocked_for_promotion
```

Tidak boleh ada output dengan status `production_ready` dari `rag-to-kaggle`.
