# TEST PLAN — rag-to-kaggle

Dokumen ini memuat rencana test untuk pipeline `rag-to-kaggle`.

## 1. Prinsip test

1. Semua schema baru harus punya validator.
2. Semua adapter baru harus punya fixture kecil.
3. Semua import harus eksplisit mode-nya.
4. Semua collection sandbox harus memakai nama sandbox.
5. Tidak ada test yang menulis ke Chroma utama.
6. Report harus mencatat failed cases.

## 2. Test status saat ini

| Area | Status |
|---|---|
| K2 output contract validation | Sudah ada/stabil |
| K3 explicit import mode | Sudah ada/stabil |
| K4 local retrieval benchmark | Sudah ada/stabil |
| K5 L1 handoff integration | Sudah ada/stabil |
| K6 L2 HTML parser handoff | Planned |
| K7 web staging adapter | Planned |
| K8 metadata-aware embedding | Planned |
| K9 Chroma export adapter | Planned |
| K10 collection compare | Planned |
| K11 promotion handoff report | Planned |

## 3. K6 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_normalize_rag_l2_html_minimal` | Membaca JSONL minimal | Output valid |
| `test_normalize_rag_l2_html_full_metadata` | Menjaga metadata lengkap | `url`, `domain`, `parser`, `heading_path` tetap ada |
| `test_l2_html_schema_validation` | Validasi schema | Output K2-compatible |
| `test_l2_html_reject_missing_text` | Menolak chunk tanpa teks | Masuk failed/invalid |
| `test_l2_html_preserve_chunk_index` | Menjaga urutan chunk | `chunk_index` stabil |
| `test_l2_html_sandbox_collection_name` | Cegah nama production | Nama collection harus sandbox |

## 4. K7 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_web_staging_lifecycle_status` | Memastikan lifecycle source | Status valid |
| `test_web_staging_quarantine_parser_warning` | Parser warning tidak ikut approved | Masuk quarantine |
| `test_web_staging_no_secret_export` | Mencegah secret bocor | `.env`, token, API key tidak masuk export |
| `test_export_web_staging_k2_compatible` | Export tetap K2-compatible | Validator pass |

## 5. K8 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_metadata_embedding_text_format` | Format embedding text stabil | Field berurutan dan tidak kosong |
| `test_metadata_does_not_replace_content` | Konten asli tidak hilang | `content` tetap ada |
| `test_baseline_vs_metadata_benchmark` | Bandingkan performa | Report baseline vs kandidat |
| `test_numeric_query_not_harmed` | Query angka tidak rusak | Query angka tetap match |

## 6. K9 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_read_chroma_export_jsonl` | Membaca export Chroma | Semua chunk terbaca |
| `test_chroma_export_manifest_required` | Manifest wajib | Gagal jika manifest hilang |
| `test_embedding_model_preserved` | Model embedding tidak hilang | Ada di report |
| `test_no_main_chroma_write` | Cegah write produksi | Tidak ada path Chroma utama disentuh |

## 7. K10 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_compare_baseline_vs_candidate` | Compare dua collection | Report per query |
| `test_compare_failed_queries_written` | Catat query gagal | `failed_queries.jsonl` dibuat |
| `test_compare_source_match` | Cek source match | Metrik source match muncul |
| `test_compare_metadata_preservation` | Cek metadata | Metadata penting tidak hilang |
| `test_compare_no_promotion_side_effect` | Cegah promote | Tidak ada write ke main collection |

## 8. K11 test cases

| Test | Tujuan | Ekspektasi |
|---|---|---|
| `test_promotion_handoff_report_schema` | Schema report valid | Status valid |
| `test_no_promoted_status_allowed` | Cegah status promote | `promoted` ditolak |
| `test_blocked_when_regression_detected` | Regression harus blocking | Status `blocked` atau `regression_detected` |
| `test_pass_only_for_local_review` | Pass bukan promote | Status `pass_for_local_review` |

## 9. Boundary regression tests

Test lintas modul:

```text
- Tidak ada script yang default menulis ke Chroma utama.
- Semua import butuh mode eksplisit.
- Semua output kandidat diberi status candidate/sandbox/report.
- Semua report menyertakan manifest input.
- Semua benchmark menyertakan daftar failed queries.
```

## 10. Dokumentasi test

Setiap test baru harus memperbarui dokumen ini. Setiap 9 commit implementasi, commit ke-10 wajib mengecek kesesuaian test plan dengan implementasi.
