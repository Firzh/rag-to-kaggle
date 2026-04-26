from __future__ import annotations

import hashlib
import re
from pathlib import Path

from common import project_path, write_jsonl

RAW_DIR = project_path("data", "raw")
SANITIZED_PATH = project_path("data", "sanitized", "corpus_sanitized.jsonl")

ALLOWED_EXT = {".txt", ".md"}

SENSITIVE_PATTERNS = [
    # API keys / token kasar
    (re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[\w\-\.]{12,}['\"]?"), "[REDACTED_CREDENTIAL]"),
    # Email
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    # Nomor HP Indonesia sederhana
    (re.compile(r"(?<!\d)(?:\+62|62|0)8[1-9][0-9]{7,11}(?!\d)"), "[REDACTED_PHONE]"),
    # NIK 16 digit sederhana
    (re.compile(r"(?<!\d)\d{16}(?!\d)"), "[REDACTED_16_DIGIT_ID]"),
]


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    for pattern, repl in SENSITIVE_PATTERNS:
        text = pattern.sub(repl, text)

    return text.strip()


def stable_doc_id(path: Path, text: str) -> str:
    raw = f"{path.name}:{hashlib.sha1(text.encode('utf-8')).hexdigest()[:16]}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def main() -> None:
    if not RAW_DIR.exists():
        RAW_DIR.mkdir(parents=True, exist_ok=True)

    rows = []
    files = sorted([p for p in RAW_DIR.rglob("*") if p.is_file() and p.suffix.lower() in ALLOWED_EXT])

    if not files:
        sample = RAW_DIR / "sample_public_dummy.md"
        sample.write_text(
            "# Contoh Corpus Dummy\n\nIni contoh teks publik/dummy untuk mengetes pipeline RAG lokal dan Kaggle.\n",
            encoding="utf-8",
        )
        files = [sample]

    for path in files:
        raw_text = path.read_text(encoding="utf-8", errors="ignore")
        text = clean_text(raw_text)
        if not text:
            continue

        rows.append({
            "doc_id": stable_doc_id(path, text),
            "title": path.stem,
            "source": str(path.relative_to(RAW_DIR)).replace("\\", "/"),
            "text": text,
            "metadata": {
                "file_name": path.name,
                "file_ext": path.suffix.lower(),
                "sanitized": True,
            },
        })

    write_jsonl(SANITIZED_PATH, rows)
    print(f"OK: {len(rows)} dokumen tersanitasi -> {SANITIZED_PATH}")


if __name__ == "__main__":
    main()
