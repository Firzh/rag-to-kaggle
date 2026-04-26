# Security Checklist sebelum Upload ke Kaggle

Pastikan semua item berikut aman.

```text
[ ] Corpus berasal dari data publik/dummy.
[ ] Tidak ada NIK.
[ ] Tidak ada nomor KK.
[ ] Tidak ada nomor HP pribadi.
[ ] Tidak ada alamat rumah.
[ ] Tidak ada email pribadi.
[ ] Tidak ada data kesehatan.
[ ] Tidak ada data keuangan pribadi.
[ ] Tidak ada data pegawai internal.
[ ] Tidak ada dokumen pemerintah internal.
[ ] Tidak ada surat rahasia.
[ ] Tidak ada credential, API key, token, password.
[ ] Tidak ada file .env.
[ ] Tidak ada API key di notebook.
[ ] Output Kaggle tidak berisi data sensitif.
```

Aturan praktis:

- Kalau ragu, jangan upload.
- Gunakan corpus dummy/publik untuk latihan.
- Simpan API key di `.env` lokal atau Kaggle Secrets, bukan di file project.
