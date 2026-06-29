# skills

My personal collection of [Claude skills](https://docs.claude.com) — reusable bundles of instructions and resources that teach Claude a workflow once so it runs consistently every time.

## How it's organized

One flat, unsorted list. Each skill lives in its own top-level folder containing a `SKILL.md`:

```
skills/
├── README.md
└── <skill-name>/
    └── SKILL.md        # frontmatter (name + description) + instructions
        └── (optional) scripts/, references/, assets/
```

No categories, no nesting — keeping it simple. To find a skill, scan the list below or `ls` the folder.

## Skills

- **grill-me** — asks you questions one at a time (with a recommended answer each) until it has a strong shared understanding of a project or task. Triggers on `/grill`, `/grill-me`, or similar.

<!--
Add each new skill here as a one-line entry, e.g.:
- **skill-name** — one-line description of what it does and when it triggers.

Planned:
- codebase-explore — (TBD, brainstorming the right shape)
-->

## Anatomy of a skill

Every skill needs a `SKILL.md` with YAML frontmatter and Markdown instructions:

```yaml
---
name: skill-name
description: What it does AND when to use it. This is the trigger — be specific about the phrases and contexts that should activate it.
---

# Skill Name

Instructions for Claude, written in the imperative. Explain the *why*, not just the *what*.
```

The `description` is the most important field: it's the only part always loaded into context, and it decides whether the skill fires at all.

## Adding a new skill

1. Create a folder: `mkdir <skill-name>`
2. Write `<skill-name>/SKILL.md` with frontmatter + instructions
3. Add a one-line entry to the **Skills** list above
4. Commit
