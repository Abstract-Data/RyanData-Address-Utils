#!/usr/bin/env python3
"""
gate.py — Abstract Data Dev-Env enforcement gate (v1.1.0)

One file, three responsibilities, no third-party dependencies (stdlib only):

  1. Stop / SubagentStop loop-closer   -> `gate.py stop-check`
     Refuses to let a turn end while there are unresolved verification failures
     or an outstanding task-critic verdict. This is the fix for the "open loop
     after a failed check" pattern.

  2. Dangerous-ops PreToolUse gate     -> `gate.py pretool`
     DENY for operations that are never appropriate autonomously (global git
     config, hook self-modification) and ASK (escalate to the human) for the
     "meaning-changing" operations the review flagged: CI workflow edits,
     production-loader edits, dependency/lockfile changes, migrations, force
     pushes, direct SQL backfill, cloud-risk alembic runs.

  3. Disposition ledger CLI            -> `gate.py record-failure | dispose
                                            | task-critic | status`
     The escape hatch the Stop gate checks against. A failed check is cleared
     only by a written disposition that names the check.

Harness support: works under BOTH Claude Code and Cursor. The two send
different hook payload fields (Claude `session_id` + `tool_name`/`tool_input`;
Cursor `conversation_id` + `beforeShellExecution`/`afterFileEdit` fields) and
expect different output (Claude `hookSpecificOutput.permissionDecision` and
`{"decision":"block"}`; Cursor `{"permission":...}` and `{"followup_message":...}`).
The gate detects the harness from the payload and adapts.

Session keying (v1.1.0 fix): the Stop gate sees the session id in its payload,
but the CLI record path does not (no env var in a tool call), so verdicts used
to land in a `no-session` ledger the Stop gate never read. Now the pretool gate
— which fires on every tool call and *does* have the payload — persists the live
session id to `.claude/state/current-session`, and every path resolves through
`resolve_session()`, so the CLI and Stop gate always agree on the ledger.

Wiring lives in settings.hooks.json (Claude) and ~/.cursor/hooks.json (Cursor).
Agent-facing rules live in AGENTS.enforcement.md.

Philosophy: deterministic, evidence-based, fail-OPEN on internal bugs (a gate
bug must never brick every session) but fail-CLOSED on the conditions it is
designed to catch. The Stop gate has a loop guard so a genuinely stuck session
is released with a loud warning rather than hung forever.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

VERSION = "1.1.0"
MAX_STOP_BLOCKS = 3  # loop guard: release after this many consecutive blocks


# --------------------------------------------------------------------------- #
# I/O helpers
# --------------------------------------------------------------------------- #
def read_payload() -> dict:
    """Read the hook JSON from stdin. Returns {} on any problem."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def project_dir(payload: dict | None = None) -> Path:
    env = (
        os.environ.get("CLAUDE_PROJECT_DIR")
        or os.environ.get("CURSOR_PROJECT_DIR")
        or os.environ.get("GROK_WORKSPACE_ROOT")
    )
    if env:
        return Path(env)
    p = payload or {}
    roots = p.get("workspace_roots")
    if isinstance(roots, list) and roots:
        return Path(roots[0])
    if p.get("workspaceRoot"):
        return Path(p["workspaceRoot"])
    if p.get("cwd"):
        return Path(p["cwd"])
    return Path.cwd()


def state_dir(proj: Path) -> Path:
    d = proj / ".claude" / "state"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ledger_path(proj: Path, session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id or "no-session")
    return state_dir(proj) / f"gate-{safe}.json"


def _session_file(proj: Path) -> Path:
    """Sentinel holding the active session id, so the CLI and Stop gate agree."""
    return state_dir(proj) / "current-session"


def load_ledger(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except Exception:
            pass
    return {"session_id": path.stem, "task_critic": None, "checks": {}, "stop_blocks": 0}


def save_ledger(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2))


# --------------------------------------------------------------------------- #
# Harness detection + session resolution
# --------------------------------------------------------------------------- #
def _harness(payload: dict | None) -> str:
    """'cursor', 'grok', or 'claude', inferred from payload shape / env (ADR-0062)."""
    p = payload or {}
    if "conversation_id" in p or "cursor_version" in p or "generation_id" in p:
        return "cursor"
    # Grok Build: env is the strongest signal; camelCase envelope is secondary.
    if (
        os.environ.get("GROK_SESSION_ID")
        or os.environ.get("GROK_HOOK_EVENT")
        or "sessionId" in p
        or "workspaceRoot" in p
        or p.get("hookEventName")
        in {
            "pre_tool_use",
            "post_tool_use",
            "stop",
            "session_start",
            "session_end",
            "subagent_stop",
        }
    ):
        return "grok"
    return "claude"


def _sid_from_payload(payload: dict | None) -> str:
    p = payload or {}
    return (
        p.get("session_id")
        or p.get("sessionId")
        or p.get("conversation_id")
        or ""
    )


