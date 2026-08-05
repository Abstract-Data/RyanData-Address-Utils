# prompts/

Version-controlled home for agent system prompts used in this project (as opposed to the
project-level guidance in `AGENTS.md`, which applies to every agent).

## Layout

Each agent with a maintained prompt gets its own subdirectory:

```
prompts/
  {agent-name}/
    current.md       # active prompt — always a copy of the latest versioned snapshot
    CHANGELOG.md      # append-only history, newest entry first
    v1.0.0.md         # versioned snapshot
    v1.1.0.md
```

## Workflow

1. Never edit `current.md` in place. Write a new versioned snapshot (`v{MAJOR.MINOR.PATCH}.md`),
   copy it to `current.md`, and append an entry to `CHANGELOG.md` explaining what changed and why.
2. Bump MAJOR for a role/scope change, MINOR for a meaningful behavior change, PATCH for wording
   clarifications that don't change behavior.
3. `CHANGELOG.md` is append-only — never edit or delete a past entry, even if it turns out to be
   wrong. Add a new entry that supersedes it.

This project currently has no standalone versioned agent prompts — the subagent definitions in
`.claude/agents/*.md` serve as both the prompt and the deployment artifact. Add a subdirectory
here if a prompt needs to be iterated independently of its subagent file (e.g., a prompt reused
across multiple tools where the subagent frontmatter isn't portable).
