# The Unofficial Guide to SJSU CS Professors and Courses

## Project Overview

This project is a Retrieval-Augmented Generation (RAG) system for unofficial SJSU Computer Science professor and course reviews. A user can ask a plain-language question about professors, courses, workload, grading, teaching style, or department experience, and the system retrieves relevant student-generated documents before generating a grounded answer.

The goal is to make scattered student knowledge easier to search. Official SJSU course catalogs explain course descriptions, but they do not summarize student experiences with professors, exams, projects, grading, lecture quality, or class structure.

## Domain and Document Sources

Domain: SJSU Computer Science professor and course reviews.

The source documents are stored in the `documents/` folder. They include Rate My Professors reviews and Reddit discussions.

1. `documents/rmp_william_andreopoulos.txt` — Rate My Professors reviews for William Andreopoulos, especially CS149.
2. `documents/rmp_dominic_abucejo.txt` — Rate My Professors reviews for Dominic Abucejo, especially CS160.
3. `documents/rmp_frank_luo.txt` — Rate My Professors reviews for Frank Luo, especially CS157A.
4. `documents/reddit_andreopoulos_cs_courses.txt` — Reddit discussion about William Andreopoulos for CS courses.
5. `documents/reddit_cs149_professors.txt` — Reddit discussion comparing CS149 professors.
6. `documents/reddit_cs_department.txt` — Reddit discussion about the SJSU CS department.
7. `documents/reddit_cs_cmpe_professors.txt` — Reddit discussion about CS and CMPE professor experiences.
8. `documents/reddit_sjsu_cs_rank_discussion.txt` — Reddit discussion about SJSU CS reputation and student performance.
9. `documents/reddit_spartans_ultimate_guide.txt` — Reddit guide with general SJSU student advice and professor-selection advice.
10. `documents/reddit_cs_instructor_help.txt` — Reddit discussion asking for help choosing CS instructors.

## Document Ingestion

The ingestion script is `src/ingest.py`.

It loads all `.txt` files from the `documents/` folder, removes placeholder text, normalizes whitespace, and saves structured chunks to `data/chunks.json`.

The script produced 57 chunks from 10 source documents.

## Chunking Strategy

I used review/comment-based chunking instead of splitting every fixed number of characters. Since the corpus is mostly short Rate My Professors reviews and Reddit comments, each review or comment usually contains one complete idea.

Each chunk keeps the source header with the review/comment so that retrieved text still contains professor, course, source, and topic context. If a section is unusually long, the script can split it into overlapping chunks with a maximum length of 900 characters and 150 characters of overlap.

This strategy fits the documents because reviews are short and opinion-based. Very small chunks could lose professor or course context. Very large chunks could mix unrelated topics such as grading, internships, teaching style, and department reputation.

## Sample Chunks

### Sample Chunk 1

Source: `reddit_andreopoulos_cs_courses.txt`

> Post/Comment 5: Overall, the thread suggests Andreopoulos is considered flexible and fair for CS149, with some students emphasizing that deadlines, assignments, and projects are manageable if students keep up with the work.

### Sample Chunk 2

Source: `rmp_dominic_abucejo.txt`

> Review 4: Course: CS160. Rating: 5.0. Difficulty: 3.0. Text: A pretty chill class. Only one project throughout the entire semester.

### Sample Chunk 3

Source: `rmp_frank_luo.txt`

> Review 1: Course: CS157A. Rating: 4.0. Difficulty: 2.0. Text: He's worked in the industry for years and it shows. He doesn't just read off slides; he explains how things actually work in the real world.

### Sample Chunk 4

Source: `reddit_spartans_ultimate_guide.txt`

> Post/Comment 6: The guide suggests that SJSU CS students should work strategically: choose professors carefully, plan degree requirements early, use resources, and focus on practical career preparation.

### Sample Chunk 5

Source: `reddit_cs_department.txt`

> Post/Comment 3: One commenter said the SJSU CS department has good and bad professors. They said students will encounter both very difficult and very easy professors, but most professors will work with students.

## Embedding Model and Vector Store

Embedding model: `sentence-transformers/all-MiniLM-L6-v2`

Vector store: `ChromaDB`

I chose `all-MiniLM-L6-v2` because it runs locally, is free, and is fast enough for a small project. For a production system, I would compare embedding models based on accuracy, latency, cost, context length, multilingual support, and whether the system needs to run locally or through an API.

## Retrieval Approach

The retrieval code is in `src/retrieve.py`.

The system retrieves top chunks from ChromaDB using semantic similarity. I started with `top_k = 5`.

After testing, I added keyword boosting/reranking because pure semantic search struggled with rare professor names such as “Dominic Abucejo.” The reranking step rewards exact matches for names, course numbers, and important query terms.

## Retrieval Test Results

### Query 1

Question: What do students say about William Andreopoulos for CS149?

Top retrieved chunks came from `reddit_andreopoulos_cs_courses.txt`.

Why relevant: the chunks directly mention William Andreopoulos, CS149, flexible deadlines, fair assignments, fair grading, and student opinions comparing him to other CS149 professors.

### Query 2

Question: What do students say about Dominic Abucejo's CS160 class?

Top retrieved chunks came from `rmp_dominic_abucejo.txt`.

