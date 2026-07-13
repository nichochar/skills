#!/usr/bin/env python3
"""Shared database and formatting helpers for the Kindle highlights tools."""

from __future__ import annotations

import difflib
import re
import sqlite3
import unicodedata
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
DB_PATH = SKILL_DIR / "data" / "highlights.db"
OUTPUT_DIR = SKILL_DIR / "output"


def connect(db_path: Path = DB_PATH) -> sqlite3.Connection:
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}\nRun sync.py first.")
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def find_book(connection: sqlite3.Connection, query: str) -> sqlite3.Row:
    books = connection.execute(
        "SELECT id, title, author FROM books ORDER BY title COLLATE NOCASE"
    ).fetchall()
    if not books:
        raise SystemExit("No books found. Run sync.py first.")
    needle = query.casefold().strip()
    exact = [book for book in books if book["title"].casefold() == needle]
    if exact:
        return exact[0]
    contains = [book for book in books if needle in book["title"].casefold()]
    if contains:
        return min(contains, key=lambda book: len(book["title"]))
    titles = [book["title"] for book in books]
    matches = difflib.get_close_matches(query, titles, n=1, cutoff=0.35)
    if not matches:
        raise SystemExit(f'No book title matched "{query}".')
    return next(book for book in books if book["title"] == matches[0])


def highlight_rows(
    connection: sqlite3.Connection,
    *,
    book: str | None = None,
    search: str | None = None,
    all_books: bool = False,
) -> list[sqlite3.Row]:
    base = """
        SELECT h.*, b.title, b.author
        FROM highlights AS h
        JOIN books AS b ON b.id = h.book_id
    """
    parameters: list[object] = []
    if book:
        matched = find_book(connection, book)
        base += " WHERE b.id = ?"
        parameters.append(matched["id"])
    elif search:
        base += " WHERE h.text LIKE ? COLLATE NOCASE OR b.title LIKE ? COLLATE NOCASE"
        parameters.extend((f"%{search}%", f"%{search}%"))
    elif not all_books:
        raise ValueError("Select a book, search query, or all books")
    base += " ORDER BY b.title COLLATE NOCASE, COALESCE(h.added_at, ''), h.id"
    return connection.execute(base, parameters).fetchall()


def slugify(value: str, fallback: str = "highlights") -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:80] or fallback


def location_label(row: sqlite3.Row) -> str:
    bits = []
    if row["page"] is not None:
        bits.append(f'page {row["page"]}')
    if row["loc_start"] is not None:
        location = str(row["loc_start"])
        if row["loc_end"] is not None and row["loc_end"] != row["loc_start"]:
            location += f'-{row["loc_end"]}'
        bits.append(f"location {location}")
    if row["added_at"]:
        bits.append(row["added_at"].replace("T", " "))
    return " · ".join(bits)
