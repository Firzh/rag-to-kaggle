from __future__ import annotations

import shutil
from pathlib import Path

from common import project_path

SANITIZED_PATH = project_path("data", "sanitized", "corpus_sanitized.jsonl")
EXPORT_PATH = project_path("data", "export", "corpus_export.jsonl")


def main() -> None:
    if not SANITIZED_PATH.exists():
        raise FileNotFoundError(
            "File sanitized belum ada. Jalankan dulu: python scripts/sanitize_corpus.py"
        )

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SANITIZED_PATH, EXPORT_PATH)
    print(f"OK: export siap upload ke Kaggle -> {EXPORT_PATH}")


if __name__ == "__main__":
    main()
