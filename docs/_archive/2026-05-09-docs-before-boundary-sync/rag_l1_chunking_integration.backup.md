# K5 — Integrasi L1 chunking_v2 dari rag-lc

## Tujuan

K5 menghubungkan hasil `chunking_v2.py` dari project `rag-lc` ke pipeline `rag-to-kaggle`.

Integrasi ini memakai file handoff JSONL, bukan import langsung module Python dari `rag-lc`.

## Prinsip

`rag-lc` bertugas:

- parsing dokumen;
- menjalankan chunking_v2;
- menghasilkan chunk JSONL;
- menjaga metadata awal dari dokumen.

`rag-to-kaggle` bertugas:

- membaca file JSONL hasil L1;
- menormalisasi ke schema K2;
- memvalidasi schema;
- membuat local embedding;
- memasukkan ke Chroma sandbox;
- menjalankan benchmark retrieval.

## Alur

rag-lc
→ chunking_v2.py
→ l1_chunks.jsonl
→ rag-to-kaggle/data/l1_incoming/l1_chunks.jsonl
→ normalize_rag_l1_chunks.py
→ data/l1_import/cleaned_chunks.parquet
→ data/l1_import/metadata.jsonl
→ validate_kaggle_outputs.py
→ kaggle_import_pipeline.py --mode local-embedding
→ run_local_retrieval_benchmark.py

## Format Input dari rag-lc

File JSONL dari `rag-lc` minimal harus berisi satu chunk per baris.

Format minimal:

{
  "doc_id": "doc_001",
  "title": "Judul Dokumen",
  "source": "nama_file.pdf",
  "chunk_index": 0,
  "text": "Isi chunk hasil chunking_v2",
  "metadata": {
    "section_title": "Pendahuluan",
    "page": 1,
    "chunking_method": "chunking_v2"
  }
}

Format lebih lengkap:

{
  "chunk_id": "doc_001_0000_xxxxx",
  "doc_id": "doc_001",
  "title": "Judul Dokumen",
  "source": "nama_file.pdf",
  "source_type": "local_file",
  "chunk_index": 0,
  "text": "Isi chunk hasil chunking_v2",
  "char_count": 850,
  "token_estimate": 210,
  "chunking_method": "chunking_v2",
  "sanitized": true,
  "origin_pipeline": "rag_lc_l1_chunking_v2",
  "content_hash": "...",
  "metadata": {
    "section_title": "Pendahuluan",
    "page": 1
  }
}

## Output K5

K5 menghasilkan paket K2-compatible:

- cleaned_chunks.parquet
- metadata.jsonl
- retrieval_score.csv
- evaluation_report.md

Output default:

data/l1_import/

## Collection Sandbox

Collection default untuk hasil L1:

rag_kaggle_l1_chunking_sandbox

## Aturan Penting

1. Hasil L1 tidak boleh langsung masuk Chroma utama.
2. Hasil L1 harus masuk Chroma sandbox.
3. File L1 harus lolos validate_kaggle_outputs.py.
4. Hasil L1 harus lolos benchmark retrieval lokal.
5. Promote ke collection utama tetap pending sampai compare collection tersedia.
6. Metadata chunking_method harus menyebut `chunking_v2` agar hasil L1 bisa dilacak.
