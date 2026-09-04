# Stacks — Book Browser & Recommendation Assistant

A small app for browsing a book dataset and asking a RAG-based agent for
personalized recommendations.

## Features

- **Browse & search** — filter books by title, author, or publication year;
  click a card to expand its summary.
- **Ask for recommendations** — chat with an agent that retrieves relevant
  books from a vector index and explains why each one fits your request.

## Web app

The frontend is a static HTML/CSS/JS page served by a FastAPI backend.
FastAPI exposes two endpoints: `GET /api/books` (search over the CSV
dataset) and `POST /api/chat` (forwards the message to the RAG agent below
and returns its response as HTML). See `main.py` and `static/` for the
implementation details.

## Recommendation engine (RAG)

The `/api/chat` endpoint is backed by a retrieval-augmented generation
agent built with:

```
sentence-transformers   # embedding + cross-encoder reranking
transformers, torch     # response generation
faiss                   # vector similarity search
datasets                # loading the book corpus
numpy, time, yaml       # utilities and config loading
```

**Models**

| Role | Model |
|---|---|
| Embedding (encoder) | [`Qwen/Qwen3-Embedding-0.6B`](https://huggingface.co/Qwen/Qwen3-Embedding-0.6B) |
| Reranker | [`BAAI/bge-reranker-base`](https://huggingface.co/BAAI/bge-reranker-base) |
| Response generation | [`Qwen/Qwen3-8B`](https://huggingface.co/Qwen/Qwen3-8B) |

**Pipeline**

1. The user's message is embedded with the Qwen3 encoder and used to search
   a FAISS index of book embeddings.
2. The top candidates are reranked with the BAAI cross-encoder to surface
   the most relevant matches.
3. The best-matching books are inserted into a prompt, and Qwen3-8B
   generates the final natural-language recommendation.

### Dataset

Books are sourced from
[`textminr/cmu-book-summaries`](https://huggingface.co/datasets/textminr/cmu-book-summaries)
on Hugging Face.

### Configuration

Most of the RAG setup is controlled by a YAML config file rather than
hardcoded values:

```yaml
vectorDBindex: "books.index"           # path to the FAISS index file
metadata: "books_metadata"             # path to the book metadata store (titles, authors, etc.)
Embedding_model_max_seq_length: 512    # max tokens the encoder will embed per book/query
reranker_depth: 20                     # how many top FAISS matches get passed to the reranker
nb_relevant_suggestions: 3             # how many reranked books get passed to the generator as context
agent_role: "book recommendation assistant"
generation_model_max_new_tokens: 512   # response length cap for Qwen3-8B
generation_model_temperature: 0.7      # sampling temperature for generation
notes: "
    For each recommendation:
      - Give the title and author.
      - Briefly explain why it matches the user's request.

    If none of the books are a good match, say so instead of inventing recommendations.
    If the user didn't ask for a recommendation, ignore the retrieved books.
    If the retrieved books do not have an author or any other missing information, say so and do not include them in the recommendations.
    "
```

- **`vectorDBindex` / `metadata`** — where the prebuilt FAISS index and its
  matching book metadata live on disk, so they're loaded once at startup
  instead of rebuilt per request.
- **`Embedding_model_max_seq_length`** — caps how much text the encoder
  reads when embedding a book or a query; longer summaries get truncated.
- **`reranker_depth`** — the retrieval fan-out: FAISS returns this many
  nearest neighbors before the cross-encoder narrows them down.
- **`nb_relevant_suggestions`** — how many of the reranked books actually
  get handed to the generation model as context.
- **`agent_role`** — sets the agent's persona in the system prompt.
- **`generation_model_max_new_tokens` / `generation_model_temperature`** —
  standard generation controls: response length ceiling and
  randomness/creativity of Qwen3-8B's output.
- **`notes`** — instructions appended to the prompt that keep the agent
  grounded: cite title + author, explain the match, admit when nothing
  fits, ignore retrieval when no recommendation was asked for, and skip
  books with missing metadata rather than guessing.

## Project structure

```
bookapp/
├── main.py           # FastAPI app: /api/books, /api/chat, serves static/
├── books.csv          # book dataset (title, author, pub_year, summary)
├── static/
│   ├── index.html     # Library / Recommend tabs
│   ├── style.css
│   └── app.js
└── README.md
```

## Setup

```bash
pip install fastapi uvicorn markdown sentence-transformers transformers torch faiss-cpu datasets pyyaml
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000`.

## Screenshots

_Coming soon._
