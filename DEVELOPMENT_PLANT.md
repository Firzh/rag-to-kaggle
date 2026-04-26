# DEVELOPMENT PLANT — rag-to-kaggle K6–K11

## 1. Posisi Terakhir Project

Project `rag-to-kaggle` saat ini sudah mencapai titik stabil untuk jalur awal:

```text
Local corpus
→ sanitize/export
→ Kaggle cleaning/chunking
→ normalized K2 schema
→ local embedding
→ Chroma sandbox
→ retrieval benchmark
```

Patch yang sudah selesai:

```text
K1 — Kaggle smoke test
K2 — Kaggle output contract + schema validation
K3 — explicit import modes
K4 — local retrieval benchmark
K5 — rag-lc L1 chunking_v2 handoff integration
```

Status K5:

```text
rag-lc L1 chunking_v2
→ JSONL handoff
→ normalize_rag_l1_chunks.py
→ K2-compatible output
→ validate_kaggle_outputs.py
→ kaggle_import_pipeline.py --mode local-embedding
→ rag_kaggle_l1_chunking_sandbox
→ L1 handoff benchmark
```

Hasil K5 menunjukkan integrasi berhasil. Chunk/section yang benar sudah muncul di top-k. Jika top-1 belum selalu tepat, itu dicatat sebagai isu retrieval ranking, bukan blocker integrasi.

---

## 2. Kontrak Data yang Disepakati dengan rag-lc

Sisi `rag-lc` akan membuat export adapter yang mengubah output `chunk_text_v2()` menjadi JSONL.

Format pertukaran utama:

```json
{
  "doc_id": "hash_dokumen_web",
  "title": "Judul Halaman",
  "source": "https://example.com/artikel",
  "source_type": "web",
  "parser": "html_parser_v1",
  "page": null,
  "chunk_index": 0,
  "text": "Isi chunk",
  "metadata": {
    "url": "https://example.com/artikel",
    "domain": "example.com",
    "section_title": "Pendahuluan",
    "section_index": 0,
    "heading_path": "Pendahuluan",
    "char_count": 850,
    "token_estimate": 210,
    "document_hash": "...",
    "chunk_hash": "...",
    "chunker": "chunking_v2"
  }
}
```

Minimal wajib:

```json
{
  "doc_id": "...",
  "text": "..."
}
```

Sangat disarankan:

```text
title
source
source_type
parser
page
chunk_index
metadata.url
metadata.domain
metadata.section_title
metadata.section_index
metadata.heading_path
metadata.char_count
metadata.token_estimate
metadata.document_hash
metadata.chunk_hash
metadata.chunker
```

Catatan penting:

```text
doc_id/title/source/source_type/parser/page harus diberikan dari base_metadata saat memanggil chunk_text_v2.
chunker tidak boleh dipaksa menebak metadata dokumen dari teks saja.
```

---

## 3. Prinsip Pipeline Setelah K5

Mulai K6 dan seterusnya, `rag-to-kaggle` berperan sebagai pipeline adapter dan evaluator, bukan sebagai aplikasi RAG utama.

Keputusan pipeline:

```text
Kaggle:
- cleaning batch
- chunking experiment
- retrieval experiment
- optional embedding smoke test

Lokal:
- embedding final
- Chroma sandbox
- benchmark retrieval
- compare collection
- promote gate
```

Data tidak boleh langsung masuk Chroma utama.

Semua input baru harus melewati:

```text
normalize
→ validate
→ local embedding
→ Chroma sandbox
→ benchmark
→ compare
→ promote gate
```

---

# K6 — L2 HTML Parser Handoff Adapter

## Tujuan

K6 menyiapkan `rag-to-kaggle` agar bisa menerima output dari `rag-lc` L2 `html_parser.py`.

L2 HTML parser akan menangani sumber HTML/web yang sudah diparse di sisi `rag-lc`.

## Input

Input berupa JSONL hasil parser + chunking dari `rag-lc`.

Default input:

```text
data/l2_html_incoming/html_chunks.jsonl
```

Contoh input:

```json
{
  "doc_id": "hash_dokumen_web",
  "title": "Judul Halaman",
  "source": "https://example.com/artikel",
  "source_type": "web",
  "parser": "html_parser_v1",
  "page": null,
  "chunk_index": 0,
  "text": "Isi chunk",
  "metadata": {
    "url": "https://example.com/artikel",
    "domain": "example.com",
    "section_title": "Pendahuluan",
    "section_index": 0,
    "heading_path": "Pendahuluan",
    "char_count": 850,
    "token_estimate": 210,
    "document_hash": "...",
    "chunk_hash": "...",
    "chunker": "chunking_v2"
  }
}
```

## Output

Output K6 harus tetap K2-compatible:

```text
data/l2_html_import/cleaned_chunks.parquet
data/l2_html_import/metadata.jsonl
data/l2_html_import/retrieval_score.csv
data/l2_html_import/evaluation_report.md
```