Why relevant: the chunks directly mention Dominic Abucejo and CS160, including comments about the class being easy or chill, lectures, grading, projects, quizzes, and structure.

### Query 3

Question: What advice do SJSU CS students give about choosing professors?

Top retrieved chunks came from `reddit_spartans_ultimate_guide.txt` and `reddit_cs_instructor_help.txt`.

Why relevant: the chunks discuss choosing professors carefully, planning classes early, using student advice, and checking unofficial professor information.

## Grounded Generation

The generation code is in `src/generate.py`.

The system uses Groq with `llama-3.3-70b-versatile`.

Grounding is enforced through the system prompt. The model is instructed to:

1. Answer using only the retrieved context.
2. Not use outside knowledge.
3. Say it does not have enough information if the documents do not answer the question.
4. Mention relevant source filenames.
5. Avoid inventing facts, professors, courses, ratings, dates, or sources.

The code also returns source filenames from retrieved chunk metadata.

## Example Responses

### Example 1

Question: What do students say about William Andreopoulos for CS149?

System response summary: Students describe William Andreopoulos for CS149 as a decent and flexible professor. They mention fair assignments, fair grading, deadline extensions, and manageable work if students keep up.

Source: `reddit_andreopoulos_cs_courses.txt`

### Example 2

Question: What do students say about Dominic Abucejo's CS160 class?

System response summary: Students have mixed opinions. Some describe the class as easy or chill, while others criticize lectures, grading delays, structure, and project/teamwork issues.

Source: `rmp_dominic_abucejo.txt`

### Out-of-Scope Example

Question: What do students say about a biology professor?

System response: I don't have enough information in the provided documents to answer that.

## Query Interface

The interface is implemented in `app.py`.

It uses Gradio. The user enters a question in a textbox, clicks “Ask,” and receives:

1. A generated answer.
2. A list of retrieved source files.

To run the interface:

`python app.py`

Then open the local Gradio URL, usually:

`http://127.0.0.1:7860`

## Sample Interaction Transcript

Input: What do students say about William Andreopoulos for CS149?

Output: Students describe William Andreopoulos as flexible and fair for CS149. Retrieved comments mention deadline extensions, fair assignments and projects, fair grading, and manageable work.

Retrieved from: `reddit_andreopoulos_cs_courses.txt`

## Evaluation Report

The full evaluation report is in `evaluation/evaluation_results.md`.

I evaluated the system on five test questions:

1. What do students say about William Andreopoulos for CS149?
2. What do students say about Dominic Abucejo's CS160 class?
3. What do students say about Frank Luo for CS157A?
4. What advice do SJSU CS students give about choosing professors?
5. What do students say about the overall SJSU CS department experience?

Each evaluation entry includes the question, expected answer, system response, retrieved chunks, sources, accuracy judgment, and notes.

## Failure Case

The main failure happened before keyword boosting was added.

Question: What do students say about Dominic Abucejo's CS160 class?

Failure: Pure semantic retrieval returned mostly unrelated chunks about Ramin Moazeni, Frank Luo, and William Andreopoulos.

Cause: The embedding search did not strongly match the rare professor name “Dominic Abucejo” and course number “CS160.”

Pipeline stage: Retrieval failure.

Fix: I added keyword boosting/reranking in `src/retrieve.py`. After this fix, the Dominic Abucejo query returned `rmp_dominic_abucejo.txt` as the top results.

## Spec Reflection

One way the spec helped was by forcing me to decide the domain, documents, chunking strategy, retrieval approach, and evaluation questions before writing the code. This made the implementation more focused because the ingestion and retrieval code were built around review/comment-style documents.

One way the implementation diverged from the original spec was retrieval. I initially planned to use semantic search only, but testing showed that semantic search struggled with rare professor names and course numbers. I added keyword boosting to improve exact-match retrieval.

## AI Usage

I used AI assistance for specific implementation tasks, while reviewing and testing the code myself.

First, I used AI to help design the ingestion and chunking pipeline. I gave it my document structure and chunking strategy, and used the generated code as a starting point. I verified the output by printing random chunks and checking that they were readable and self-contained.

Second, I used AI to help implement the retrieval and generation pipeline. I asked for code using `sentence-transformers`, ChromaDB, and Groq. I then tested retrieval on my evaluation questions and changed the code by adding keyword boosting after I found a retrieval failure.

Third, I used AI to help create the Gradio interface. I checked that the interface had a clear question input, answer output, and source output before using it for the demo.

## How to Run the Project

Create and activate a virtual environment:

`python3 -m venv .venv`

`source .venv/bin/activate`

Install dependencies:

`pip install -r requirements.txt`

Create a `.env` file:

`GROQ_API_KEY=your_key_here`

Run ingestion:

`python src/ingest.py`

Build vector store and test retrieval:

`python src/retrieve.py`

Run generation test:

`python src/generate.py`

Run the interface:

`python app.py`

Run evaluation:

`python evaluation/run_evaluation.py`

## Repository Structure

```text
app.py
README.md
planning.md
requirements.txt
documents/
data/
src/
  __init__.py
  ingest.py
  retrieve.py
  generate.py
evaluation/
  run_evaluation.py
  evaluation_results.md
```
