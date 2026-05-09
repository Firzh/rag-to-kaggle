# DOCS MIGRATION PLAN — rag-to-kaggle

Dokumen ini memandu migrasi dokumentasi lama ke struktur baru.

## 1. Tujuan migrasi

1. Menjadikan status implementasi eksplisit.
2. Memisahkan boundary Kaggle dari runtime RAG.
3. Meluruskan jalur return Kaggle agar tidak terbaca sebagai direct promote.
4. Memperkenalkan aturan dokumentasi 9+1 commit.
5. Menjaga dokumen lama yang masih relevan sebagai catatan teknis.

## 2. Dokumen baru

```text
docs/DOCS_INDEX.md
docs/IMPLEMENTATION_STATUS.md
docs/DEVELOPMENT_PLAN.md
docs/KAGGLE_BOUNDARY.md
docs/RAG_HANDOFF_CONTRACT.md
docs/PIPELINE_SCOPE.md
docs/TEST_PLAN.md
docs/DOCS_MAINTENANCE_POLICY.md
docs/DOCS_MIGRATION_PLAN.md
```

## 3. Dokumen lama yang disarankan tetap dipertahankan

```text
docs/kaggle_output_contract.md
docs/kaggle_import_modes.md
docs/local_retrieval_benchmark.md
docs/rag_l1_chunking_integration.md
docs/security_checklist.md
docs/workflow.md
docs/api_tutorial_notes.md
```

Dokumen lama ini tidak perlu dihapus jika tidak bertentangan. Jika ada bagian yang menyiratkan import langsung ke Chroma utama, tambahkan catatan bahwa boundary baru mengharuskan sandbox/report + local compare.

## 4. File root legacy

Jika ada file root `DEVELOPMENT_PLANT.md`, file tersebut sebaiknya diarsipkan atau diganti dengan `docs/DEVELOPMENT_PLAN.md`.

Rencana aman:

```bash
STAMP="2026-05-09-docs-before-boundary-sync"
mkdir -p "docs/_archive/$STAMP"
[ -f DEVELOPMENT_PLANT.md ] && mv DEVELOPMENT_PLANT.md "docs/_archive/$STAMP/DEVELOPMENT_PLANT.old.md"
```

Jika ingin tetap mempertahankan root file untuk kompatibilitas, buat isi pendek yang mengarah ke:

```text
docs/DEVELOPMENT_PLAN.md
```

## 5. README update

README perlu diberi blok tautan dokumentasi baru dari `README_DOCS_BLOCK.md`.

## 6. Post-migration check

```bash
git diff --check
grep -RIn "Chroma utama\|main Chroma\|promote" README.md docs --exclude-dir=_archive || true
git status --short
git diff --stat
```

## 7. Commit title

```bash
git commit -m "docs(kaggle): align pipeline boundary and handoff contracts"
```