def resolve_session(proj: Path, payload: dict | None = None, *, persist: bool = False) -> str:
    """Resolve the active session id from every available source, consistently.

    Order: payload (Claude session_id / Cursor conversation_id) -> env -> --session ->
    the persisted sentinel -> 'no-session'. When ``persist`` (hook paths that hold a
    payload), the resolved id is written to the sentinel so the CLI path can find it.
    """
    sid = _sid_from_payload(payload)
    if sid:
        if persist:
            try:
                _session_file(proj).write_text(sid)
            except Exception:
                pass
        return sid
    sid = (
        os.environ.get("CLAUDE_SESSION_ID")
        or os.environ.get("CURSOR_CONVERSATION_ID")
        or os.environ.get("GROK_SESSION_ID")
        or _arg("--session")
    )
    if sid:
        return sid
    f = _session_file(proj)
    if f.exists():
        try:
            s = f.read_text().strip()
            if s:
                return s
        except Exception:
            pass
    return "no-session"


# --------------------------------------------------------------------------- #
# Output emitters (harness-aware)
# --------------------------------------------------------------------------- #
def emit_allow() -> None:
    """Allow the action: exit 0, no output (both harnesses treat this as allow)."""
    sys.exit(0)


def emit_stop_block(reason: str, harness: str = "claude") -> None:
    """Block / re-drive on Stop. Claude/Grok hard-block; Cursor re-drives via followup_message."""
    if harness == "cursor":
        # Cursor's stop hook cannot hard-block; a followup_message auto-continues the
        # agent (bounded by Cursor's loop_limit), achieving loop closure.
        print(json.dumps({"followup_message": reason}))
    else:
        # Claude and Grok share decision/block vocabulary for Stop (ADR-0062).
        print(json.dumps({"decision": "block", "reason": reason}))
    sys.exit(0)


def emit_pretool(decision: str, reason: str, harness: str = "claude") -> None:
    """decision is 'deny' or 'ask'. 'allow'/silent uses emit_allow()."""
    if harness == "cursor":
        # Cursor permission protocol: allow|deny|ask, with messages for the user/agent.
        print(json.dumps({"permission": decision, "user_message": reason, "agent_message": reason}))
    elif harness == "grok":
        # Grok PreToolUse: flat {"decision": "allow"|"deny", "reason": ...}. No documented
        # ask — map ask → deny with an explicit human-confirmation prefix (fail-closed).
        if decision == "ask":
            print(
                json.dumps(
                    {
                        "decision": "deny",
                        "reason": f"Human confirmation required: {reason}",
                    }
                )
            )
        else:
            print(json.dumps({"decision": decision, "reason": reason}))
    else:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": decision,
                        "permissionDecisionReason": reason,
                    }
                }
            )
        )
    sys.exit(0)


# --------------------------------------------------------------------------- #
# 1. Stop / SubagentStop loop-closer
# --------------------------------------------------------------------------- #
def open_items(ledger: dict, require_task_critic: bool) -> list[str]:
    """Unresolved Stop-gate items for a session, read from its FILE ledger dict.

    Reads the task-critic verdict and the undisposed failed/skipped checks
    directly out of the ``gate-<session>.json`` ledger dict (no DB, no
    ``state.py`` sibling). A missing/garbled ledger arrives here as
    ``load_ledger``'s safe default (``task_critic`` None, empty ``checks``),
    which blocks iff a task is declared.
    """
    items: list[str] = []

    if require_task_critic:
        tc = ledger.get("task_critic")
        if not tc or tc.get("verdict") != "PASS":
            items.append(
                "task-critic has not recorded a PASS for this session. Run "
                "task-critic against TASK.md, then record the result: "
                "`python .claude/hooks/gate.py task-critic --verdict PASS|BLOCK`."
            )

    for name, rec in ledger.get("checks", {}).items():
        if rec.get("status") in ("failed", "skipped") and not rec.get("disposition"):
            detail = rec.get("detail") or ""
            items.append(
                f"check '{name}' is {rec['status']} with no disposition"
                + (f" ({detail})" if detail else "")
                + ". Either fix it and re-run, or record a disposition: "
                f"`python .claude/hooks/gate.py dispose --check '{name}' "
                "--status fixed|deferred|ticket|ignore --note '...'`."
            )
    return items


class StopDecision:
    """Outcome of the Stop loop-closer core — a test seam over ``cmd_stop_check``.

    ``blocks`` is the gate verdict; ``items`` the unresolved reasons; ``reason``
    the harness-facing message; ``released`` marks a bounded loop-guard release
    (block became allow after ``MAX_STOP_BLOCKS``), which the caller surfaces
    loudly on stderr.
    """

    def __init__(
        self,
        *,
        blocks: bool,
        items: list[str],
        reason: str,
        released: bool = False,
    ) -> None:
        self.blocks = blocks
        self.items = items
        self.reason = reason
        self.released = released


