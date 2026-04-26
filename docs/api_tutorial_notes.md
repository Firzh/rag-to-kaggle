# Catatan API

## Gemini lokal

Gunakan `.env`:

```env
GEMINI_API_KEY=isi_api_key_gemini_kamu
GEMINI_MODEL=gemini-2.0-flash
```

Script `scripts/rag_chat.py` akan:

1. membuat embedding query;
2. mengambil konteks dari ChromaDB;
3. menyusun prompt RAG;
4. mengirim prompt ke Gemini;
5. meminta jawaban hanya berdasarkan konteks.

## Jangan taruh API key di Kaggle Notebook

Untuk Kaggle, gunakan menu Secrets bila suatu saat perlu API key.
Namun untuk tahap hook RAG ini, notebook Kaggle tidak membutuhkan Gemini API.