## Collection Sandbox

```text
rag_kaggle_l2_html_sandbox
```

## File yang Direncanakan

```text
docs/rag_l2_html_handoff.md
configs/rag_l2_html_schema.json
configs/local_retrieval_eval_html.jsonl
scripts/normalize_rag_l2_html.py
```

## Acceptance Criteria

```text
1. normalize_rag_l2_html.py bisa membaca html_chunks.jsonl.
2. Output lolos validate_kaggle_outputs.py.
3. source_type = web.
4. metadata url/domain/parser/section_title tetap terbawa.
5. Import local-embedding ke rag_kaggle_l2_html_sandbox berhasil.
6. Benchmark HTML retrieval menghasilkan CSV dan MD report.
```

---

# K7 — Mini Scraper Staging Adapter

## Tujuan

K7 mulai menyambungkan mini scraper agent, tetapi hanya sampai staging. Mini scraper belum boleh langsung masuk Chroma utama.

## Posisi Mini Scraper

Mini scraper dikembangkan terpisah.

Alur yang disepakati:

```text
mini scraper
→ web_raw
→ web_parsed
→ web_sanitized
→ web_export_for_kaggle.jsonl
→ rag-to-kaggle
→ normalize
→ validate
→ local embedding
→ Chroma web sandbox
→ benchmark
```

## Folder yang Direncanakan

```text
data/web_staging/raw/
data/web_staging/parsed/
data/web_staging/sanitized/
data/web_staging/quarantine/
data/web_staging/export/
registry/source_registry.jsonl
registry/crawl_log.jsonl
```

## Status Data

```text
discovered
fetched
parsed
sanitized
approved
exported_to_kaggle
imported_to_chroma_sandbox
promoted_to_chroma_main
```

## File yang Direncanakan

```text
docs/mini_scraper_staging_adapter.md
configs/web_staging_schema.json
scripts/normalize_web_staging.py
scripts/validate_web_staging.py
scripts/export_web_staging_for_kaggle.py
```

## Acceptance Criteria

```text
1. Mini scraper output tidak langsung masuk Chroma.
2. Web staging JSONL bisa dinormalisasi ke K2.
3. Data web memiliki url, domain, fetched_at, parser, source_type=web.
4. Data yang belum approved tidak boleh masuk export.
5. Dedup by url/content_hash tersedia.
6. Output bisa masuk Chroma sandbox web.
```

---

# K8 — Metadata-Aware Embedding Text

## Tujuan

K8 memperbaiki ranking retrieval dengan menambahkan metadata penting ke teks yang dipakai untuk embedding.

Masalah yang terlihat di K5:

```text
Chunk yang benar sudah muncul di top-k, tetapi belum selalu top-1.
```

Solusi awal:

```text
Gunakan embedding_text berbeda dari document_text.
```

Document text tetap:

```text
Isi chunk asli
```

Embedding text menjadi:

```text
Title: ...
Source: ...
Section: ...
Heading Path: ...

Isi chunk asli
```

## Prinsip

```text
- Jangan mengubah teks dokumen asli.
- Metadata hanya dipakai sebagai konteks tambahan saat embedding.
- Metadata yang dipakai harus eksplisit dan dapat dilacak.
```

## Field yang Diprioritaskan

```text
title
source
source_type
section_title
heading_path
parser
domain
url
```

## File yang Direncanakan

```text
docs/metadata_aware_embedding.md
configs/embedding_text_template.json
scripts/build_embedding_text.py
scripts/kaggle_import_pipeline.py
```

## Collection Sandbox

```text
rag_kaggle_metadata_aware_sandbox
```

## Acceptance Criteria

```text
1. Pipeline bisa memilih plain_text atau metadata_aware_text.
2. Document yang disimpan di Chroma tetap chunk asli.
3. Embedding dibuat dari embedding_text.
4. Benchmark L1/HTML bisa dibandingkan antara plain vs metadata-aware.
5. Tidak ada metadata sensitif dimasukkan ke embedding_text.
```

---

# K9 — Chroma Export Adapter dari RAG Lama

## Tujuan

K9 menyiapkan jalur audit data lama yang sudah terlanjur masuk ChromaDB.

Alur:

```text
rag-lc ChromaDB lama
→ export chunks + metadata JSONL
→ rag-to-kaggle normalize
→ validate
→ optional Kaggle audit
→ local embedding
→ Chroma sandbox baru
```

## Masalah yang Ingin Diatasi

```text
- chunk lama terlalu panjang
- chunk lama terlalu pendek
- metadata kosong
- source tidak jelas
- data duplikat
- data kotor telanjur masuk Chroma
```

## Input

```text
data/chroma_export_incoming/chroma_export.jsonl
```

## Output

