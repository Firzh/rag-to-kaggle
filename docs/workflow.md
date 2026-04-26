# Workflow RAG Lokal ↔ Kaggle

## Tahap 1 — Lokal

1. Simpan file aman ke `data/raw/`.
2. Jalankan `scripts/sanitize_corpus.py`.
3. Jalankan `scripts/export_corpus.py`.
4. Upload `data/export/corpus_export.jsonl` ke Kaggle.

## Tahap 2 — Kaggle

1. Baca `corpus_export.jsonl`.
2. Bersihkan teks.
3. Pecah menjadi chunk.
4. Buat embedding batch.
5. Simpan:
   - `cleaned_chunks.parquet`
   - `embeddings.npy`
   - `metadata.jsonl`
   - `retrieval_score.csv`
   - `evaluation_report.md`

## Tahap 3 — Lokal

1. Download output Kaggle ke `data/import/`.
2. Jalankan `scripts/import_kaggle_results.py`.
3. Jalankan `scripts/test_retrieval.py`.
4. Jalankan `scripts/rag_chat.py` untuk answer generation dengan Gemini.
