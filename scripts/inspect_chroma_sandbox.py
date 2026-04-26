from __future__ import annotations

from pathlib import Path
import chromadb

from common import getenv, project_path


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)

    if not path.is_absolute():
        path = (project_path() / path).resolve()

    return path


def main() -> None:
    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_kaggle_sandbox")

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)

    count = collection.count()

    print(f"Chroma path     : {chroma_path}")
    print(f"Collection name : {collection_name}")
    print(f"Total chunks    : {count}")

    result = collection.get(
        limit=5,
        include=["documents", "metadatas"],
    )

    for i, doc_id in enumerate(result["ids"]):
        print("=" * 80)
        print("ID:", doc_id)
        print("Metadata:", result["metadatas"][i])
        print("Document:")
        print(result["documents"][i][:1000])


if __name__ == "__main__":
    main()
