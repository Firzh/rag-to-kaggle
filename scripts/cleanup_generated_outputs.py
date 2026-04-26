from __future__ import annotations

import argparse
import shutil
from pathlib import Path


DEFAULT_FILE_PATTERNS = [
    "data/sanitized/*.jsonl",
    "data/export/*.jsonl",
    "data/import/*.pre_k2.bak",
    "outputs/*.csv",
    "outputs/*.json",
    "outputs/*.jsonl",
    "outputs/*.md",
    "outputs/*.npy",
    "outputs/*.parquet",
    "outputs/*.txt",
    "*.log",
]

IMPORT_FILE_PATTERNS = [
    "data/import/*.csv",
    "data/import/*.json",
    "data/import/*.jsonl",
    "data/import/*.md",
    "data/import/*.npy",
    "data/import/*.parquet",
]

CACHE_DIR_PATTERNS = [
    ".pytest_cache",
    "**/__pycache__",
    "**/.ipynb_checkpoints",
]

CHROMA_DIR_PATTERNS = [
    "chroma_db",
]

PROTECTED_EXACT = {
    ".env",
    ".env.example",
    ".gitignore",
    "README.md",
    "requirements.txt",
}

PROTECTED_PREFIXES = (
    "docs/",
    "configs/",
    "scripts/",
    "notebooks/",
    "data/raw/",
)


def normalize_relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def is_protected(path: Path, root: Path) -> bool:
    try:
        rel = normalize_relative(path, root)
    except ValueError:
        return True

    if rel in PROTECTED_EXACT:
        return True

    return any(rel.startswith(prefix) for prefix in PROTECTED_PREFIXES)


def resolve_file_matches(patterns: list[str], root: Path) -> list[Path]:
    matches: list[Path] = []

    for pattern in patterns:
        matches.extend(root.glob(pattern))

    files = [
        path for path in matches
        if path.is_file() and not is_protected(path, root)
    ]

    return sorted(set(path.resolve() for path in files))


def resolve_dir_matches(patterns: list[str], root: Path) -> list[Path]:
    matches: list[Path] = []

    for pattern in patterns:
        matches.extend(root.glob(pattern))

    dirs = [
        path for path in matches
        if path.is_dir() and not is_protected(path, root)
    ]

    return sorted(set(path.resolve() for path in dirs), key=lambda p: len(str(p)), reverse=True)


def print_plan(files: list[Path], dirs: list[Path], root: Path, dry_run: bool) -> None:
    action = "would delete" if dry_run else "deleted"

    if not files and not dirs:
        print("OK: tidak ada generated output yang perlu dibersihkan.")
        return

    print("Generated Output Cleanup")
    print("=" * 80)

    for path in files:
        print(f"{action:12} file  {normalize_relative(path, root)}")

    for path in dirs:
        print(f"{action:12} dir   {normalize_relative(path, root)}")

    print("=" * 80)

    if dry_run:
        print("Dry-run mode. Jalankan dengan --yes untuk benar-benar menghapus.")
    else:
        print(f"Deleted files: {len(files)}")
        print(f"Deleted dirs : {len(dirs)}")


def cleanup_generated_outputs(
    *,
    dry_run: bool,
    include_import: bool,
    include_chroma: bool,
    include_cache: bool,
) -> int:
    root = Path.cwd()

    file_patterns = list(DEFAULT_FILE_PATTERNS)
    dir_patterns: list[str] = []

    if include_import:
        file_patterns.extend(IMPORT_FILE_PATTERNS)

    if include_cache:
        dir_patterns.extend(CACHE_DIR_PATTERNS)

    if include_chroma:
        dir_patterns.extend(CHROMA_DIR_PATTERNS)

    files = resolve_file_matches(file_patterns, root)
    dirs = resolve_dir_matches(dir_patterns, root)

    print_plan(files, dirs, root, dry_run)

    if dry_run:
        return 0

    deleted_count = 0

    for path in files:
        path.unlink(missing_ok=True)
        deleted_count += 1

    for path in dirs:
        shutil.rmtree(path, ignore_errors=True)
        deleted_count += 1

    return deleted_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Clean generated Kaggle/RAG hook outputs without touching raw data, "
            "docs, configs, scripts, notebooks, or environment files."
        )
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Benar-benar hapus file. Tanpa flag ini hanya dry-run.",
    )
    parser.add_argument(
        "--include-import",
        action="store_true",
        help="Ikut bersihkan file hasil Kaggle di data/import.",
    )
    parser.add_argument(
        "--include-chroma",
        action="store_true",
        help="Ikut hapus folder chroma_db lokal.",
    )
    parser.add_argument(
        "--include-cache",
        action="store_true",
        help="Ikut hapus __pycache__, .pytest_cache, dan .ipynb_checkpoints.",
    )

    args = parser.parse_args()

    cleanup_generated_outputs(
        dry_run=not args.yes,
        include_import=args.include_import,
        include_chroma=args.include_chroma,
        include_cache=args.include_cache,
    )


if __name__ == "__main__":
    main()