```text
data/chroma_export_import/cleaned_chunks.parquet
data/chroma_export_import/metadata.jsonl
data/chroma_export_import/retrieval_score.csv
data/chroma_export_import/evaluation_report.md
```

## File yang Direncanakan

```text
docs/chroma_export_adapter.md
configs/chroma_export_schema.json
scripts/normalize_chroma_export.py
scripts/audit_chroma_export.py
```

## Acceptance Criteria

```text
1. Export Chroma lama bisa dibaca sebagai JSONL.
2. Metadata lama tidak hilang.
3. Missing metadata bisa dihitung.
4. Duplicate content_hash bisa dihitung.
5. Output lolos K2 validation.
6. Collection sandbox hasil re-embedding bisa dibuat.
```

---

# K10 — Collection Compare

## Tujuan

K10 membandingkan collection lama dan collection baru sebelum ada keputusan promote.

Contoh collection:

```text
rag_local_corpus
rag_kaggle_l1_chunking_sandbox
rag_kaggle_l2_html_sandbox
rag_kaggle_metadata_aware_sandbox
rag_kaggle_web_sandbox
```

## Metrik Awal

```text
hit_doc_top1
hit_doc_topk
hit_source_top1
hit_source_topk
hit_section_top1
hit_section_topk
expected_terms_ratio_top1
expected_terms_ratio_topk
average_distance
missing_metadata_count
duplicate_content_hash_count
empty_text_count
```

## File yang Direncanakan

```text
docs/collection_compare.md
configs/collection_compare_eval.jsonl
scripts/compare_collections.py
scripts/audit_collection_metadata.py
```

## Output

```text
outputs/collection_compare.csv
outputs/collection_compare_report.md
```

## Acceptance Criteria

```text
1. Bisa membandingkan minimal dua collection.
2. Bisa memakai eval file yang sama.
3. Bisa membaca metadata doc_id/source/section_title.
4. Report menunjukkan collection mana yang lebih baik per metrik.
5. Tidak ada promote otomatis di K10.
```

---

# K11 — Promotion Gate

## Tujuan

K11 membuat gerbang promosi collection sandbox ke collection utama.

Promotion gate bukan auto promote bebas. Gate hanya memberi izin promote jika syarat terpenuhi.

## Syarat Promote

```text
1. Schema valid.
2. Metadata lengkap.
3. Tidak ada data sensitif.
4. Empty text = 0.
5. Duplicate content_hash dalam batas wajar.
6. Benchmark tidak lebih buruk dari collection lama.
7. Source/doc_id jelas.
8. Collection lama sudah dibackup.
9. Collection baru sudah diberi fingerprint.
```

## Fingerprint yang Wajib Ada

```text
collection_name
created_at
embedding_model
embedding_backend
embedding_backend_version
chunking_method
chunking_version
parser
parser_version
source_type
origin_pipeline
schema_version
```

## File yang Direncanakan

```text
docs/collection_promotion_policy.md
configs/promotion_gate_rules.json
scripts/check_promotion_gate.py
scripts/collection_promote.py
```

## Acceptance Criteria

```text
1. check_promotion_gate.py bisa memberi PASS/FAIL.
2. collection_promote.py tidak berjalan jika gate FAIL.
3. Promote membutuhkan flag eksplisit.
4. Backup collection lama wajib tersedia.
5. Promotion report tersimpan.
```

---

## 4. Urutan Prioritas K6–K11

Prioritas utama:

```text
K6  — L2 HTML Parser Handoff Adapter
K7  — Mini Scraper Staging Adapter
K8  — Metadata-Aware Embedding Text
K9  — Chroma Export Adapter
K10 — Collection Compare
K11 — Promotion Gate
```

Rasional:

```text
K6 diperlukan karena rag-lc akan lanjut ke L2 html_parser.
K7 diperlukan karena mini scraper mulai dikembangkan terpisah.
K8 diperlukan untuk memperbaiki ranking top-1.
K9 diperlukan untuk audit Chroma lama.
K10 diperlukan sebelum membandingkan collection.
K11 baru boleh setelah compare stabil.
```

---

## 5. Hal yang Tidak Boleh Dilakukan Dulu

```text
- Jangan auto promote collection.
- Jangan scraper langsung masuk Chroma utama.
- Jangan mencampur embedding Kaggle TF-IDF dengan local embedding.
- Jangan menghapus collection lama sebelum ada backup.
- Jangan menaruh API key, .env, atau data sensitif ke Kaggle.
- Jangan menjadikan Kaggle sebagai backend produksi.
```

---

## 6. Ringkasan Keputusan

```text
rag-lc:
lanjut L2 html_parser.py.

rag-to-kaggle:
lanjut K6 untuk menerima output L2 HTML parser.

mini scraper:
boleh berjalan terpisah, tetapi output ditahan di staging JSONL.

Promote:
tetap pending sampai K10 dan K11 selesai.
```
