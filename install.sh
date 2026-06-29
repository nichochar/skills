#!/usr/bin/env bash
# Install every skill in this repo into Claude Code and Codex.
# A "skill" is any directory containing a SKILL.md file.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Destinations. Add or remove targets here.
TARGETS=(
  "$HOME/.claude/skills"
  "$HOME/.codex/skills"
)

# Find skill directories (those containing a SKILL.md), excluding hidden dirs like .git.
mapfile -t SKILL_DIRS < <(
  find "$REPO_DIR" -name SKILL.md -not -path '*/.*/*' -print0 \
    | xargs -0 -n1 dirname \
    | sort -u
)

if [ "${#SKILL_DIRS[@]}" -eq 0 ]; then
  echo "No skills (no SKILL.md found) under $REPO_DIR" >&2
  exit 1
fi

for target in "${TARGETS[@]}"; do
  if [ ! -d "$target" ]; then
    echo "skip: $target does not exist (tool not installed?)"
    continue
  fi
  for src in "${SKILL_DIRS[@]}"; do
    name="$(basename "$src")"
    dest="$target/$name"
    rm -rf "$dest"            # clear stale files so renames/deletions propagate
    cp -R "$src" "$dest"
    echo "installed: $name -> $dest"
  done
done

echo "Done. Restart your Claude Code / Codex session to pick up changes."
