# K3 — Kaggle Import Modes

## Tujuan

K3 memisahkan dua mode import hasil Kaggle agar pipeline tidak mencampur embedding eksperimen dengan embedding final lokal.

## Mode 1 — smoke-kaggle-embedding

Mode ini memakai file:

- cleaned_chunks.parquet
- metadata.jsonl
- embeddings.npy

Tujuannya hanya untuk smoke test:

- memastikan embeddings.npy bisa dibaca;
- memastikan jumlah embedding sama dengan jumlah chunk;
- memastikan data bisa masuk ChromaDB sandbox.

Mode ini tidak dipakai untuk collection final.

Collection default:

rag_kaggle_tfidf_smoke_k3

## Mode 2 — local-embedding

Mode ini memakai file:

- cleaned_chunks.parquet
- metadata.jsonl

Lalu embedding dibuat ulang di lokal memakai FastEmbed.

Mode ini adalah jalur utama untuk pipeline B-2.

Collection default:

rag_kaggle_local_embed_sandbox_k3

## Keputusan Pipeline

Kaggle bertugas:

- cleaning;
- chunking;
- evaluasi batch;
- output cleaned_chunks.parquet dan metadata.jsonl.

Lokal bertugas:

- embedding final;
- ChromaDB sandbox;
- retrieval test;
- compare;
- promote jika sudah aman.

## Aturan

1. Jangan mencampur embedding Kaggle dan embedding lokal dalam satu collection.
2. Gunakan collection berbeda untuk setiap mode.
3. Gunakan --reset hanya untuk collection sandbox.
4. Jalankan validate_kaggle_outputs.py sebelum import.
5. Collection hasil K3 belum boleh dipromote ke RAG utama.
