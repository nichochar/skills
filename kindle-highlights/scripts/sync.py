#!/usr/bin/env python3
"""Parse a Kindle clippings file and idempotently sync it to SQLite."""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sqlite3
from pathlib import Path

from parse_clippings import parse_file


SKILL_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB = SKILL_DIR / "data" / "highlights.db"
RAW_DIR = SKILL_DIR / "data" / "raw"

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS books (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT
);
CREATE TABLE IF NOT EXISTS highlights (
    id INTEGER PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id),
    type TEXT NOT NULL CHECK (type IN ('highlight', 'note', 'bookmark')),
    page INTEGER,
    loc_start INTEGER,
    loc_end INTEGER,
    added_at TEXT,
    text TEXT NOT NULL,
    hash TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_books_title ON books(title COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_highlights_book ON highlights(book_id);
CREATE INDEX IF NOT EXISTS idx_highlights_added ON highlights(added_at);
"""


def clipping_hash(entry: dict[str, object]) -> str:
    value = f'{entry["book_title"]}|{entry["location_start"] if entry["location_start"] is not None else ""}|{entry["text"]}'
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def get_or_create_book(connection: sqlite3.Connection, title: str, author: str | None) -> int:
    row = connection.execute(
        "SELECT id, author FROM books WHERE title = ? COLLATE NOCASE ORDER BY id LIMIT 1",
        (title,),
    ).fetchone()
    if row:
        if not row[1] and author:
            connection.execute("UPDATE books SET author = ? WHERE id = ?", (author, row[0]))
        return int(row[0])
    cursor = connection.execute("INSERT INTO books(title, author) VALUES (?, ?)", (title, author))
    return int(cursor.lastrowid)


def update_latest(source: Path) -> Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    latest = RAW_DIR / "latest.txt"
    if source.resolve() == latest.resolve(strict=False):
        return latest
    temporary = RAW_DIR / ".latest.txt.tmp"
    temporary.unlink(missing_ok=True)
    latest.unlink(missing_ok=True)
    try:
        if source.parent.resolve() == RAW_DIR.resolve():
            temporary.symlink_to(source.name)
            os.replace(temporary, latest)
        else:
            shutil.copy2(source, temporary)
            os.replace(temporary, latest)
    except OSError:
        temporary.unlink(missing_ok=True)
        shutil.copy2(source, latest)
    return latest


def sync(clippings: Path, db_path: Path = DEFAULT_DB) -> tuple[int, int, int]:
    entries, errors = parse_file(clippings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    new = skipped = 0
    try:
        connection.executescript(SCHEMA)
        with connection:
            for entry in entries:
                digest = clipping_hash(entry)
                book_id = get_or_create_book(connection, str(entry["book_title"]), entry["author"])
                existing = connection.execute("SELECT id FROM highlights WHERE hash = ?", (digest,)).fetchone()
                if existing:
                    connection.execute(
                        """UPDATE highlights SET book_id = ?, type = ?, page = ?, loc_start = ?,
                           loc_end = ?, added_at = ?, text = ? WHERE id = ?""",
                        (
                            book_id,
                            entry["type"],
                            entry["page"],
                            entry["location_start"],
                            entry["location_end"],
                            entry["added_at"],
                            entry["text"],
                            existing[0],
                        ),
                    )
                    skipped += 1
                    continue
                connection.execute(
                    """INSERT INTO highlights
                       (book_id, type, page, loc_start, loc_end, added_at, text, hash)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        book_id,
                        entry["type"],
                        entry["page"],
                        entry["location_start"],
                        entry["location_end"],
                        entry["added_at"],
                        entry["text"],
                        digest,
                    ),
                )
                new += 1
    finally:
        connection.close()
    update_latest(clippings)
    return new, skipped, len(errors)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clippings", type=Path, help="path to My Clippings.txt")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not args.clippings.is_file():
        parser.error(f"file not found: {args.clippings}")
    new, skipped, errors = sync(args.clippings.resolve(), args.db)
    print(f"{new} new, {skipped} skipped, {errors} parse errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
