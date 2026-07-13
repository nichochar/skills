#!/usr/bin/env python3
"""Build a searchable, print-friendly offline study site from highlights."""

from __future__ import annotations

import argparse
import html
from collections import OrderedDict
from pathlib import Path

from _common import OUTPUT_DIR, connect, highlight_rows, location_label, slugify


def render(rows: list, title: str) -> str:
    groups: OrderedDict[tuple[str, str | None], list] = OrderedDict()
    for row in rows:
        groups.setdefault((row["title"], row["author"]), []).append(row)
    sections = []
    for (book, author), highlights in groups.items():
        byline = f'<p class="author">{html.escape(author)}</p>' if author else ""
        items = []
        for row in highlights:
            text = html.escape(row["text"] or "(no text)").replace("\n", "<br>")
            metadata = html.escape(location_label(row))
            searchable = html.escape(f'{book} {author or ""} {row["text"]}'.casefold(), quote=True)
            items.append(
                f'<article class="highlight" data-search="{searchable}"><blockquote>{text}</blockquote>'
                f'<div class="meta">{html.escape(row["type"].title())}{" · " + metadata if metadata else ""}</div></article>'
            )
        sections.append(
            f'<section class="book"><header><div class="cover" aria-hidden="true">{html.escape(book[:1].upper())}</div>'
            f'<div><h2>{html.escape(book)}</h2>{byline}<span class="count">{len(highlights)} clippings</span></div></header>'
            f'{"".join(items)}</section>'
        )
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} · Kindle highlights</title><style>
:root{{--ink:#22201d;--muted:#70685f;--paper:#f7f3eb;--card:#fffdfa;--rule:#d9d0c4;--accent:#9a5936}}
*{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.65 Georgia,serif}}
.masthead{{background:#27211d;color:white;padding:54px 24px 38px}}.masthead>div,main{{max-width:900px;margin:auto}}h1{{margin:0;font-size:clamp(2rem,7vw,4rem);line-height:1.05}}
.summary{{color:#d8cec4;margin:.8rem 0 1.5rem}}#search{{width:100%;padding:14px 18px;border:0;border-radius:8px;font:16px system-ui,sans-serif}}
main{{padding:46px 24px 80px}}.book{{margin-bottom:64px}}.book>header{{display:flex;gap:20px;align-items:center;border-bottom:1px solid var(--rule);padding-bottom:18px}}
.cover{{width:68px;height:92px;flex:none;display:grid;place-items:center;background:var(--accent);color:white;border-radius:3px 8px 8px 3px;font-size:2rem;box-shadow:4px 4px 0 #d9c5b4}}
h2{{margin:0;line-height:1.2;font-size:clamp(1.5rem,4vw,2.25rem)}}.author{{margin:.25rem 0;color:var(--muted)}}.count,.meta{{font:13px/1.5 system-ui,sans-serif;color:var(--muted);text-transform:uppercase;letter-spacing:.06em}}
.highlight{{background:var(--card);border-left:3px solid var(--accent);margin:22px 0;padding:20px 24px;break-inside:avoid}}blockquote{{margin:0 0 12px}}mark{{background:#ffe79a}}
.empty{{display:none;text-align:center;color:var(--muted);padding:40px}}@media print{{.masthead{{background:white;color:black;padding:0}}#search,.summary{{display:none}}main{{padding:20px 0}}.highlight{{box-shadow:none;border:1px solid #bbb}}.book{{break-before:page}}}}
</style></head><body><header class="masthead"><div><h1>{safe_title}</h1><p class="summary">{len(rows)} clippings across {len(groups)} books · generated offline</p><input id="search" type="search" placeholder="Search these highlights…" autocomplete="off"></div></header>
<main id="content">{"".join(sections)}<p class="empty" id="empty">No highlights match that search.</p></main>
<script>
const input=document.querySelector('#search'),empty=document.querySelector('#empty');
input.addEventListener('input',()=>{{const q=input.value.trim().toLocaleLowerCase();let visible=0;document.querySelectorAll('.book').forEach(book=>{{let n=0;book.querySelectorAll('.highlight').forEach(item=>{{const show=!q||item.dataset.search.includes(q);item.hidden=!show;if(show)n++}});book.hidden=n===0;visible+=n}});empty.style.display=visible?'none':'block'}});
</script></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--book", help="fuzzy-match a book title")
    selection.add_argument("--search", help="search highlight text and book titles")
    selection.add_argument("--all", action="store_true", help="include the complete library")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args()
    with connect() as connection:
        rows = highlight_rows(connection, book=args.book, search=args.search, all_books=args.all)
    if not rows:
        raise SystemExit("No highlights matched.")
    label = args.book or args.search or "all-highlights"
    destination = args.output_dir / f"site-{slugify(label)}" / "index.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(render(rows, label), encoding="utf-8")
    print(f"Wrote {len(rows)} highlights to {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
