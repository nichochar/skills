# skills

My personal collection of [Claude skills](https://docs.claude.com) — reusable bundles of instructions that teach a workflow once so it runs consistently every time.

Each skill is a top-level folder with a `SKILL.md` (YAML frontmatter + Markdown instructions, plus optional `scripts/`, `references/`, `assets/`). One flat list, no nesting.

## Skills

- **bro** — restates the previous message in plain human language, no jargon. Invoke with `/bro`; it never fires on its own.
- **explain-diff** — turns a diff, branch, or PR into a self-contained HTML explainer with background, intuition, a code walkthrough, and an interactive quiz.
- **grill-me** — grills you in rounds of numbered questions (each with a recommended answer) until it has a strong shared understanding of a project or task. Triggers on `/grill`, `/grill-me`, or similar.
- **i-have-adhd** — shapes every reply for an ADHD reader: concrete next action first, numbered steps, no tangents, real time estimates.
- **kindle-highlights** — imports Kindle clippings into SQLite for searching, flashcards, and offline study sites, with English and French header support.
- **stageshow** — builds faux product UI that looks like a real product, as a still illustration or an animated demo with a cursor. Browser and app windows, dashboards, phones, notifications, terminals, bento grids and cursor walkthroughs. Credit: [Benji Taylor / benjitaylor/skills](https://github.com/benjitaylor/skills) (MIT).
- **technical-writing** — layered technical-writing standard (Diátaxis structure, Google developer style sentences, STE instruction rules, Global English syntax) for docs, RFCs, READMEs, PR descriptions, and commit messages. Invoke with `/technical-writing`; it never fires on its own. Credit: [cursor/plugins (pstack)](https://github.com/cursor/plugins/blob/main/pstack/skills/technical-writing/SKILL.md).
- **writing-review** — critiques essays and blog posts structure-first (one point, lead, mechanism, missing objection, ending), then evidence, voice, and lines; always ends with a ship / one-pass-away / rework verdict.

## Installing

This repo is just source-of-truth; the tools don't scan it. Run `./install.sh` to copy every skill into both Claude Code (`~/.claude/skills/`) and Codex (`~/.codex/skills/`), then restart your session. The script overwrites same-named skills in those dirs, so keep this repo authoritative.

## Adding a new skill

1. `mkdir <skill-name>`, then write `<skill-name>/SKILL.md`.
2. The `description` field is the trigger — it's the only part always in context, so be specific about the phrases and contexts that should fire it. Write instructions in the imperative; explain the *why*.
3. Add a one-line entry to **Skills** above, run `./install.sh`, and commit.
