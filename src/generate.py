import os
from dotenv import load_dotenv
from groq import Groq

from retrieve import retrieve


MODEL_NAME = "llama-3.3-70b-versatile"


def format_context(retrieved_chunks: list[dict]) -> str:
    context_blocks = []

    for i, chunk in enumerate(retrieved_chunks, start=1):
        source = chunk["metadata"]["source"]
        chunk_index = chunk["metadata"]["chunk_index"]

        context_blocks.append(
            f"[Source {i}: {source}, chunk {chunk_index}]\n"
            f"{chunk['text']}"
        )

    return "\n\n---\n\n".join(context_blocks)


def get_sources(retrieved_chunks: list[dict]) -> list[str]:
    sources = []

    for chunk in retrieved_chunks:
        source = chunk["metadata"]["source"]
        if source not in sources:
            sources.append(source)

    return sources


def ask(question: str, top_k: int = 5) -> dict:
    load_dotenv(".env")

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY missing. Add it to your .env file.")

    retrieved_chunks = retrieve(question, top_k=top_k)

    # Filter weak retrieval results so unrelated chunks do not pollute the answer.
    # Adjusted score comes from semantic distance minus keyword boost.
    filtered_chunks = [
        chunk for chunk in retrieved_chunks
        if chunk.get("adjusted_score", chunk.get("distance", 999)) <= 0.70
    ]

    # If everything is weak, give the model no context so it refuses.
    retrieved_chunks = filtered_chunks

    context = format_context(retrieved_chunks)
    sources = get_sources(retrieved_chunks)

    client = Groq(api_key=api_key)

    system_prompt = """
You are a grounded question-answering assistant for a RAG system.

Rules:
1. Answer using ONLY the provided context.
2. Do not use outside knowledge.
3. If the context does not contain enough information, say: "I don't have enough information in the provided documents to answer that."
4. Mention the relevant source file names in the answer.
5. Do not invent facts, professors, courses, ratings, dates, or sources.
6. Keep the answer concise and directly tied to the retrieved student reviews/comments.
""".strip()

    user_prompt = f"""
Question:
{question}

Retrieved context:
{context}

Answer:
""".strip()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )

    answer = response.choices[0].message.content

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "retrieved_chunks": retrieved_chunks,
    }


def print_answer(question: str):
    result = ask(question)

    print("=" * 80)
    print("QUESTION:")
    print(result["question"])
    print("=" * 80)
    print("ANSWER:")
    print(result["answer"])
    print()
    print("SOURCES:")
    for source in result["sources"]:
        print(f"- {source}")


if __name__ == "__main__":
    test_questions = [
        "What do students say about William Andreopoulos for CS149?",
        "What do students say about Dominic Abucejo's CS160 class?",
        "What do students say about a biology professor?",
    ]

    for question in test_questions:
        print_answer(question)
        print()
