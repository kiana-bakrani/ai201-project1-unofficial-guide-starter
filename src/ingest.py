from pathlib import Path
import json
import re


DOCUMENTS_DIR = Path("documents")
OUTPUT_PATH = Path("data/chunks.json")


def clean_text(text: str) -> str:
    """
    Basic cleaning for manually collected .txt documents.
    Removes placeholder text and normalizes whitespace.
    """
    text = text.replace("PASTE STUDENT REVIEW TEXT HERE.", "")
    text = text.replace("PASTE RELEVANT REDDIT POST OR COMMENT TEXT HERE.", "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def split_into_sections(text: str) -> list[str]:
    """
    Split text into review/comment sections.

    The documents use labels like:
    Review 1:
    Post/Comment 1:

    This keeps each review or Reddit comment mostly intact.
    """
    marker_pattern = r"(?=(?:Review|Post/Comment)\s+\d+:)"
    parts = re.split(marker_pattern, text)

    header = parts[0].strip()
    sections = []

    for part in parts[1:]:
        part = part.strip()
        if not part:
            continue

        # Attach header metadata to each chunk so the chunk has source/professor/course context.
        section = f"{header}\n\n{part}".strip()
        sections.append(section)

    # If no review/comment markers exist, keep the whole cleaned document.
    if not sections and text.strip():
        sections.append(text.strip())

    return sections


def split_long_chunk(text: str, max_chars: int = 900, overlap: int = 150) -> list[str]:
    """
    If a section is unusually long, split it into overlapping character chunks.
    Most of our reviews/comments should stay as single chunks.
    """
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + max_chars
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def load_and_chunk_documents() -> list[dict]:
    """
    Load every .txt file in documents/, clean it, split it into chunks,
    and attach metadata for source attribution.
    """
    all_chunks = []

    for path in sorted(DOCUMENTS_DIR.glob("*.txt")):
        raw_text = path.read_text(encoding="utf-8")
        cleaned = clean_text(raw_text)
        sections = split_into_sections(cleaned)

        # Add one document-level overview chunk so retrieval can match broad questions
        # like "What do students say about the SJSU CS department?"
        overview = cleaned[:1200].strip()

        chunk_index = 0

        if overview:
            all_chunks.append(
                {
                    "id": f"{path.stem}_{chunk_index}",
                    "text": overview,
                    "metadata": {
                        "source": path.name,
                        "chunk_index": chunk_index,
                        "chunk_type": "document_overview",
                    },
                }
            )
            chunk_index += 1

        for section in sections:
            for chunk_text in split_long_chunk(section):
                if len(chunk_text.strip()) < 30:
                    continue

                all_chunks.append(
                    {
                        "id": f"{path.stem}_{chunk_index}",
                        "text": chunk_text,
                        "metadata": {
                            "source": path.name,
                            "chunk_index": chunk_index,
                        },
                    }
                )
                chunk_index += 1

    return all_chunks


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    chunks = load_and_chunk_documents()

    OUTPUT_PATH.write_text(
        json.dumps(chunks, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Loaded documents from: {DOCUMENTS_DIR}")
    print(f"Saved chunks to: {OUTPUT_PATH}")
    print(f"Total chunks: {len(chunks)}")
    print()

    print("Sample chunks:")
    print("=" * 80)

    for chunk in chunks[:5]:
        print(f"ID: {chunk['id']}")
        print(f"Source: {chunk['metadata']['source']}")
        print(chunk["text"][:700])
        print("-" * 80)


if __name__ == "__main__":
    main()
