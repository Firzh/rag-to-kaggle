from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

from common import getenv, project_path

load_dotenv(project_path(".env"))


def resolve_chroma_path() -> Path:
    raw = getenv("CHROMA_PATH", "./chroma_db")
    path = Path(raw)
    if not path.is_absolute():
        path = (project_path() / path).resolve()
    return path


def retrieve_context(question: str) -> list[dict]:
    model_name = getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
    query_prefix = getenv("EMBEDDING_QUERY_PREFIX", "query:")
    chroma_path = resolve_chroma_path()
    collection_name = getenv("COLLECTION_NAME", "rag_local_corpus")
    top_k = int(getenv("TOP_K_FINAL", "4"))

    embedder = SentenceTransformer(model_name)
    query_embedding = embedder.encode([f"{query_prefix} {question}"], normalize_embeddings=True)[0].astype("float32").tolist()

    client = chromadb.PersistentClient(path=str(chroma_path))
    collection = client.get_collection(collection_name)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    contexts = []
    for i, (doc, meta, dist) in enumerate(zip(
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    ), start=1):
        contexts.append({
            "rank": i,
            "text": doc,
            "metadata": meta,
            "distance": dist,
        })
    return contexts


def build_prompt(question: str, contexts: list[dict]) -> str:
    context_blocks = []
    for item in contexts:
        meta = item["metadata"]
        source = meta.get("source", "unknown")
        title = meta.get("title", "untitled")
        chunk = meta.get("chunk_index", "?")
        context_blocks.append(
            f"[S{item['rank']}] title={title}; source={source}; chunk={chunk}\n{item['text']}"
        )

    joined_context = "\n\n".join(context_blocks)

    return f"""
Anda adalah asisten RAG. Jawab hanya berdasarkan konteks yang diberikan.
Jika konteks tidak cukup, jawab: "Konteks belum cukup untuk menjawab secara valid."

Bahasa jawaban: Indonesia.
Wajib sertakan sitasi sumber dalam format [S1], [S2], dan seterusnya pada kalimat yang relevan.
Jangan membuat fakta di luar konteks.

KONTEKS:
{joined_context}

PERTANYAAN:
{question}

JAWABAN:
""".strip()


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("Pertanyaan: ").strip()

    api_key = getenv("GEMINI_API_KEY")
    model_name = getenv("GEMINI_MODEL", "gemini-2.0-flash")

    contexts = retrieve_context(question)
    prompt = build_prompt(question, contexts)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )

    print("\n" + "=" * 80)
    print("JAWABAN RAG")
    print("=" * 80)
    print(response.text)

    print("\n" + "=" * 80)
    print("SUMBER RETRIEVAL")
    print("=" * 80)
    for item in contexts:
        meta = item["metadata"]
        print(
            f"[S{item['rank']}] distance={item['distance']:.4f} | "
            f"title={meta.get('title')} | source={meta.get('source')} | chunk={meta.get('chunk_index')}"
        )


if __name__ == "__main__":
    main()