def evaluate_stop(proj: Path, payload: dict | None = None, session_id: str | None = None) -> StopDecision:
    """Pure core of the Stop loop-closer: decide block vs. allow over the FILE ledger.

    Stop-gate state lives entirely in ``.claude/state/gate-<session>.json`` (task-
    critic verdict, per-check status/disposition, the ``stop_blocks`` counter).
    A missing/garbled ledger is treated as "unresolved" via ``load_ledger``'s
    safe default (``task_critic`` None), which blocks iff ``TASK.md`` exists. The
    ``stop_blocks`` loop-guard counter lives in the ledger dict: it increments on
    each consecutive block and releases once it exceeds ``MAX_STOP_BLOCKS``.
    """
    proj = Path(proj)
    if session_id is None:
        session_id = resolve_session(proj, payload)
    lpath = ledger_path(proj, session_id)
    ledger = load_ledger(lpath)
    require_tc = (proj / "TASK.md").exists()

    items = open_items(ledger, require_task_critic=require_tc)
    if not items:
        # Clean pass: reset the consecutive-block counter and allow.
        if ledger.get("stop_blocks"):
            ledger["stop_blocks"] = 0
            save_ledger(lpath, ledger)
        return StopDecision(blocks=False, items=[], reason="")

    # Loop guard: count CONSECUTIVE blocks; never hang a session forever.
    ledger["stop_blocks"] = int(ledger.get("stop_blocks", 0)) + 1
    save_ledger(lpath, ledger)
    if ledger["stop_blocks"] > MAX_STOP_BLOCKS:
        reason = (
            f"[gate] WARNING: enforcement gate released after {ledger['stop_blocks']} blocks with "
            "unresolved items:\n  - " + "\n  - ".join(items) + "\n"
        )
        return StopDecision(blocks=False, items=items, reason=reason, released=True)

    reason = (
        "Do not end the turn yet. The enforcement gate found unresolved "
        f"items ({len(items)}):\n\n  - "
        + "\n  - ".join(items)
        + "\n\nResolve each, then stop. This is the loop-closure rule: no "
        "session ends on a failed or skipped check without a written "
        "disposition."
    )
    return StopDecision(blocks=True, items=items, reason=reason)


LEDGER_MAX_AGE_DAYS = 30  # FR-7: prune gate-*.json ledgers older than this


def _prune_aged_ledgers(proj: Path, current_session: str | None = None) -> None:
    """FR-7: self-prune aged ``gate-*.json`` ledgers at every stop-check.

    Deletes ledgers whose mtime is older than 30 days, EXCLUDING: (a) the
    current session's ledger, (b) any ledger with an undisposed ``failed`` or
    ``skipped`` check, (c) any ledger carrying a task-critic ``BLOCK`` verdict.

    Single ``os.scandir`` pass (budget <10ms), stdlib-only, and fails OPEN: any
    error is swallowed and it never blocks or raises.
    """
    try:
        proj = Path(proj)
        sdir = proj / ".claude" / "state"
        cutoff = time.time() - LEDGER_MAX_AGE_DAYS * 86400
        keep = ledger_path(proj, current_session).name if current_session is not None else None
        with os.scandir(sdir) as it:
            for entry in it:
                name = entry.name
                if not (name.startswith("gate-") and name.endswith(".json")):
                    continue
                if name == keep:
                    continue
                try:
                    if entry.stat().st_mtime >= cutoff:
                        continue
                    data = json.loads(Path(entry.path).read_text())
                    checks = data.get("checks") or {}
                    if any(
                        c.get("status") in ("failed", "skipped") and not c.get("disposition")
                        for c in checks.values()
                    ):
                        continue
                    tc = data.get("task_critic")
                    # task_critic is a dict {"verdict": "BLOCK", ...} — a bare
                    # `== "BLOCK"` never matches, so a BLOCK ledger would be wrongly pruned.
                    if isinstance(tc, dict) and tc.get("verdict") == "BLOCK":
                        continue
                    Path(entry.path).unlink()
                except Exception:
                    continue
    except Exception:
        pass


