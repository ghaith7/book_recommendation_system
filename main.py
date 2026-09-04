"""
Minimal FastAPI backend for the book browser + recommendation chat app.

Endpoints:
  GET  /api/books         -> list books, optionally filtered by title/author/year
  POST /api/chat          -> stubbed recommendation chatbot response
  GET  /                  -> serves the frontend (static/index.html)
"""

import csv
from pathlib import Path
import markdown
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from RagAgent import RagAgent


BASE_DIR = Path(__file__).parent

CSV_PATH = BASE_DIR / "books.csv"

rag_agent = RagAgent("./rag_agent_config.yaml")
app = FastAPI(title="Book Browser API")


def load_books() -> list[dict]:
    """Read the CSV dataset into a list of dicts once at startup."""
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


BOOKS = load_books()


@app.get("/api/books")
def get_books(
    title: str = Query("", description="Filter by title (partial match)"),
    author: str = Query("", description="Filter by author (partial match)"),
    year: str = Query("", description="Filter by publication year (exact or partial match)"),
):
    """Return books matching the given filters. Any empty filter is ignored."""
    title_q = title.strip().lower()
    author_q = author.strip().lower()
    year_q = year.strip()

    results = []
    for book in BOOKS:
        if title_q and title_q not in book["title"].lower():
            continue
        if author_q and author_q not in book["author"].lower():
            continue
        if year_q and year_q not in book["pub_year"]:
            continue
        results.append(book)

    return {"count": len(results), "books": results}


class ChatMessage(BaseModel):
    message: str


@app.post("/api/chat")
def chat(payload: ChatMessage):
    prompt = rag_agent.query2prompt(payload.message)
    response = rag_agent.generate_response(prompt)
    
    html_response = markdown.markdown(response)
    return {"response": html_response}


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
