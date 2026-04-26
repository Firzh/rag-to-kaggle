# Instalasi di Windows

Target folder:

```text
F:\AI-Models\rag-to-kaggle
```

## Opsi A — Timpa isi folder rag-to-kaggle dengan isi ZIP

Setelah download ZIP starter kit, jalankan PowerShell:

```powershell
New-Item -ItemType Directory -Force "F:\AI-Models\rag-to-kaggle" | Out-Null
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\rag-to-kaggle-hook-starter.zip" -DestinationPath "F:\AI-Models\rag-to-kaggle" -Force
cd /d F:\AI-Models\rag-to-kaggle
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

## Opsi B — Backup dulu folder lama

```powershell
Rename-Item "F:\AI-Models\rag-to-kaggle" "rag-to-kaggle_backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
New-Item -ItemType Directory -Force "F:\AI-Models\rag-to-kaggle" | Out-Null
Expand-Archive -LiteralPath "$env:USERPROFILE\Downloads\rag-to-kaggle-hook-starter.zip" -DestinationPath "F:\AI-Models\rag-to-kaggle" -Force
```

## Test awal

```powershell
cd /d F:\AI-Models\rag-to-kaggle
.\.venv\Scripts\activate
python scripts/sanitize_corpus.py
python scripts/export_corpus.py
```

Output yang harus muncul:

```text
data/export/corpus_export.jsonl
```
