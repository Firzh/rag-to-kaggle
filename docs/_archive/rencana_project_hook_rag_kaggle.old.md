# Rencana Project Hook RAG Lokal ↔ Kaggle

## 1. Tujuan Project

Project kecil ini dibuat untuk menghubungkan sistem **RAG lokal** dengan **Kaggle sebagai AI/RAG Training Lab**. Fokus utamanya bukan menjadikan Kaggle sebagai server produksi, tetapi sebagai tempat latihan untuk:

1. membersihkan corpus;
2. menguji strategi chunking;
3. membuat embedding batch;
4. melatih komponen kecil seperti embedding model atau reranker;
5. mengevaluasi kualitas retrieval;
6. mengembalikan hasil eksperimen ke ChromaDB lokal.

Dengan pendekatan ini, ChromaDB lokal tetap menjadi pusat penyimpanan corpus dan vector database, sedangkan Kaggle berfungsi sebagai tempat komputasi sementara untuk eksperimen dan pengembangan.

---

## 2. Prinsip Penggunaan

Kaggle dipakai sebagai laboratorium pembelajaran, bukan sebagai backend permanen. Prinsip yang wajib dijaga:

- Jangan memakai Kaggle untuk aplikasi produksi.
- Jangan menjalankan server/API publik dari Kaggle.
- Jangan mengunggah dokumen rahasia, data pribadi, data kantor internal, NIK, nomor telepon, alamat, data warga, atau dokumen sensitif.
- Gunakan data publik, dummy, atau corpus yang sudah disanitasi.
- Matikan GPU saat tidak dibutuhkan.
- Debug kode di CPU terlebih dahulu.
- Gunakan GPU hanya untuk embedding batch, training ringan, atau inference berat.
- Simpan checkpoint agar training bisa dilanjutkan tanpa mengulang dari awal.
- Jangan menggunakan banyak akun untuk melewati limit.

---

## 3. Arsitektur Sederhana

```text
Local PC
├── Corpus asli
├── ChromaDB utama
├── Aplikasi RAG lokal
├── Script export corpus
└── Script import hasil Kaggle

        │
        │ export data aman
        ▼

Kaggle Notebook
├── Cleaning
├── Chunking experiment
├── Embedding batch
├── Reranker training/evaluation
├── Retrieval benchmark
└── Export hasil eksperimen

        │
        │ download hasil
        ▼

Local PC
├── Import cleaned chunks
├── Import embeddings
├── Update ChromaDB
├── Jalankan retrieval test
└── Integrasi dengan LLM API
```

---

## 4. Pembagian Peran Komponen

| Komponen | Peran |
|---|---|
| Local PC | Tempat corpus utama, ChromaDB, aplikasi RAG, dan kontrol project |
| Kaggle | Tempat eksperimen, training ringan, embedding batch, dan evaluasi |
| ChromaDB | Vector database lokal untuk menyimpan chunks dan embeddings |
| NVIDIA NIM | Kandidat API LLM gratis/trial untuk answer generation |
| Gemini API | Cadangan API free tier untuk inference |
| Local model | Fallback offline dan sarana pembelajaran teknis |

---

## 5. Struktur Folder Project

```text
rag-kaggle-hook/
├── README.md
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
│   ├── export_corpus.py
│   ├── sanitize_corpus.py
│   ├── import_kaggle_results.py
│   ├── build_chroma.py
│   ├── test_retrieval.py
│   └── rag_chat.py
├── configs/
│   ├── chunking.yaml
│   ├── embedding.yaml
│   └── retrieval.yaml
├── outputs/
│   ├── cleaned_chunks.parquet
│   ├── embeddings.npy
│   ├── metadata.jsonl
│   ├── retrieval_score.csv
│   └── evaluation_report.md
└── docs/
    ├── workflow.md
    ├── security_checklist.md
    └── api_tutorial_notes.md
```

---

## 6. Format Data Antara Lokal dan Kaggle

### 6.1 Export Corpus dari Lokal

Gunakan format `JSONL` agar mudah diproses di Kaggle.

Contoh `corpus_export.jsonl`:

