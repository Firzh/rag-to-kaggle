## Dokumentasi teknis

| Dokumen | Fungsi |
|---|---|
| `docs/DOCS_INDEX.md` | Peta seluruh dokumentasi teknis repo |
| `docs/IMPLEMENTATION_STATUS.md` | Status fitur yang sudah dan belum diimplementasikan |
| `docs/DEVELOPMENT_PLAN.md` | Rencana pengembangan K6 dan seterusnya |
| `docs/KAGGLE_BOUNDARY.md` | Batas scope Kaggle sebagai lab/pipeline eksperimen |
| `docs/RAG_HANDOFF_CONTRACT.md` | Kontrak data masuk/keluar antara RAG dan Kaggle |
| `docs/PIPELINE_SCOPE.md` | Batas pipeline, sandbox, report, dan larangan promote langsung |
| `docs/TEST_PLAN.md` | Rencana test dan acceptance criteria |
| `docs/DOCS_MAINTENANCE_POLICY.md` | Kebijakan update dokumentasi, termasuk aturan 9+1 commit |

Catatan maintenance: setiap 9 commit implementasi, commit ke-10 wajib dipakai untuk update dokumentasi. Perubahan kontrak data, boundary, atau safety gate tetap wajib didokumentasikan segera walaupun belum mencapai commit ke-10.