def _tripwire_check(proj: Path) -> None:
    """FR-2.4c: warn-only, schema-aware, harness-general drift tripwire.

    At Stop, hash each hook named in the committed ``.abstract-data/hooks-manifest.json``
    trust anchor and compare it to the recorded ``sha256``. The manifest is read
    schema-aware — the deployed hook must never parse a schema it predates:

    * a **schema-2 envelope** (``{"schema": int, "entries": {"<relpath>": {...}}}``) →
      each entry key is a PROJECT-RELATIVE path resolved as ``proj/<relpath>``, so a
      ``.cursor/hooks/*`` copy is exactly as visible as the ``.claude/hooks/*`` one
      (no hardcoded hooks dir);
    * a **legacy v1** flat basename object (NO ``"schema"`` key) → each basename is
      resolved under ``proj/.claude/hooks/`` AND ONE loud migrate warning naming the
      legacy schema is emitted — never a silent fail-open.

    On any hash mismatch emit ONE warn-only stderr line listing the drifted keys. Never
    blocks (always returns ``None``). Budget <20ms; fails OPEN (any error swallowed).
    SILENT when the manifest is missing or unparseable -- and it short-circuits BEFORE
    hashing on that silent path so the common case is near-zero cost.
    """
    try:
        proj = Path(proj)
        manifest_path = proj / ".abstract-data" / "hooks-manifest.json"
        if not manifest_path.is_file():
            return None
        try:
            manifest = json.loads(manifest_path.read_text())
        except (json.JSONDecodeError, OSError, ValueError):
            return None
        if not isinstance(manifest, dict):
            return None

        # Schema-aware key resolution. schema-2 keys are project-relative paths; a legacy
        # v1 flat object (no "schema") is basename-keyed under .claude/hooks/.
        legacy = "schema" not in manifest
        if legacy:
            hooks_dir = proj / ".claude" / "hooks"
            resolved = [(key, entry, hooks_dir / key) for key, entry in manifest.items()]
        else:
            entries = manifest.get("entries")
            if not isinstance(entries, dict):
                # Corrupt schema envelope: fail OPEN (silent), never crash a deployed hook.
                return None
            resolved = [(key, entry, proj / key) for key, entry in entries.items()]

        if legacy:
            # Loud, exactly-once: a legacy manifest must be migrated (never a silent pass).
            print(
                "[gate] WARNING: legacy schema-1 hooks manifest — run `hooks upgrade` "
                "to migrate",
                file=sys.stderr,
            )

        drifted: list[str] = []
        for key, entry, script_path in resolved:
            if not isinstance(entry, dict):
                continue
            expected = entry.get("sha256")
            if not expected:
                continue
            try:
                actual = hashlib.sha256(script_path.read_bytes()).hexdigest()
            except OSError:
                continue
            if actual != expected:
                drifted.append(key)

        if drifted:
            print(
                "[gate] WARNING: deployed hook drift vs committed manifest: "
                + ", ".join(sorted(drifted)),
                file=sys.stderr,
            )
        return None
    except Exception:
        return None


def cmd_stop_check() -> None:
    payload = read_payload()
    proj = project_dir(payload)
    harness = _harness(payload)

    try:
        session_id = resolve_session(proj, payload, persist=True)

        # FR-7: self-prune aged gate-*.json ledgers (fails open; never blocks).
        _prune_aged_ledgers(proj, current_session=session_id)

        # FR-11: warn-only drift tripwire vs the committed hooks manifest
        # (silent when no/unparseable manifest; fails open; never blocks).
        _tripwire_check(proj)

        # evaluate_stop reads the session's FILE ledger and decides block vs.
        # allow. A missing/garbled ledger is treated as unresolved (blocks iff
        # TASK.md exists); the bounded-release counter lives in the ledger dict.
        decision = evaluate_stop(proj, payload, session_id=session_id)
        if not decision.blocks:
            if decision.released:
                # Released, but loudly. Surface to the human via stderr.
                sys.stderr.write(decision.reason)
            emit_allow()

        emit_stop_block(decision.reason, harness)

    except SystemExit:
        raise
    except Exception as exc:  # fail OPEN on a gate bug; never brick the session
        sys.stderr.write(f"[gate] internal error in stop-check, allowing: {exc}\n")
        emit_allow()


# --------------------------------------------------------------------------- #
# 2. Dangerous-ops PreToolUse gate
# --------------------------------------------------------------------------- #
# Hard DENY: never appropriate for an agent to do autonomously.
# Any per-harness deployed-hooks directory (Claude / Cursor / Antigravity / Copilot). Since the
# schema-2 tripwire is cross-harness (FR-2.3), the enforcement gate is now a first-class trust
# anchor under EACH tool's hooks dir — so the pre-write protection layer (FR-2.2) must guard them
# all, not just .claude/hooks/. A tampered .cursor/hooks/gate.py must be as protected as the
# Claude one. The leading literal dot keeps `plugins/abstract-data-claude/hooks/` (no dot) out.
_HOOKS_DIR = r"\.(?:claude|cursor|agents|github|grok)/hooks/"

BASH_DENY = [
    (re.compile(r"\bgit\s+config\s+--global\b"),
     "Global git config changes are blocked. Make this change yourself."),
    (re.compile(r"\bchmod\b.*" + _HOOKS_DIR),
     "Modifying enforcement hook files is blocked."),
]

# FR-6.6: the three authoring-repo enforcement SOURCES still uncovered after #188 —
# the hook source tree, the frozenset-bearing catalog-sync test, and the
# selection-narrowing file. Shared alternation so the sed / cp|mv|tee / redirect
# write-form rules below stay DRY. Harmless in deployed target projects (these paths
# do not exist there).
_FR66_TARGETS = (
    r"(?:src/abstract_data/project_tools/hooks/"
    r"|tests/test_hooks_catalog_sync\.py"
    r"|\.abstract-data/selection\.toml)"
)

