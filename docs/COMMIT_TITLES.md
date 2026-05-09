# Commit Titles — rag-to-kaggle Documentation Sync

## Utama

```bash
git commit -m "docs(kaggle): align pipeline boundary and handoff contracts"
```

## Alternatif

```bash
git commit -m "docs(kaggle): clarify sandbox-only return path to rag"
```

```bash
git commit -m "docs(kaggle): add implementation status and scope boundaries"
```

```bash
git commit -m "docs(kaggle): add 9+1 documentation cadence"
```

## Bila sekaligus mengarsipkan dokumentasi lama

```bash
git commit -m "docs(kaggle): archive stale planning notes and add boundary docs"
```

## Aturan maintenance

Setiap 9 commit implementasi, commit ke-10 harus menjadi commit dokumentasi. Perubahan kontrak data, boundary, safety gate, atau jalur return ke RAG wajib didokumentasikan segera walaupun belum mencapai commit ke-10.
