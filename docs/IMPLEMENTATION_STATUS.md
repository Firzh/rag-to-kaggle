# IMPLEMENTATION STATUS — rag-to-kaggle

Dokumen ini menjadi sumber status implementasi `rag-to-kaggle`. Tujuannya agar dokumentasi tidak memberi kesan bahwa fitur pending sudah tersedia.

## 1. Posisi project

`rag-to-kaggle` adalah pipeline adapter dan evaluator untuk membawa artifact aman dari RAG lokal menuju Kaggle, menjalankan eksperimen/audit, lalu mengembalikan report atau rekomendasi.

`rag-to-kaggle` bukan runtime RAG utama dan bukan pemilik Chroma utama.

## 2. Implemented

| Kode | Status | Catatan |
|---|---|---|
| K1 | Implemented | Kaggle smoke test |
| K2 | Implemented | Output contract + schema validation |
| K3 | Implemented | Explicit import modes |
| K4 | Implemented | Local retrieval benchmark |
| K5 | Implemented | `ai-rag-local`/`rag-lc` L1 `chunking_v2` handoff integration |

Status K5:

```text
rag-lc L1 chunking_v2
  -> JSONL handoff
  -> normalize_rag_l1_chunks.py
  -> K2-compatible output
  -> validate_kaggle_outputs.py
  -> kaggle_import_pipeline.py --mode local-embedding
  -> rag_kaggle_l1_chunking_sandbox
  -> L1 handoff benchmark
```

K5 dianggap berhasil bila chunk/section yang benar muncul di top-k. Jika top-1 belum selalu tepat, itu dicatat sebagai isu ranking, bukan blocker integrasi.

## 3. Not yet implemented / pending

| Kode | Status | Catatan |
|---|---|---|
| K6 | Planned | L2 HTML Parser Handoff Adapter |
| K7 | Planned | Mini Scraper Staging Adapter |
| K8 | Planned | Metadata-Aware Embedding Text |
| K9 | Planned | Chroma Export Adapter |
| K10 | Planned | Collection Compare |
| K11 | Planned | Promotion Gate handoff report |

## 4. Status batas penting

| Area | Status |
|---|---|
| Kaggle sebagai lab eksperimen | Aktif sebagai prinsip |
| Direct write ke Chroma utama | Tidak boleh |
| Local Chroma sandbox | Boleh untuk import/evaluasi |
| Promote ke Chroma utama | Bukan wewenang `rag-to-kaggle` |
| Report/risk label/rekomendasi parameter | Boleh dikembalikan ke RAG |
| GAC/geometry experiment | Boleh sebagai eksperimen, bukan produksi |

## 5. Status dokumentasi lama

Beberapa dokumen lama masih relevan, tetapi harus dibaca bersama boundary baru:

- `docs/kaggle_output_contract.md`
- `docs/kaggle_import_modes.md`
- `docs/local_retrieval_benchmark.md`
- `docs/rag_l1_chunking_integration.md`
- `docs/security_checklist.md`
- `docs/workflow.md`

Jika dokumen lama menyiratkan import langsung ke Chroma utama, tafsir baru yang berlaku adalah:

```text
Kaggle result -> local sandbox/report -> local compare di ai-rag-local -> promote gate di ai-rag-local
```

## 6. Aturan dokumentasi 9+1 commit

Setiap 9 commit implementasi, commit ke-10 wajib memperbarui dokumentasi ini dan dokumen terkait.

Perubahan berikut wajib didokumentasikan segera tanpa menunggu commit ke-10:

- perubahan kontrak JSONL;
- perubahan schema output Kaggle;
- perubahan jalur import;
- perubahan nama collection sandbox;
- perubahan boundary Chroma utama;
- penambahan promotion-related artifact;
- perubahan mode embedding;
- perubahan benchmark atau acceptance criteria.
