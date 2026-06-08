from pathlib import Path
import json
import shutil

import chromadb
from sentence_transformers import SentenceTransformer
import re


CHUNKS_PATH = Path("data/chunks.json")
CHROMA_PATH = Path("chroma_db")
COLLECTION_NAME = "sjsu_cs_guide"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def load_chunks() -> list[dict]:
    if not CHUNKS_PATH.exists():
        raise FileNotFoundError(
            f"{CHUNKS_PATH} does not exist. Run: python src/ingest.py"
        )

    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_client():
    return chromadb.PersistentClient(path=str(CHROMA_PATH))


def build_vector_store(reset: bool = True):
    """
    Embed chunks and store them in ChromaDB.

    reset=True deletes the old local ChromaDB folder so the store matches
    the latest chunks.json exactly.
    """
    if reset and CHROMA_PATH.exists():
        shutil.rmtree(CHROMA_PATH)

    chunks = load_chunks()
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)

    ids = [chunk["id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    print(f"Loaded {len(chunks)} chunks.")
    print(f"Embedding model: {EMBEDDING_MODEL_NAME}")
    print("Creating embeddings...")

    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    client = get_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    print(f"Saved {collection.count()} chunks to ChromaDB collection: {COLLECTION_NAME}")


def keyword_boost(query: str, text: str) -> float:
    """
    Simple keyword boost for exact names, course numbers, and important terms.
    This helps rare professor names like "Dominic Abucejo" that semantic search
    may not rank highly on its own.
    """
    query_terms = re.findall(r"[A-Za-z0-9]+", query.lower())
    text_lower = text.lower()

    boost = 0.0

    for term in query_terms:
        if len(term) < 3:
            continue
        if term in text_lower:
            boost += 0.08

    return boost


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    """
    Return top-k chunks for a query, including source metadata and distance.
    Lower adjusted_score is better.
    """
    model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    query_embedding = model.encode([query]).tolist()[0]

    client = get_client()
    collection = client.get_collection(name=COLLECTION_NAME)

    # Retrieve more than we need, then rerank using keyword matches.
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=20,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []

    for doc, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        boost = keyword_boost(query, doc)
        adjusted_score = distance - boost

        retrieved.append(
            {
                "text": doc,
                "metadata": metadata,
                "distance": distance,
                "keyword_boost": boost,
                "adjusted_score": adjusted_score,
            }
        )

    retrieved.sort(key=lambda item: item["adjusted_score"])
    return retrieved[:top_k]


def print_results(query: str, top_k: int = 5):
    print("=" * 80)
    print(f"Query: {query}")
    print("=" * 80)

    results = retrieve(query, top_k=top_k)

    for i, result in enumerate(results, start=1):
        print(f"\nResult {i}")
        print(f"Source: {result['metadata']['source']}")
        print(f"Chunk index: {result['metadata']['chunk_index']}")
        print(f"Distance: {result['distance']:.4f}")
        print(f"Keyword boost: {result.get('keyword_boost', 0):.4f}")
        print(f"Adjusted score: {result.get('adjusted_score', result['distance']):.4f}")
        print("-" * 80)
        print(result["text"][:1000])


if __name__ == "__main__":
    build_vector_store(reset=True)

    test_queries = [
        "What do students say about William Andreopoulos for CS149?",
        "What do students say about Dominic Abucejo CS160?",
        "What advice do SJSU CS students give about choosing professors?",
    ]

    for query in test_queries:
        print_results(query, top_k=5)
        print()
