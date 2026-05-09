# KAGGLE BOUNDARY — rag-to-kaggle

Dokumen ini menetapkan batas scope Kaggle dalam ekosistem RAG lokal.

## 1. Definisi peran

`rag-to-kaggle` adalah:

```text
adapter + evaluator + experiment pipeline
```

`rag-to-kaggle` bukan:

```text
production RAG runtime
pemilik Chroma utama
promotion authority
server RAG publik
agent yang mengubah data utama otomatis
```

## 2. Yang boleh dilakukan Kaggle

Kaggle boleh digunakan untuk:

- cleaning batch;
- chunking experiment;
- embedding smoke test;
- retrieval experiment;
- geometry audit besar;
- visualisasi evaluasi;
- pengukuran recall/MRR/score distribution;
- pembuatan report;
- pembuatan risk label;
- rekomendasi parameter.

## 3. Yang tidak boleh dilakukan Kaggle

Kaggle tidak boleh:

- menulis langsung ke Chroma utama;
- menghapus chunk asli;
- mengganti collection produksi;
- melakukan promote;
- menyimpan `.env`, API key, token, atau secret;
- menjadi backend produksi;
- membuka server publik untuk RAG lokal;
- menjadi sumber kebenaran final tanpa local regression;
- mengembalikan centroid/medoid sebagai pengganti evidence asli tanpa local compare.

## 4. Return path yang aman

Return path aman:

```text
Kaggle output
  -> report/risk label/recommended params/failed queries
  -> local sandbox di ai-rag-local
  -> old-vs-sandbox compare
  -> local regression
  -> promote gate milik ai-rag-local
```

Return path yang tidak aman:

```text
Kaggle output
  -> Chroma utama
```

## 5. Boundary terhadap `ai-rag-local`

| Area | `ai-rag-local` | `rag-to-kaggle` |
|---|---|---|
| Chroma utama | Pemilik | Tidak boleh menulis |
| Runtime RAG | Pemilik | Tidak menjalankan produksi |
| Parser/quality gate final | Pemilik | Menguji/audit output |
| JSONL handoff | Export/import kontrak | Membaca/menghasilkan output kontrak |
| Sandbox collection | Bisa membuat/menguji lokal | Bisa menghasilkan candidate artifact |
| Benchmark | Local regression final | Eksperimen/evaluasi pendukung |
| Promote | Pemilik keputusan | Tidak punya otoritas |

## 6. Boundary terhadap eksperimen geometri

Geometry audit dan GAC boleh menjadi eksperimen di Kaggle. Hasilnya hanya boleh kembali sebagai:

- `geometry_audit_summary.json`;
- `chunk_risk_labels.jsonl`;
- `recommended_runtime_policy.json`;
- `failed_cases.jsonl`;
- catatan re-chunking.

Hasil eksperimen tidak boleh langsung mengganti index utama.

## 7. Aturan dokumentasi

Perubahan boundary Kaggle harus memperbarui dokumen ini. Dalam siklus normal, setiap 9 commit implementasi diikuti commit ke-10 untuk dokumentasi.
