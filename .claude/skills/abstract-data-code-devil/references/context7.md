# Context7 grounding for the critics

Adversarial reviews go wrong most often not by missing issues but by asserting confident-but-wrong
claims about library behavior from stale training data — "this ORM call is parameterized", "this
client retries automatically", "this route is cached". Those false findings destroy the council's
credibility. Context7 fixes this by giving the critics current, version-specific documentation to
cite instead of memory.

## When to use it

During **Step 0** of SKILL.md, once the stack and key libraries are known. Do it before dispatching
any critic so every critic works from the same grounded excerpts.

## Availability

Context7 is exposed as MCP tools, typically:
- `resolve-library-id` — turn a library name (e.g., "fastapi", "next.js", "sqlalchemy") into a
  Context7-compatible library ID.
- `query-docs` (a.k.a. get-library-docs) — fetch documentation for a resolved ID, optionally scoped
  to a topic (e.g., "dependency injection", "middleware", "connection pool").

Tool names may be prefixed by the server ID in this environment. If the tools are **not** present,
skip grounding and make sure every library-behavior finding is labeled
"potential — requires manual verification". Never fake a citation.

## Flow

1. Identify the libraries whose behavior the review actually hinges on — auth, ORM/DB clients, HTTP
   clients, framework routing/caching, serialization, task queues. Don't fetch docs for libraries
   that aren't load-bearing for any finding.
2. For each, call `resolve-library-id` with the library name.
3. Call `query-docs` on the resolved ID, scoped to the topic the code exercises (e.g., for a retry
   concern, fetch the HTTP client's timeout/retry docs).
4. Pass the returned excerpts into each critic's CONTEXT block. Keep excerpts tight and relevant —
   the critics need the authoritative behavior, not the whole manual.

## How critics should cite it

When a finding depends on documented library behavior, the **Evidence** field should reference the
Context7 excerpt ("per fetched docs for <lib> <version>, <method> does not escape …") so the claim is
traceable. If the docs contradict a critic's initial assumption, the finding must be corrected or
dropped — grounding beats intuition.

## Receipt

Record whether grounding was used by passing `--context7 used` or `--context7 unavailable` to
`scripts/write_receipt.py`, so the receipt reflects how much of the review was documentation-grounded
versus reliant on manual verification.