# ASK (escalate to human): the "meaning-changing" operations from the review.
BASH_ASK = [
    (re.compile(r"\bgit\s+push\b.*(--force|-f)\b"),
     "Force push — confirm target branch and that this is intended."),
    (re.compile(r"\bgit\s+push\b.*\b(main|master|preview|prod|production|release)\b"),
     "Push to a protected branch — confirm before proceeding."),
    (re.compile(r"\bgit\s+reset\s+--hard\b"),
     "Hard reset discards work — confirm."),
    (re.compile(r"\bgit\s+clean\s+-[a-z]*f"),
     "git clean -f deletes untracked files — confirm."),
    (re.compile(r"\balembic\s+(upgrade|downgrade)\b"),
     "Alembic migration run — confirm the target DB is NOT a cloud/production "
     "database (house rule: no cloud alembic upgrades)."),
    (re.compile(r"\bsupabase\s+db\s+(push|reset)\b"),
     "Supabase schema push/reset against a remote project — confirm."),
    (re.compile(r"\bpsql\b.*-c\b.*\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER)\b", re.I),
     "Direct SQL write/DDL — confirm (house rule: prefer migrations / queued "
     "discovery over direct SQL backfill)."),
    # Anchor `but` as the INVOKED command — at command start, after a shell
    # separator (\n ; & |), or behind a command runner (command/sudo/env/exec),
    # optional leading flags, then the state verb. A bare `\bbut\b` matched the
    # English word "but" anywhere before a config/reset/undo token (e.g.
    # `git commit -m "fix undo path but keep config"`), a live FP once gate.py
    # deployed to Cursor. The runner-word branch (FR-6.1, decision A) still
    # requires the state verb IMMEDIATELY after `but` (modulo flags), so a runner
    # word merely appearing earlier in prose does not trip it; a rare residual FP
    # like "run that command but reset it" only costs a human ASK, never a deny.
    (re.compile(r"(?:^|[\n;&|]|\b(?:command|sudo|env|exec)\s+)\s*but\s+(?:-\S+\s+)*(?:config|reset|undo)\b"),
     "GitButler state-changing operation — confirm."),
    (re.compile(r"\brm\s+-rf\b"),
     "Recursive force delete — confirm path."),
    # FR-12: shell write-forms targeting the committed hooks manifest or the
    # .claude/hooks/ dir are trust-anchor tampering — escalate to human. Anchored
    # to a write verb *followed by* the target so a bare mention in an unrelated
    # arg (e.g. a --note) does not trip (memory: gate-bash-deny-false-positive).
    (re.compile(r"\bsed\s+-i\b.*(?:\.abstract-data/hooks-manifest\.json|" + _HOOKS_DIR + ")", re.I),
     "in-place edit of the hooks manifest or a deployed hooks dir — confirm (trust anchor)."),
    (re.compile(r"\b(?:cp|mv|tee)\b\s+.*(?:\.abstract-data/hooks-manifest\.json|" + _HOOKS_DIR + ")", re.I),
     "cp/mv/tee onto the hooks manifest or a deployed hooks dir — confirm (trust anchor)."),
    # ``.*`` (not ``\s*``) after the operator so ``> ./.claude/hooks/x``, an absolute
    # path, or a quoted target is still caught — matching the sibling cp/mv/tee rule.
    (re.compile(r">>?.*(?:\.abstract-data/hooks-manifest\.json|" + _HOOKS_DIR + ")", re.I),
     "redirect onto the hooks manifest or a deployed hooks dir — confirm (trust anchor)."),
    # FR-2.2/1.7: shell write-forms targeting the skill-behavior coverage manifest or an
    # eval baseline are eval trust-anchor tampering — escalate to human. Anchored to a
    # write verb *followed by* the target so a bare mention in an unrelated arg (e.g. a
    # --note) does not trip (memory: gate-bash-deny-false-positive).
    (re.compile(r"\bsed\s+-i\b.*(?:tests/skill-behavior/coverage\.yaml|evals/baselines/)", re.I),
     "in-place edit of the coverage manifest or evals/baselines/ — confirm (eval trust anchor)."),
    (re.compile(r"\b(?:cp|mv|tee)\b\s+.*(?:tests/skill-behavior/coverage\.yaml|evals/baselines/)", re.I),
     "cp/mv/tee onto the coverage manifest or evals/baselines/ — confirm (eval trust anchor)."),
    (re.compile(r">>?.*(?:tests/skill-behavior/coverage\.yaml|evals/baselines/)", re.I),
     "redirect onto the coverage manifest or evals/baselines/ — confirm (eval trust anchor)."),
    # FR-6.6: shell write-forms onto the authoring repo's enforcement sources — the hook
    # source tree, the frozenset-bearing catalog-sync test, and the selection-narrowing
    # file — get ASK friction backing human PR review (the enforcement pin is a
    # diff-visibility aid, not a mechanical control; FR-2.2). Anchored to a write verb
    # *followed by* the target so a bare mention in a --note does not trip.
    (re.compile(r"\bsed\s+-i\b.*" + _FR66_TARGETS, re.I),
     "in-place edit of an enforcement source (hook sources / catalog-sync test / "
     "selection.toml) — confirm (FR-6.6 authoring-repo trust anchor)."),
    (re.compile(r"\b(?:cp|mv|tee)\b\s+.*" + _FR66_TARGETS, re.I),
     "cp/mv/tee onto an enforcement source (hook sources / catalog-sync test / "
     "selection.toml) — confirm (FR-6.6 authoring-repo trust anchor)."),
    (re.compile(r">>?.*" + _FR66_TARGETS, re.I),
     "redirect onto an enforcement source (hook sources / catalog-sync test / "
     "selection.toml) — confirm (FR-6.6 authoring-repo trust anchor)."),
    # FR-3.4: `hooks provision` writes into EVERY root it is handed — one confirmation
    # covering a whole fleet, with the apply-preflight escape set for its children.
    # Anchored on the BINARY (`abstract[-_]data … hooks provision`) rather than on the
    # words, so prose mentioning "hooks provision" in a commit message or a --note
    # cannot trip it (memory: gate-bash-deny-false-positive).
    (re.compile(r"\babstract[-_]data\b(?:\s+\S+)*\s+hooks\s+provision\b"),
     "Fleet provisioning: `hooks provision` runs apply/retrofit across every root given "
     "— confirm the root list and that a fleet-wide write is intended."),
]

