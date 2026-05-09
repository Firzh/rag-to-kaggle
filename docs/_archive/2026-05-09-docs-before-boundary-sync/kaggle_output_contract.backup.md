# Kaggle Output Contract — K2

## 1. Tujuan

Dokumen ini menetapkan format standar output dari Kaggle agar hasil cleaning dan chunking dapat dipakai secara stabil oleh pipeline lokal.

Pada keputusan pipeline B-2, Kaggle tidak menjadi pembuat embedding final. Kaggle hanya dipakai untuk:

1. membersihkan teks;
2. melakukan chunking;
3. mengevaluasi retrieval secara batch;
4. menghasilkan file chunk dan metadata yang rapi.

Embedding final tetap dibuat di lokal agar konsisten dengan RAG lokal dan ChromaDB sandbox.

## 2. Posisi Kaggle dalam Pipeline

Alur utama:

Local sanitized corpus
→ Kaggle cleaning/chunking
→ cleaned_chunks.parquet + metadata.jsonl
→ local embedding
→ ChromaDB sandbox
→ retrieval benchmark
→ compare
→ promote jika sudah aman

## 3. Output Wajib dari Kaggle

Kaggle minimal harus menghasilkan file berikut:

- cleaned_chunks.parquet
- metadata.jsonl
- retrieval_score.csv
- evaluation_report.md

File berikut boleh ada, tetapi tidak wajib:

- embeddings.npy

Catatan: embeddings.npy dari Kaggle hanya digunakan untuk smoke test atau eksperimen, bukan untuk collection final.

## 4. Schema cleaned_chunks.parquet

cleaned_chunks.parquet wajib memiliki kolom berikut:

| Kolom | Tipe | Keterangan |
|---|---|---|
| chunk_id | string | ID unik setiap chunk |
| doc_id | string | ID dokumen asal |
| title | string | Judul dokumen |
| source | string | Nama file, URL, atau sumber dokumen |
| source_type | string | local_file, web, chroma_export, dummy, unknown |
| chunk_index | integer | Urutan chunk dalam dokumen |
| text | string | Isi chunk yang sudah bersih |
| char_count | integer | Jumlah karakter dalam chunk |
| token_estimate | integer | Estimasi jumlah token |
| chunking_method | string | Metode chunking yang dipakai |
| sanitized | boolean | Status bahwa teks sudah disanitasi |
| origin_pipeline | string | Asal pipeline pemrosesan |
| content_hash | string | Hash isi chunk |

## 5. Schema metadata.jsonl

metadata.jsonl wajib memiliki jumlah baris yang sama dengan cleaned_chunks.parquet.

Setiap baris metadata minimal memiliki struktur berikut:

{
  "chunk_id": "...",
  "doc_id": "...",
  "title": "...",
  "source": "...",
  "source_type": "local_file",
  "chunk_index": 0,
  "char_count": 700,
  "token_estimate": 180,
  "chunking_method": "paragraph_aware_v1",
  "sanitized": true,
  "origin_pipeline": "kaggle_cleaning",
  "content_hash": "..."
}

## 6. Aturan Validasi

Output Kaggle dianggap valid jika:

1. cleaned_chunks.parquet tersedia.
2. metadata.jsonl tersedia.
3. retrieval_score.csv tersedia.
4. evaluation_report.md tersedia.
5. cleaned_chunks.parquet tidak kosong.
6. Semua kolom wajib tersedia.
7. chunk_id tidak kosong.
8. chunk_id tidak duplikat.
9. doc_id tidak kosong.
10. source tidak kosong.
11. text tidak kosong.
12. content_hash tidak kosong.
13. sanitized bernilai true.
14. metadata.jsonl memiliki jumlah baris yang sama dengan cleaned_chunks.parquet.
15. Urutan chunk_id di metadata.jsonl sama dengan urutan chunk_id di cleaned_chunks.parquet.

## 7. Nilai source_type yang Diizinkan

source_type hanya boleh berisi salah satu dari:

- local_file
- web
- chroma_export
- dummy
- unknown

## 8. Nilai origin_pipeline yang Disarankan

origin_pipeline dapat memakai nilai berikut:

- kaggle_cleaning
- kaggle_chunking
- local_sanitize
- web_staging
- chroma_export
- unknown

## 9. Penamaan Collection Sandbox

Collection untuk smoke test Kaggle embedding:

rag_kaggle_tfidf_smoke

Collection untuk local embedding dari hasil Kaggle:

rag_kaggle_local_embed_sandbox

Collection untuk hasil chunking versi L1:

rag_kaggle_l1_chunking_sandbox

Collection untuk data web dari mini scraper:

rag_kaggle_web_sandbox

## 10. Prinsip Keamanan

Data dari Kaggle tidak boleh langsung masuk Chroma utama.

Semua output Kaggle harus masuk Chroma sandbox terlebih dahulu.

Promote ke collection utama hanya boleh dilakukan setelah:

1. schema valid;
2. metadata lengkap;
3. retrieval benchmark lulus;
4. compare terhadap collection lama tidak menunjukkan penurunan besar;
5. tidak ada data sensitif;
6. chunk tidak kosong atau rusak.