```json
{"doc_id":"doc_001","title":"Contoh Dokumen","source":"local","text":"Isi dokumen yang sudah aman untuk diproses.","metadata":{"category":"public","year":2026}}
{"doc_id":"doc_002","title":"Contoh Lain","source":"local","text":"Teks lain yang sudah disanitasi.","metadata":{"category":"dummy","year":2026}}
```

### 6.2 Output dari Kaggle

Output utama dari Kaggle sebaiknya berupa:

```text
cleaned_chunks.parquet
embeddings.npy
metadata.jsonl
retrieval_score.csv
evaluation_report.md
adapter_lora/            # opsional jika ada fine-tuning
reranker_model/          # opsional jika ada reranker kecil
```

---

## 7. Workflow Utama

## Tahap A — Lokal

1. Kumpulkan corpus lokal.
2. Pisahkan dokumen aman dan dokumen sensitif.
3. Sanitasi data.
4. Export corpus aman ke `data/export/corpus_export.jsonl`.
5. Upload file tersebut ke Kaggle Dataset atau langsung ke Kaggle Notebook.

## Tahap B — Kaggle

1. Load `corpus_export.jsonl`.
2. Bersihkan teks.
3. Uji strategi chunking.
4. Buat embedding batch.
5. Jalankan evaluasi retrieval.
6. Opsional: latih reranker kecil.
7. Export hasil eksperimen.

## Tahap C — Kembali ke Lokal

1. Download hasil dari Kaggle.
2. Simpan ke folder `data/import/`.
3. Import chunks dan embeddings ke ChromaDB.
4. Jalankan retrieval test lokal.
5. Uji dengan LLM API seperti NVIDIA NIM atau Gemini.
6. Catat hasil evaluasi.

---

## 8. Rencana Penggunaan Harian 2–3 Jam

### Hari 1 — Setup dan Sanitasi Corpus

Target:

- membuat struktur project;
- menyiapkan `.env`;
- membuat script sanitasi;
- membuat corpus dummy/publik;
- memastikan tidak ada data sensitif yang ikut ter-export.

Output:

```text
data/sanitized/
data/export/corpus_export.jsonl
docs/security_checklist.md
```

### Hari 2 — Chunking Experiment

Target:

- mencoba beberapa ukuran chunk;
- membandingkan chunk size 300, 500, 800, dan 1000 token;
- menambahkan metadata seperti `doc_id`, `section`, `page`, dan `source`.

Output:

```text
outputs/cleaned_chunks.parquet
configs/chunking.yaml
```

### Hari 3 — Embedding Batch

Target:

- membuat embedding untuk semua chunk;
- menyimpan embedding dalam format `.npy`;
- menyimpan metadata dalam format `.jsonl`.

Output:

```text
outputs/embeddings.npy
outputs/metadata.jsonl
```

### Hari 4 — Import ke ChromaDB Lokal

Target:

- membuat atau update ChromaDB lokal;
- memasukkan chunks, metadata, dan embeddings;
- memastikan query dasar berjalan.

Output:

```text
chroma_db/
scripts/build_chroma.py
scripts/test_retrieval.py
```

### Hari 5 — Evaluasi Retrieval

Target:

- membuat 50–100 pertanyaan evaluasi;
- mengukur apakah jawaban muncul di top-3 atau top-5 retrieval;
- mencatat query yang gagal.

Output:

```text
outputs/retrieval_score.csv
outputs/evaluation_report.md
```

### Hari 6 — Reranker atau Fine-Tuning Ringan

Target:

- mencoba reranker kecil;
- membandingkan hasil retrieval sebelum dan sesudah reranking;
- tidak wajib fine-tuning LLM besar.

Output:

```text
outputs/rerank_score.csv
outputs/evaluation_report.md
```

### Hari 7 — Integrasi dengan API LLM

Target:

- menghubungkan retrieval lokal dengan model API;
- mencoba NVIDIA NIM Free Endpoint;
- menyiapkan cadangan Gemini API;
- membuat script `rag_chat.py`.

Output:

```text
scripts/rag_chat.py
docs/api_tutorial_notes.md
```

---

## 9. Fokus Eksperimen yang Paling Bernilai

Prioritas eksperimen sebaiknya seperti berikut:

