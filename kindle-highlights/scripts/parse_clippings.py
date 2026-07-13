#!/usr/bin/env python3
"""Parse Kindle ``My Clippings.txt`` files into normalized JSON."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


DELIMITER_RE = re.compile(r"(?m)^==========\r?(?:\n|$)")
TRAILING_AUTHOR_RE = re.compile(r"^(?P<title>.+?)\s+\((?P<author>[^()]*)\)\s*$")

FRENCH_MONTHS = {
    "janvier": "January",
    "février": "February",
    "fevrier": "February",
    "mars": "March",
    "avril": "April",
    "mai": "May",
    "juin": "June",
    "juillet": "July",
    "août": "August",
    "aout": "August",
    "septembre": "September",
    "octobre": "October",
    "novembre": "November",
    "décembre": "December",
    "decembre": "December",
}
WEEKDAYS = (
    "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|"
    "lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche"
)


def split_title_author(line: str) -> tuple[str, str | None]:
    """Split a trailing parenthesized author while preserving parentheses in titles."""
    line = line.strip()
    match = TRAILING_AUTHOR_RE.match(line)
    if not match:
        return line, None
    author = match.group("author").strip()
    # Side-loaded documents can omit the author even when the title ends with
    # a parenthesized series label. Do not turn that label into an author.
    if re.search(r"\b(?:book|trilogy|edition|series|saga|tome|volume)\b|\d", author, re.I):
        return line, None
    return match.group("title").strip(), author or None


def parse_date(value: str) -> str | None:
    """Parse English or French Kindle timestamps and return ISO 8601."""
    value = value.strip().replace("\u202f", " ").replace("\xa0", " ")
    for french, english in FRENCH_MONTHS.items():
        value = re.sub(rf"\b{re.escape(french)}\b", english, value, flags=re.I)
    value = re.sub(rf"^(?:{WEEKDAYS})\s*,?\s*", "", value, flags=re.I)
    value = re.sub(r"\s+à\s+(?=\d{1,2}:\d{2})", " ", value, flags=re.I)
    value = re.sub(r"\s+", " ", value).strip()
    formats = (
        "%B %d, %Y %I:%M:%S %p",
        "%B %d, %Y %H:%M:%S",
        "%B %d %Y %I:%M:%S %p",
        "%B %d %Y %H:%M:%S",
        "%d %B %Y %H:%M:%S",
        "%d %B %Y %I:%M:%S %p",
        "%m/%d/%Y %I:%M:%S %p",
        "%d/%m/%Y %H:%M:%S",
    )
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue
    return None


def _number_range(value: str) -> tuple[int | None, int | None]:
    numbers = [int(number) for number in re.findall(r"\d+", value)]
    if not numbers:
        return None, None
    return numbers[0], numbers[1] if len(numbers) > 1 else numbers[0]


def parse_metadata(line: str) -> dict[str, Any]:
    """Normalize a Kindle metadata line in English or French."""
    clean = line.strip().lstrip("\ufeff").strip()
    clean = re.sub(r"^[-–—]\s*", "", clean)
    folded = clean.casefold()
    if "surlignement" in folded or "highlight" in folded:
        entry_type = "highlight"
    elif re.search(r"\b(?:note)\b", folded):
        entry_type = "note"
    elif "bookmark" in folded or "signet" in folded:
        entry_type = "bookmark"
    else:
        entry_type = None

    result: dict[str, Any] = {
        "type": entry_type,
        "page": None,
        "location_start": None,
        "location_end": None,
        "added_at": None,
    }
    for part in (item.strip() for item in clean.split("|")):
        part_folded = part.casefold()
        if "added on" in part_folded or "ajouté le" in part_folded or "ajoute le" in part_folded:
            date_text = re.split(r"added on|ajout[ée] le", part, maxsplit=1, flags=re.I)[-1]
            result["added_at"] = parse_date(date_text)
        elif "location" in part_folded or "emplacement" in part_folded:
            start, end = _number_range(part)
            result["location_start"], result["location_end"] = start, end
        elif re.search(r"\bpage\b", part_folded):
            page, _ = _number_range(part)
            result["page"] = page
    return result


def parse_text(content: str) -> tuple[list[dict[str, Any]], list[str]]:
    """Parse text, dedupe edited highlights, and return entries plus error messages."""
    records: dict[tuple[str, int | None, str], dict[str, Any]] = {}
    errors: list[str] = []
    for index, block in enumerate(DELIMITER_RE.split(content), start=1):
        lines = block.strip("\r\n").splitlines()
        if not any(line.strip() for line in lines):
            continue
        if len(lines) < 2:
            errors.append(f"entry {index}: expected title and metadata lines")
            continue
        title, author = split_title_author(lines[0].lstrip("\ufeff"))
        metadata = parse_metadata(lines[1])
        if not title:
            errors.append(f"entry {index}: empty book title")
            continue
        if metadata["type"] is None:
            errors.append(f"entry {index} ({title}): unrecognized clipping type")
            continue
        if metadata["added_at"] is None:
            errors.append(f"entry {index} ({title}): unrecognized added date")
        text = "\n".join(lines[2:]).strip()
        entry = {
            "book_title": title,
            "author": author,
            **metadata,
            "text": text,
        }
        key = (title, metadata["location_start"], text)
        previous = records.get(key)
        if previous is None or (entry["added_at"] or "") >= (previous["added_at"] or ""):
            records[key] = entry
    entries = list(records.values())
    entries.sort(key=lambda item: (item["book_title"].casefold(), item["added_at"] or "", item["location_start"] or -1))
    return entries, errors


def parse_file(path: str | Path) -> tuple[list[dict[str, Any]], list[str]]:
    content = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    return parse_text(content)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("clippings", type=Path, help="path to My Clippings.txt")
    parser.add_argument("--out", type=Path, help="write JSON to this path instead of stdout")
    args = parser.parse_args()
    entries, errors = parse_file(args.clippings)
    payload = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        sys.stdout.write(payload)
    for error in errors:
        print(f"warning: {error}", file=sys.stderr)
    print(f"Parsed {len(entries)} entries with {len(errors)} parse errors", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
