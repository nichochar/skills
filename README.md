# skills

My personal collection of [Claude skills](https://docs.claude.com) — reusable bundles of instructions that teach a workflow once so it runs consistently every time.

Each skill is a top-level folder with a `SKILL.md` (YAML frontmatter + Markdown instructions, plus optional `scripts/`, `references/`, `assets/`). One flat list, no nesting.

## Skills

- **grill-me** — asks you questions one at a time until it has a strong shared understanding of a project or task. Triggers on `/grill`, `/grill-me`, or similar.

## Installing

This repo is just source-of-truth; the tools don't scan it. Run `./install.sh` to copy every skill into both Claude Code (`~/.claude/skills/`) and Codex (`~/.codex/skills/`), then restart your session. The script overwrites same-named skills in those dirs, so keep this repo authoritative.

## Adding a new skill

1. `mkdir <skill-name>`, then write `<skill-name>/SKILL.md`.
2. The `description` field is the trigger — it's the only part always in context, so be specific about the phrases and contexts that should fire it. Write instructions in the imperative; explain the *why*.
3. Add a one-line entry to **Skills** above, run `./install.sh`, and commit.