1. **Chunking quality**  
   Apakah potongan teks masih utuh secara makna?

2. **Metadata quality**  
   Apakah setiap chunk memiliki sumber yang jelas?

3. **Embedding quality**  
   Apakah query berhasil menemukan chunk yang benar?

4. **Retrieval evaluation**  
   Apakah jawaban muncul di top-3 atau top-5?

5. **Reranking**  
   Apakah reranker memperbaiki urutan chunk?

6. **Answer generation**  
   Apakah LLM menjawab hanya berdasarkan konteks?

7. **Citation discipline**  
   Apakah jawaban selalu mengutip sumber/chunk?

---

## 10. Parameter Awal yang Disarankan

### Chunking

```yaml
chunk_size: 700
chunk_overlap: 120
split_by: paragraph
preserve_headings: true
```

### Retrieval

```yaml
top_k_initial: 10
top_k_final: 4
use_reranker: false
similarity_metric: cosine
```

### RAG Answering

```yaml
temperature: 0.2
max_tokens: 800
answer_language: Indonesian
must_cite_context: true
refuse_if_context_insufficient: true
```

---

## 11. Template `.env.example`

```env
# Local Vector DB
CHROMA_PATH=./chroma_db
COLLECTION_NAME=rag_local_corpus

# NVIDIA NIM
NVIDIA_API_KEY=isi_api_key_di_sini
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=qwen/qwen3-coder-480b-a35b-instruct

# Gemini API sebagai cadangan
GEMINI_API_KEY=isi_api_key_di_sini
GEMINI_MODEL=gemini-2.0-flash

# RAG Config
TOP_K_INITIAL=10
TOP_K_FINAL=4
TEMPERATURE=0.2
MAX_TOKENS=800
```

---

## 12. Checklist Keamanan Data

Sebelum upload ke Kaggle, pastikan corpus tidak mengandung:

- NIK;
- nomor KK;
- nomor HP pribadi;
- alamat rumah;
- email pribadi;
- data kesehatan;
- data keuangan;
- data pegawai internal;
- dokumen pemerintah internal;
- surat rahasia;
- dokumen yang belum boleh dipublikasikan;
- credential, API key, token, password;
- file `.env`.

Checklist minimum:

```text
[ ] Corpus berasal dari data publik/dummy.
[ ] Semua data pribadi sudah dihapus.
[ ] Semua credential sudah dihapus.
[ ] Tidak ada dokumen internal kantor.
[ ] Tidak ada file .env.
[ ] Tidak ada API key di notebook.
[ ] Output Kaggle tidak berisi data sensitif.
```

---

## 13. Batasan Project

Project ini tidak bertujuan untuk:

- melatih LLM besar dari nol;
- membuat model komersial;
- membuat server publik di Kaggle;
- mengganti API production;
- memproses data rahasia;
- menjalankan sistem 24/7.

Project ini bertujuan untuk:

- memahami pipeline RAG;
- melatih kebiasaan evaluasi retrieval;
- membangun ChromaDB lokal yang rapi;
- mencoba embedding dan reranking;
- belajar integrasi API LLM secara bertahap.

---

## 14. Roadmap Tutorial Berikutnya

Setelah file rencana ini selesai, tutorial berikutnya dapat dilanjutkan ke:

1. membuat akun dan API key NVIDIA NIM;
2. mengetes endpoint NVIDIA NIM;
3. memilih model LLM;
4. membuat script Python sederhana;
5. membuat `.env`;
6. menghubungkan retrieval ChromaDB dengan LLM;
7. menambahkan fallback Gemini API;
8. membuat evaluasi jawaban RAG.

---

## 15. Keputusan Awal

Keputusan awal project:

```text
Kaggle      = AI/RAG Training Lab
ChromaDB    = Vector database lokal
NVIDIA NIM  = API LLM utama untuk testing
Gemini API  = API cadangan
Local model = fallback offline dan latihan teknis
```

Strategi ini menjaga penggunaan resource tetap etis, terukur, dan produktif. Kaggle dipakai sebagai tempat belajar membangun komponen RAG, sedangkan sistem utama tetap dikendalikan secara lokal.