# Edit/Write DENY by path: hook self-modification + the state store.
#
# Patterns are case-INSENSITIVE: on a case-insensitive filesystem (macOS APFS,
# Windows) a case-varied path (``.Claude/hooks/gate.py``) resolves to the same
# protected file, so a case-sensitive rule would be a trivial Edit/Write bypass.
PATH_DENY = [
    (re.compile(_HOOKS_DIR, re.I),
     "Editing enforcement hook files is blocked. Change them via a reviewed PR."),
    (re.compile(r"\.claude/settings(\.local)?\.json$", re.I),
     "Editing hook settings is blocked. Change them via a reviewed PR."),
    # FR-12: the committed manifest is a trust anchor with the same Edit/Write
    # protection as .claude/hooks/. (Also covered by the .abstract-data/ rule
    # below; kept explicit so the trust-anchor intent is legible.)
    (re.compile(r"\.abstract-data/hooks-manifest\.json$", re.I),
     "Editing the hooks manifest is blocked. It is a trust anchor; reconcile via "
     "the state CLI / a reviewed PR."),
    # Defense-in-depth (spec §9 step 3): block a raw Edit/Write into the state
    # store dir (state.db, attestations/*.json, ledgers). This closes the
    # raw-file forge path only; it does NOT claim to close the sqlite3/`python -c`
    # bypass (per the honest FR-7 threat model). Writes go through the state CLI.
    (re.compile(r"\.abstract-data/", re.I),
     "Direct writes to the .abstract-data/ state store are blocked. Use the "
     "`abstract-data state` CLI / attestation API."),
    # FR-2.2/1.7: the skill-behavior coverage manifest and the eval baselines are
    # trust anchors on the same footing as the hooks manifest — a raw Edit/Write
    # silently changes what "passing" means. Regenerate via the sanctioned
    # eval-compile path / a reviewed PR, never a direct edit.
    (re.compile(r"tests/skill-behavior/coverage\.yaml$", re.I),
     "Editing the skill-behavior coverage manifest is blocked. It is an eval trust "
     "anchor; regenerate it via the eval-compile path / a reviewed PR."),
    (re.compile(r"evals/baselines/", re.I),
     "Editing eval baselines is blocked. They are trust anchors; regenerate them via "
     "the eval-compile path / a reviewed PR."),
]


def path_denied(file_path: str) -> bool:
    """True when a raw Edit/Write to ``file_path`` is blocked by :data:`PATH_DENY`."""
    return any(pat.search(file_path) for pat, _ in PATH_DENY)


# FR-6.2: a narrow subset of the PATH_DENY trust anchors, scanned across ANY field
# of an UNRECOGNIZED event payload. Kept deliberately narrower than the full
# PATH_DENY eval-anchor set — this is a backstop for novel event shapes, not a
# second write-gate. Matched case-insensitively against `/`-normalized values.
_PROTECTED_PAYLOAD_SUBSTR = (".claude/hooks/", ".abstract-data/", ".claude/settings")


def _protected_path_in_payload(payload: object, _depth: int = 0) -> str | None:
    """First string value anywhere in ``payload`` referencing a protected path, else None.

    FR-6.2: for events ``_extract_tool`` does NOT recognize (``kind == ""``), a novel
    event name could carry a protected-path operation under an arbitrary field name and
    slip past ``PATH_DENY`` (which only sees the ``file_path``/``command`` keys). This
    recursively walks every string value (bounded depth) and returns the first one that
    contains a protected fragment (``.claude/hooks/``, ``.abstract-data/``,
    ``.claude/settings``). Deny-ONLY — never consulted for ASK. Fails OPEN (returns
    ``None``) on any error, so a scan bug can never brick a session.
    """
    try:
        if _depth > 6:
            return None
        if isinstance(payload, str):
            low = payload.replace("\\", "/").lower()
            return payload if any(frag in low for frag in _PROTECTED_PAYLOAD_SUBSTR) else None
        if isinstance(payload, dict):
            for value in payload.values():
                hit = _protected_path_in_payload(value, _depth + 1)
                if hit is not None:
                    return hit
            return None
        if isinstance(payload, (list, tuple)):
            for value in payload:
                hit = _protected_path_in_payload(value, _depth + 1)
                if hit is not None:
                    return hit
            return None
        return None
    except Exception:
        return None


