---
name: kindle-highlights
description: Import, normalize, deduplicate, search, and study Kindle My Clippings.txt data with offline Python and SQLite tools. Use for Kindle highlights, book quotes, reading notes, bookmarks, book searches, Anki flashcards, or self-contained study material from purchased and side-loaded books or EPUBs.
---

# Kindle Highlights

Use the standard-library-only scripts in `scripts/`. Store source snapshots in `data/raw/`, the database in `data/highlights.db`, and generated materials in `output/`.

## Sync a Kindle

After each Kindle plug-in, resolve `SKILL` to the directory containing this `SKILL.md`, copy `documents/My Clippings.txt` to a timestamped file, and sync it:

```bash
SKILL="/absolute/path/to/kindle-highlights"
KINDLE=$(ls /Volumes | grep -i kindle | head -1)
mkdir -p "$SKILL/data/raw"
RAW="$SKILL/data/raw/clippings-$(date +%Y%m%d-%H%M%S).txt"
cp "/Volumes/$KINDLE/documents/My Clippings.txt" "$RAW"
python3 "$SKILL/scripts/sync.py" "$RAW"
```

Run `sync.py` every time new clippings may have been added. It is idempotent and refreshes `data/raw/latest.txt`. The parser handles UTF-8 BOMs plus English and French clipping headers, dates, weekdays, and month names.

## Parse and query

Run examples from the skill directory:

```bash
python3 scripts/parse_clippings.py data/raw/latest.txt
python3 scripts/parse_clippings.py data/raw/latest.txt --out data/clippings.json
python3 scripts/kh.py books
python3 scripts/kh.py book "Machines of Loving Grace"
python3 scripts/kh.py search "intelligence"
python3 scripts/kh.py random
python3 scripts/kh.py random --book "Machines of Loving Grace"
python3 scripts/kh.py stats
```

Treat `book` title input as fuzzy. Treat `search` as a case-insensitive search over clipping text and book titles.

## Generate study material

Create an Anki-compatible TSV and a self-contained interactive HTML viewer:

```bash
python3 scripts/flashcards.py --book "MachinesOfLovingGrace"
python3 scripts/flashcards.py --search "intelligence"
```

Create a single-file, searchable, print-friendly study site:

```bash
python3 scripts/build_site.py --book "MachinesOfLovingGrace"
python3 scripts/build_site.py --search "intelligence"
python3 scripts/build_site.py --all
```

Open generated HTML from `output/` locally; no network or external dependencies are required.
