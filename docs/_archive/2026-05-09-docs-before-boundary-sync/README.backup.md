# RAG ↔ Kaggle Hook Starter

Starter kit ini dibuat untuk folder:

```text
F:\AI-Models\rag-to-kaggle
```

Fungsinya sebagai **jembatan eksperimen** antara RAG lokal dan Kaggle:

1. sanitasi corpus lokal;
2. export corpus aman ke `JSONL`;
3. proses cleaning, chunking, embedding, dan evaluasi di Kaggle;
4. download hasil Kaggle;
5. import kembali ke ChromaDB lokal;
6. uji retrieval dan RAG dengan Gemini API.

> Kaggle dipakai sebagai lab eksperimen, bukan server produksi.

---

## Struktur

```text
rag-to-kaggle/
├── .env.example
├── requirements.txt
├── data/
│   ├── raw/
│   ├── sanitized/
│   ├── export/
│   └── import/
├── chroma_db/
├── notebooks/
│   └── kaggle_rag_training_lab.ipynb
├── scripts/
│   ├── sanitize_corpus.py
│   ├── export_corpus.py
│   ├── import_kaggle_results.py
│   ├── build_chroma.py
│   ├── test_retrieval.py
│   └── rag_chat.py
├── configs/
│   ├── chunking.yaml
│   ├── embedding.yaml
│   └── retrieval.yaml
├── outputs/
└── docs/
```

---

## 1. Setup Lokal Windows

Buka terminal dari folder project:

```powershell
cd /d F:\AI-Models\rag-to-kaggle
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env`, terutama:

```env
CHROMA_PATH=../rag-lc/chroma_db
COLLECTION_NAME=rag_local_corpus
GEMINI_API_KEY=isi_api_key_gemini_kamu
```

Kalau ChromaDB utama belum ada di `rag-lc`, boleh pakai:

```env
CHROMA_PATH=./chroma_db
```

---

## 2. Alur Cepat

### A. Masukkan corpus aman

Letakkan file `.txt` atau `.md` ke:

```text
data/raw/
```

Jangan masukkan dokumen rahasia, data pribadi, file `.env`, API key, NIK, nomor HP, atau dokumen internal.

### B. Sanitasi dan export corpus

```powershell
python scripts/sanitize_corpus.py
python scripts/export_corpus.py
```

Output:

```text
data/export/corpus_export.jsonl
```

File inilah yang di-upload ke Kaggle Dataset atau Kaggle Notebook.

### C. Jalankan notebook Kaggle

Upload:

```text
data/export/corpus_export.jsonl
notebooks/kaggle_rag_training_lab.ipynb
```

Output dari Kaggle:

```text
cleaned_chunks.parquet
embeddings.npy
metadata.jsonl
retrieval_score.csv
evaluation_report.md
```

Download semua output Kaggle ke:

```text
data/import/
```

### D. Import hasil Kaggle ke ChromaDB lokal

```powershell
python scripts/import_kaggle_results.py
```

### E. Test retrieval lokal

```powershell
python scripts/test_retrieval.py "apa isi utama dokumen ini?"
```

### F. Chat RAG dengan Gemini

```powershell
python scripts/rag_chat.py "jawab berdasarkan konteks: apa ringkasan dokumen ini?"
```

---

## 3. Catatan Model Embedding

Default starter kit memakai:

```text
intfloat/multilingual-e5-small
```

Konvensi embedding:

```text
passage: isi chunk
query: pertanyaan user
```

Gunakan model embedding yang sama di Kaggle dan lokal agar dimensi vektor tidak bentrok.

---

## 4. Batas Aman

- Kaggle bukan backend produksi.
- Jangan menjalankan server publik dari Kaggle.
- Jangan upload `.env`.
- Jangan upload data kantor/internal/rahasia.
- API key cukup di lokal atau Kaggle Secrets, bukan ditulis langsung di notebook.
