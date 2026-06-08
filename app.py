import sys
from pathlib import Path

import gradio as gr

# Allow app.py to import files from src/
sys.path.append(str(Path(__file__).parent / "src"))

from generate import ask


def handle_query(question):
    if not question.strip():
        return "Please enter a question.", ""

    try:
        result = ask(question)

        answer = result["answer"]

        if result["sources"]:
            sources = "\n".join(f"- {source}" for source in result["sources"])
        else:
            sources = "No sources retrieved."

        return answer, sources

    except Exception as e:
        return f"Error: {e}", ""


with gr.Blocks(title="Unofficial Guide to SJSU CS") as demo:
    gr.Markdown("# The Unofficial Guide to SJSU CS Professors and Courses")
    gr.Markdown(
        "Ask a question about the collected student reviews and Reddit discussions. "
        "Answers are generated only from the retrieved source documents."
    )

    question = gr.Textbox(
        label="Your question",
        placeholder="Example: What do students say about William Andreopoulos for CS149?",
        lines=2,
    )

    ask_button = gr.Button("Ask")

    answer = gr.Textbox(label="Answer", lines=10)
    sources = gr.Textbox(label="Retrieved from", lines=5)

    ask_button.click(handle_query, inputs=question, outputs=[answer, sources])
    question.submit(handle_query, inputs=question, outputs=[answer, sources])


if __name__ == "__main__":
    demo.launch()
