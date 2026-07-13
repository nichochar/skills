#!/usr/bin/env python3
"""Generate Anki TSV and an offline HTML viewer from Kindle highlights."""

from __future__ import annotations

import argparse
import html
import json
import re
from pathlib import Path

from _common import OUTPUT_DIR, connect, highlight_rows, location_label, slugify


def truncate(text: str, limit: int = 200) -> str:
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return clean
    shortened = clean[: limit + 1].rsplit(" ", 1)[0].rstrip(".,;: ")
    return shortened + "…"


def single_line(value: str) -> str:
    return value.replace("\t", " ").replace("\r", " ").replace("\n", "<br>")


def build_cards(rows: list) -> list[dict[str, str]]:
    cards = []
    for row in rows:
        author = f' — {row["author"]}' if row["author"] else ""
        context = location_label(row)
        back = f'<strong>{html.escape(row["title"])}{html.escape(author)}</strong>'
        if context:
            back += f'<br><small>{html.escape(context)}</small>'
        back += f'<hr>{html.escape(row["text"] or "(no text)").replace(chr(10), "<br>")}'
        cards.append({"front": truncate(row["text"] or "(no text)"), "back": back})
    return cards


def viewer_html(cards: list[dict[str, str]], title: str) -> str:
    data = json.dumps(cards, ensure_ascii=False).replace("<", "\\u003c")
    safe_title = html.escape(title)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_title} flashcards</title>
<style>
:root{{--ink:#182026;--muted:#64748b;--paper:#f4efe6;--card:#fffdf8;--accent:#8b5e3c}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:17px/1.55 Georgia,serif}}
main{{max-width:820px;margin:auto;padding:5vh 24px}}h1{{font-size:clamp(1.5rem,4vw,2.4rem);margin:0 0 .3rem}}
.hint,.progress{{color:var(--muted);font:14px/1.4 system-ui,sans-serif}}.scene{{perspective:1200px;margin:3vh 0}}
.card{{position:relative;min-height:410px;transform-style:preserve-3d;transition:transform .45s;cursor:pointer}}
.card.flipped{{transform:rotateY(180deg)}}.face{{position:absolute;inset:0;display:grid;place-items:center;padding:clamp(28px,7vw,70px);overflow:auto;
backface-visibility:hidden;background:var(--card);border:1px solid #ded6ca;border-radius:18px;box-shadow:0 14px 45px #51351d20}}
.front{{font-size:clamp(1.25rem,3vw,2rem);text-align:center}}.back{{transform:rotateY(180deg);display:block}}small{{color:var(--muted)}}hr{{border:0;border-top:1px solid #ddd3c5;margin:1.3rem 0}}
.controls{{display:flex;justify-content:space-between;align-items:center;gap:12px}}button{{border:1px solid #bea98f;background:var(--card);padding:10px 18px;border-radius:999px;cursor:pointer}}
</style></head><body><main><h1>{safe_title}</h1><div class="hint">Click the card to flip · use ← and → to navigate</div>
<div class="scene"><article class="card" id="card" tabindex="0" aria-label="Flashcard"><div class="face front" id="front"></div><div class="face back" id="back"></div></article></div>
<div class="controls"><button id="prev">← Previous</button><span class="progress" id="progress"></span><button id="next">Next →</button></div>
</main><script>
const cards={data};let i=0;const card=document.querySelector('#card');
function show(){{card.classList.remove('flipped');document.querySelector('#front').textContent=cards[i]?.front||'No cards';document.querySelector('#back').innerHTML=cards[i]?.back||'';document.querySelector('#progress').textContent=cards.length?`${{i+1}} / ${{cards.length}}`:'0 / 0'}}
function move(n){{if(cards.length){{i=(i+n+cards.length)%cards.length;show()}}}}card.onclick=()=>card.classList.toggle('flipped');
document.querySelector('#prev').onclick=()=>move(-1);document.querySelector('#next').onclick=()=>move(1);
document.onkeydown=e=>{{if(e.key==='ArrowLeft')move(-1);if(e.key==='ArrowRight')move(1);if(e.key===' '||e.key==='Enter'){{e.preventDefault();card.classList.toggle('flipped')}}}};show();
</script></body></html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("--book", help="fuzzy-match a book title")
    selection.add_argument("--search", help="search highlight text and book titles")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR, help=argparse.SUPPRESS)
    args = parser.parse_args()
    with connect() as connection:
        rows = highlight_rows(connection, book=args.book, search=args.search)
    if not rows:
        raise SystemExit("No highlights matched.")
    label = args.book or args.search
    slug = slugify(label)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    tsv_path = args.output_dir / f"flashcards-{slug}.tsv"
    html_path = args.output_dir / f"flashcards-{slug}.html"
    cards = build_cards(rows)
    tsv = "".join(f'{single_line(card["front"])}\t{single_line(card["back"])}\n' for card in cards)
    tsv_path.write_text(tsv, encoding="utf-8")
    html_path.write_text(viewer_html(cards, label), encoding="utf-8")
    print(f"Wrote {len(cards)} cards")
    print(tsv_path)
    print(html_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
