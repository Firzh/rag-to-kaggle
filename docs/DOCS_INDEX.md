# DOCS INDEX — rag-to-kaggle

Dokumen ini menjadi indeks dokumentasi teknis untuk `rag-to-kaggle`.

`README.md` cukup berisi gambaran cepat. Detail status, boundary, handoff, pipeline, dan test dipisahkan agar dokumentasi tidak bercampur dengan instruksi penggunaan harian.

## Dokumen wajib

| Dokumen | Fungsi |
|---|---|
| `IMPLEMENTATION_STATUS.md` | Sumber status fitur yang sudah dan belum selesai |
| `DEVELOPMENT_PLAN.md` | Rencana pengembangan K6 dan seterusnya |
| `KAGGLE_BOUNDARY.md` | Batas scope Kaggle sebagai pipeline eksperimen |
| `RAG_HANDOFF_CONTRACT.md` | Kontrak input/output antara `ai-rag-local` dan `rag-to-kaggle` |
| `PIPELINE_SCOPE.md` | Batas pipeline lokal, Kaggle, sandbox, report, dan promote |
| `TEST_PLAN.md` | Test plan untuk adapter, schema, benchmark, dan handoff |
| `DOCS_MAINTENANCE_POLICY.md` | Aturan update dokumentasi, termasuk aturan 9+1 commit |
| `DOCS_MIGRATION_PLAN.md` | Catatan migrasi dari struktur dokumentasi lama ke baru |

## Dokumen lama yang tetap relevan

Dokumen berikut tetap boleh dipertahankan sebagai catatan teknis spesifik:

| Dokumen lama | Status |
|---|---|
| `docs/kaggle_output_contract.md` | Tetap relevan sebagai kontrak output K2 |
| `docs/kaggle_import_modes.md` | Tetap relevan untuk mode import, tetapi harus dibaca bersama boundary baru |
| `docs/local_retrieval_benchmark.md` | Tetap relevan untuk benchmark lokal |
| `docs/rag_l1_chunking_integration.md` | Tetap relevan untuk K5 L1 handoff |
| `docs/security_checklist.md` | Tetap relevan dan harus diperluas jika ada data sensitif baru |
| `docs/workflow.md` | Tetap relevan sebagai catatan workflow lama |
| `docs/api_tutorial_notes.md` | Opsional; bukan source of truth boundary |

## Prinsip navigasi

1. Gunakan `IMPLEMENTATION_STATUS.md` untuk melihat apakah fitur sudah ada.
2. Gunakan `DEVELOPMENT_PLAN.md` untuk melihat pekerjaan berikutnya.
3. Gunakan `KAGGLE_BOUNDARY.md` dan `RAG_HANDOFF_CONTRACT.md` sebelum mengubah jalur data.
4. Gunakan `TEST_PLAN.md` sebelum merge patch pipeline.
5. Gunakan `DOCS_MAINTENANCE_POLICY.md` untuk memastikan commit dokumentasi tidak tertinggal.