def _bash_match(cmd: str) -> tuple[str, str] | None:
    """First matching bash rule as ``(decision, message)``, else ``None``.

    DENY rules win over ASK; within a tier the first pattern wins.
    """
    for pat, msg in BASH_DENY:
        if pat.search(cmd):
            return "deny", msg
    for pat, msg in BASH_ASK:
        if pat.search(cmd):
            return "ask", msg
    return None


def bash_decision(cmd: str) -> str:
    """Pure decision seam for a shell command: ``"deny" | "ask" | "allow"``."""
    match = _bash_match(cmd)
    return match[0] if match else "allow"

# Edit/Write ASK by path: meaning-changing files.
PATH_ASK = [
    (re.compile(r"\.github/workflows/"),
     "CI workflow edit — confirm. CI changes alter what 'passing' means."),
    (re.compile(r"production.*loader|loader.*production", re.I),
     "Production loader edit — confirm. This changes production behavior."),
    (re.compile(r"(^|/)(pyproject\.toml|requirements[^/]*\.txt|uv\.lock|"
                r"package\.json|package-lock\.json|bun\.lock(b)?|pnpm-lock\.yaml)$"),
     "Dependency / lockfile change — confirm. New or changed dependencies."),
    (re.compile(r"(alembic|migrations)/versions/"),
     "Database migration file — confirm."),
    (re.compile(r"(^|/)(Dockerfile|railway\.(json|toml)|vercel\.json|.*\.tf)$"),
     "Infrastructure / deploy config edit — confirm."),
    # FR-6.6: editing an enforcement hook SOURCE (not a deployed .claude/hooks/ copy,
    # which PATH_DENY blocks outright) escalates to a human. These scripts deploy into
    # every project; the enforcement set changes via a reviewed PR. Harmless in target
    # projects, where this source path does not exist.
    (re.compile(r"src/abstract_data/project_tools/hooks/"),
     "Edit to an enforcement hook SOURCE — confirm. These deploy into every project; "
     "change the enforcement set via a reviewed PR (FR-6.6)."),
]


# Cursor read events: permission-capable but default-allow (the gate guards writes,
# never reads). Named once so _extract_tool's classification and cmd_pretool's
# FR-6.2 payload scan agree on which events are reads to be left alone.
_CURSOR_READ_EVENTS = ("beforeReadFile", "beforeTabFileRead")


def _extract_tool(payload: dict) -> tuple[str, str, str]:
    """Return (kind, command, file_path) across Claude, Cursor, and Grok payload shapes.

    kind is 'bash', 'edit', or '' (nothing actionable).
    """
    p = payload or {}
    tool = p.get("tool_name") or p.get("toolName") or ""
    ti = p.get("tool_input") or p.get("toolInput") or {}
    if not isinstance(ti, dict):
        ti = {}

    # Claude shapes (+ Grok native tool names aliased from Claude matchers).
    if tool in ("Bash", "run_terminal_command"):
        return "bash", (ti.get("command") or ""), ""
    if tool in ("Edit", "Write", "MultiEdit", "search_replace", "write"):
        return "edit", "", (ti.get("file_path") or ti.get("path") or "")

    # Cursor shapes (granular events put fields at the top level).
    ev = p.get("hook_event_name") or p.get("hookEventName") or ""
    command = p.get("command") or ti.get("command") or ""
    if ev in ("beforeShellExecution", "afterShellExecution") or (
        command and not tool and not p.get("toolName")
    ):
        return "bash", command, ""
    # Read events (beforeReadFile / beforeTabFileRead) carry a file_path but are NOT
    # writes — the gate guards edits only. Routing a read through the edit path would
    # run PATH_DENY against it and DENY Cursor reads of .claude/hooks/, .abstract-data/,
    # and settings as if they were writes. Short-circuit to nothing-actionable (allow)
    # BEFORE the file_path fallback. Only afterFileEdit is a Cursor file WRITE.
    if ev in _CURSOR_READ_EVENTS:
        return "", "", ""
    file_path = p.get("file_path") or ti.get("file_path") or ti.get("path") or ""
    if ev == "afterFileEdit" or file_path:
        return "edit", "", file_path
    return "", "", ""


