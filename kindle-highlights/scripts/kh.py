#!/usr/bin/env python3
"""Query the local Kindle highlights database."""

from __future__ import annotations

import argparse
import sqlite3
import textwrap

from _common import connect, find_book, location_label


def print_highlight(row: sqlite3.Row, include_book: bool = False) -> None:
    if include_book:
        author = f' — {row["author"]}' if row["author"] else ""
        print(f'\n{row["title"]}{author}')
    label = location_label(row)
    print(f'[{row["type"]}{" · " + label if label else ""}]')
    print(textwrap.fill(row["text"] or "(no text)", width=100, replace_whitespace=False))


def command_books(connection: sqlite3.Connection, _args: argparse.Namespace) -> None:
    rows = connection.execute(
        """SELECT b.title, b.author, COUNT(h.id) AS count
           FROM books b LEFT JOIN highlights h ON h.book_id = b.id
           GROUP BY b.id ORDER BY b.title COLLATE NOCASE"""
    ).fetchall()
    for row in rows:
        author = f' — {row["author"]}' if row["author"] else ""
        print(f'{row["count"]:4}  {row["title"]}{author}')
    print(f"\n{len(rows)} books")


def command_book(connection: sqlite3.Connection, args: argparse.Namespace) -> None:
    book = find_book(connection, args.title)
    rows = connection.execute(
        "SELECT * FROM highlights WHERE book_id = ? ORDER BY COALESCE(added_at, ''), id",
        (book["id"],),
    ).fetchall()
    author = f' — {book["author"]}' if book["author"] else ""
    print(f'{book["title"]}{author} ({len(rows)} clippings)')
    for row in rows:
        print()
        print_highlight(row)


def command_search(connection: sqlite3.Connection, args: argparse.Namespace) -> None:
    rows = connection.execute(
        """SELECT h.*, b.title, b.author FROM highlights h
           JOIN books b ON b.id = h.book_id
           WHERE h.text LIKE ? COLLATE NOCASE OR b.title LIKE ? COLLATE NOCASE
           ORDER BY COALESCE(h.added_at, ''), h.id""",
        (f"%{args.query}%", f"%{args.query}%"),
    ).fetchall()
    print(f'{len(rows)} matches for "{args.query}"')
    for row in rows:
        print_highlight(row, include_book=True)


def command_random(connection: sqlite3.Connection, args: argparse.Namespace) -> None:
    parameters: tuple[object, ...] = ()
    where = ""
    if args.book:
        book = find_book(connection, args.book)
        where = "WHERE b.id = ?"
        parameters = (book["id"],)
    row = connection.execute(
        f"""SELECT h.*, b.title, b.author FROM highlights h
            JOIN books b ON b.id = h.book_id {where} ORDER BY RANDOM() LIMIT 1""",
        parameters,
    ).fetchone()
    if not row:
        raise SystemExit("No highlights found.")
    print_highlight(row, include_book=True)


def command_stats(connection: sqlite3.Connection, _args: argparse.Namespace) -> None:
    books = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    highlights = connection.execute("SELECT COUNT(*) FROM highlights").fetchone()[0]
    print(f"Books: {books}")
    print(f"Highlights: {highlights}")
    print("\nTop books:")
    for row in connection.execute(
        """SELECT b.title, COUNT(*) AS count FROM highlights h
           JOIN books b ON b.id = h.book_id GROUP BY b.id
           ORDER BY count DESC, b.title COLLATE NOCASE LIMIT 10"""
    ):
        print(f'  {row["count"]:4}  {row["title"]}')
    print("\nHighlights over time:")
    for row in connection.execute(
        """SELECT substr(added_at, 1, 7) AS month, COUNT(*) AS count
           FROM highlights WHERE added_at IS NOT NULL
           GROUP BY month ORDER BY month"""
    ):
        print(f'  {row["month"]}: {row["count"]}')


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    books = subparsers.add_parser("books", help="list books and clipping counts")
    books.set_defaults(handler=command_books)
    book = subparsers.add_parser("book", help="show clippings for a fuzzy-matched title")
    book.add_argument("title")
    book.set_defaults(handler=command_book)
    search = subparsers.add_parser("search", help="search clipping text and titles")
    search.add_argument("query")
    search.set_defaults(handler=command_search)
    random_parser = subparsers.add_parser("random", help="show a random clipping")
    random_parser.add_argument("--book")
    random_parser.set_defaults(handler=command_random)
    stats = subparsers.add_parser("stats", help="show library statistics")
    stats.set_defaults(handler=command_stats)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    with connect() as connection:
        args.handler(connection, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
