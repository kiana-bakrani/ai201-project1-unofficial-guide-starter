from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from generate import ask


QUESTIONS = [
    {
        "question": "What do students say about William Andreopoulos for CS149?",
        "expected": "Students describe Andreopoulos as flexible and fair for CS149, but some say lectures can be boring and that students may rely more on slides, Zybooks, and homework than live lecture.",
    },
    {
        "question": "What do students say about Dominic Abucejo's CS160 class?",
        "expected": "Students describe CS160 with Dominic Abucejo as useful or easy for some students, but some criticize lectures, grading delays, structure, and the group project/teamwork experience.",
    },
    {
        "question": "What do students say about Frank Luo for CS157A?",
        "expected": "Students describe Frank Luo based on CS157A reviews, including mixed comments about industry experience, database instruction, workload, grading, lectures, and communication.",
    },
    {
        "question": "What advice do SJSU CS students give about choosing professors?",
        "expected": "Students say professor choice matters a lot, and they recommend checking student reviews, planning classes early, using resources, and expecting some self-learning.",
    },
    {
        "question": "What do students say about the overall SJSU CS department experience?",
        "expected": "Students describe the SJSU CS experience as valuable but effort-dependent, with good and bad professors, self-learning, career preparation, clubs, tutoring, research, and internships.",
    },
]


def main():
    output = ["# Evaluation Results\n"]

    for i, item in enumerate(QUESTIONS, start=1):
        print(f"Running question {i}...")
        result = ask(item["question"])

        retrieved = result["retrieved_chunks"]

        output.append(f"## Question {i}\n")
        output.append(f"**Question:** {item['question']}\n")
        output.append(f"**Expected answer:** {item['expected']}\n")
        output.append("**System answer:**\n")
        output.append(result["answer"] + "\n")
        output.append("**Sources:**\n")
        for source in result["sources"]:
            output.append(f"- {source}")
        output.append("\n**Retrieved chunks:**\n")
        for j, chunk in enumerate(retrieved, start=1):
            source = chunk["metadata"]["source"]
            score = chunk.get("adjusted_score", chunk.get("distance"))
            preview = chunk["text"][:500].replace("\n", " ")
            output.append(f"{j}. `{source}` — adjusted score: {score:.4f}")
            output.append(f"   - Preview: {preview}")
        output.append("\n**Accuracy judgment:** TODO: accurate / partially accurate / inaccurate\n")
        output.append("**Notes:** TODO: explain why.\n")

    Path("evaluation/evaluation_results.md").write_text(
        "\n".join(output),
        encoding="utf-8",
    )

    print("Saved evaluation/evaluation_results.md")


if __name__ == "__main__":
    main()