def cmd_pretool() -> None:
    payload = read_payload()
    harness = _harness(payload)
    try:
        # Persist the live session id so the CLI record path agrees with the Stop gate.
        resolve_session(project_dir(payload), payload, persist=True)

        kind, command, file_path = _extract_tool(payload)

        if kind == "bash":
            match = _bash_match(command)
            if match:
                emit_pretool(match[0], match[1], harness)
            emit_allow()

        if kind == "edit":
            for pat, msg in PATH_DENY:
                if pat.search(file_path):
                    emit_pretool("deny", msg, harness)
            for pat, msg in PATH_ASK:
                if pat.search(file_path):
                    emit_pretool("ask", msg, harness)
            emit_allow()

        # FR-6.2: unrecognized event (kind == ""). _extract_tool only inspects the
        # known file_path/command keys, so a NOVEL event carrying a protected path
        # under any other field name would fall through to allow. Scan the whole
        # payload and DENY a protected-path reference. The enumerated Cursor read
        # events also classify as "" — they are EXCLUDED here (reads default-allow,
        # per the Cursor contract), so the scan fires only for genuinely novel events.
        event_name = (payload or {}).get("hook_event_name", "")
        hit = None if event_name in _CURSOR_READ_EVENTS else _protected_path_in_payload(payload)
        if hit:
            emit_pretool(
                "deny",
                "Unrecognized event references a protected trust-anchor path "
                f"({hit!r}). Protected-path operations must go through a reviewed PR.",
                harness,
            )
        emit_allow()

    except SystemExit:
        raise
    except Exception as exc:  # fail OPEN; a pretool bug must not block all work
        sys.stderr.write(f"[gate] internal error in pretool, allowing: {exc}\n")
        emit_allow()


# --------------------------------------------------------------------------- #
# 3. Disposition ledger CLI (called by verify-completion.sh, scripts, or agent)
# --------------------------------------------------------------------------- #
def _arg(flag: str, default: str | None = None) -> str | None:
    a = sys.argv
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def _session_ledger() -> tuple[Path, dict]:
    proj = project_dir()
    session = resolve_session(proj, None)
    lpath = ledger_path(proj, session)
    return lpath, load_ledger(lpath)


def cmd_record_failure() -> None:
    """gate.py record-failure --check NAME [--status failed|skipped] [--detail ...]"""
    name = _arg("--check")
    if not name:
        sys.exit("record-failure: --check NAME is required")
    lpath, ledger = _session_ledger()
    ledger.setdefault("checks", {})[name] = {
        "status": _arg("--status", "failed"),
        "detail": _arg("--detail", ""),
        "disposition": None,
        "at": int(time.time()),
    }
    save_ledger(lpath, ledger)
    print(f"recorded {ledger['checks'][name]['status']} check: {name}")


def cmd_dispose() -> None:
    """gate.py dispose --check NAME --status fixed|deferred|ticket|ignore --note ..."""
    name = _arg("--check")
    status = _arg("--status")
    if not name or status not in ("fixed", "deferred", "ticket", "ignore"):
        sys.exit("dispose: --check NAME and --status fixed|deferred|ticket|ignore required")
    lpath, ledger = _session_ledger()
    rec: dict[str, object] | None = ledger.setdefault("checks", {}).get(name)
    if not rec:
        # allow disposing a check that wasn't formally recorded as failing
        rec = {"status": "failed", "detail": "(no prior record)", "at": int(time.time())}
        ledger["checks"][name] = rec
    rec["disposition"] = {"status": status, "note": _arg("--note", ""), "at": int(time.time())}
    save_ledger(lpath, ledger)
    print(f"disposition recorded for '{name}': {status}")


def cmd_task_critic() -> None:
    """gate.py task-critic --verdict PASS|BLOCK [--note ...]"""
    verdict = _arg("--verdict")
    if verdict not in ("PASS", "BLOCK"):
        sys.exit("task-critic: --verdict PASS|BLOCK required")
    lpath, ledger = _session_ledger()
    ledger["task_critic"] = {"verdict": verdict, "note": _arg("--note", ""), "at": int(time.time())}
    save_ledger(lpath, ledger)
    print(f"task-critic verdict recorded: {verdict}")


def cmd_status() -> None:
    lpath, ledger = _session_ledger()
    require_tc = (project_dir() / "TASK.md").exists()
    items = open_items(ledger, require_task_critic=require_tc)
    print(f"gate v{VERSION} — ledger: {lpath}")
    print(f"task_critic: {ledger.get('task_critic')}")
    print(f"checks: {json.dumps(ledger.get('checks', {}), indent=2)}")
    print(f"open items: {len(items)}")
    for it in items:
        print(f"  - {it}")


# --------------------------------------------------------------------------- #
# dispatch
# --------------------------------------------------------------------------- #
def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    dispatch = {
        "stop-check": cmd_stop_check,
        "pretool": cmd_pretool,
        "record-failure": cmd_record_failure,
        "dispose": cmd_dispose,
        "task-critic": cmd_task_critic,
        "status": cmd_status,
        "version": lambda: print(VERSION),
    }
    fn = dispatch.get(cmd)
    if not fn:
        sys.exit(
            f"gate.py v{VERSION}\nusage: gate.py "
            "{stop-check|pretool|record-failure|dispose|task-critic|status|version}"
        )
    fn()


if __name__ == "__main__":
    main()
