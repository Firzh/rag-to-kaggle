# DOCS MAINTENANCE POLICY — rag-to-kaggle

Dokumen ini mengatur kapan dokumentasi `rag-to-kaggle` harus diperbarui.

## 1. Aturan 9+1 commit

Setiap 9 commit implementasi, commit ke-10 wajib menjadi commit dokumentasi.

```text
9 commit implementasi -> 1 commit dokumentasi
```

Commit dokumentasi ke-10 minimal mengecek:

- README;
- `IMPLEMENTATION_STATUS.md`;
- `DEVELOPMENT_PLAN.md`;
- `KAGGLE_BOUNDARY.md`;
- `RAG_HANDOFF_CONTRACT.md`;
- `PIPELINE_SCOPE.md`;
- `TEST_PLAN.md`;
- dokumen kontrak lama yang masih relevan.

## 2. Perubahan yang wajib didokumentasikan segera

Jangan menunggu commit ke-10 jika perubahan menyentuh:

- schema JSONL;
- schema output Kaggle;
- manifest;
- import mode;
- collection sandbox name;
- benchmark metric;
- return path ke RAG;
- promotion handoff report;
- security boundary;
- secret handling;
- embedding model;
- chunking strategy;
- geometry audit output;
- compare report.

## 3. Commit title dokumentasi

Gunakan pola:

```bash
git commit -m "docs(kaggle): <ringkasan>"
```

Contoh:

```bash
git commit -m "docs(kaggle): update handoff contract after K6 adapter"
```

```bash
git commit -m "docs(kaggle): document K10 compare report schema"
```

## 4. Checklist sebelum merge dokumentasi

```text
[ ] IMPLEMENTATION_STATUS tidak menyebut fitur pending sebagai implemented
[ ] README tidak menyiratkan direct import ke Chroma utama
[ ] KAGGLE_BOUNDARY masih melarang promote langsung
[ ] RAG_HANDOFF_CONTRACT sesuai schema terbaru
[ ] TEST_PLAN mencakup fitur baru
[ ] Tidak ada file lama yang bertentangan tanpa catatan migration
[ ] git diff --check bersih
```

## 5. Larangan dokumentasi

Jangan menulis:

- “Kaggle output siap produksi” tanpa local compare;
- “import ke Chroma utama” sebagai default;
- “promote otomatis” dari repo ini;
- “GAC mengganti evidence asli” sebagai default;
- “sandbox collection aman dipakai utama” tanpa promote gate RAG.
