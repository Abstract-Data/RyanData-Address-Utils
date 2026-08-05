#!/usr/bin/env bash
# verify-completion.sh — repo completion gate (wired as a Stop hook).
#
# Two jobs, in order:
#   1. Keep the enforcement-gate ledger persistent. The gate writes to
#      .claude/state/, which is gitignored and gets cleaned by the GitButler
#      worktree between turns — wiping the task-critic verdict. We relocate the
#      ledger to a stable store OUTSIDE the worktree and restore the symlink here,
#      every turn-end, BEFORE gate.py stop-check reads it.
#   2. Run this repo's checks and record failures into the ledger so the
#      loop-closure gate can refuse to end the turn on an undisposed failure.
#
# ALWAYS exits 0 — the BLOCK is enforced by gate.py reading the ledger.
set -uo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$PWD}"
GATE="$PROJECT_DIR/.claude/hooks/gate.py"
# Fall back to the machine-global gate (~/.claude/hooks/gate.py) so a deployed
# project (which gets no local gate.py) still feeds the global enforcement gate.
[ -f "$GATE" ] || GATE="$HOME/.claude/hooks/gate.py"
[ -f "$GATE" ] || exit 0  # gate not installed anywhere; nothing to enforce

# ── 1. Persist the gate ledger outside the worktree ──────────────────────────
STORE_BASE="$HOME/.local/state/abstract-data-gate"
STORE_KEY="$(printf '%s' "$PROJECT_DIR" | shasum 2>/dev/null | cut -c1-12)"
STORE="$STORE_BASE/${STORE_KEY:-default}"
STATE="$PROJECT_DIR/.claude/state"
mkdir -p "$STORE" 2>/dev/null || true
if [ -d "$STATE" ] && [ ! -L "$STATE" ]; then
  # A real dir means GitButler removed our symlink and the gate wrote here this
  # turn — migrate those ledgers into the persistent store, then re-link.
  cp "$STATE"/*.json "$STORE"/ 2>/dev/null || true
  find "$STATE" -type f -delete 2>/dev/null || true
  rmdir "$STATE" 2>/dev/null || true
fi
[ -e "$STATE" ] || ln -s "$STORE" "$STATE" 2>/dev/null || true

# Read session_id from the Stop payload so our records land in the ledger
# gate.py stop-check reads (it keys the ledger by session_id).
PAYLOAD="$(cat 2>/dev/null || true)"
SESSION_ID="$(
  printf '%s' "$PAYLOAD" | python3 -c 'import sys, json
try:
    print(json.load(sys.stdin).get("session_id", ""))
except Exception:
    print("")' 2>/dev/null || true
)"

rec() {  # rec <check-name> <failed|skipped> <detail>
  python3 "$GATE" record-failure --check "$1" --status "$2" --detail "$3" \
    ${SESSION_ID:+--session "$SESSION_ID"} >/dev/null 2>&1 || true
}

cd "$PROJECT_DIR" 2>/dev/null || exit 0

# ── 2. Repo checks (changed-file scoped; full suite only for declared tasks) ──
# Two scope corrections (#45):
#  (a) EXCLUDE vendored abstract-data-deployed hook files (.claude/.cursor/.agents/.github
#      hooks/*.py) — they are tool-owned artifacts, not this project's source, and formatting
#      them marks them MODIFIED and diverges the bundle (#37).
#  (b) SUBTRACT files that were already dirty at SESSION START (recorded by
#      session-py-baseline.sh) — a session that changed no .py of its own must not be blamed for
#      pre-existing uncommitted drift. Falls back to current behavior when no baseline exists.
BASELINE_FILE="$STORE/py-baseline-$(printf '%s' "${SESSION_ID:-}" | tr -c 'A-Za-z0-9._-' '_').txt"
CHANGED_RAW="$(
  { git diff --name-only HEAD 2>/dev/null; \
    git ls-files --others --exclude-standard 2>/dev/null; } \
  | grep -E '\.py$' \
  | grep -vE '(^|/)\.(claude|cursor|agents|github)/(.*/)?hooks/' \
  | sort -u
)"
if [ -n "${SESSION_ID:-}" ] && [ -n "$CHANGED_RAW" ] && [ -f "$BASELINE_FILE" ]; then
  CHANGED_RAW="$(comm -23 <(printf '%s\n' "$CHANGED_RAW") <(sort -u "$BASELINE_FILE"))"
fi
EXIST=()
while IFS= read -r f; do
  [ -n "$f" ] && [ -f "$f" ] && EXIST+=("$f")
done <<< "$CHANGED_RAW"

TASK_MD="$PROJECT_DIR/TASK.md"

if [ "${#EXIST[@]}" -eq 0 ] && [ ! -f "$TASK_MD" ]; then
  exit 0
fi

if [ "${#EXIST[@]}" -gt 0 ]; then
  if ! uv run ruff check "${EXIST[@]}" >/dev/null 2>&1; then
    rec ruff failed "ruff check failed on changed files: ${EXIST[*]}"
  fi
  # CI parity (issue #25): the quality workflow runs `ruff format --check .` repo-wide, so a
  # format-only drift (correct lint, wrong formatting) passes this gate but fails CI. Mirror it
  # on the changed files — same changed-file scope as ruff check above.
  if ! uv run ruff format --check "${EXIST[@]}" >/dev/null 2>&1; then
    rec ruff-format failed "ruff format --check failed on changed files (run: ruff format ${EXIST[*]})"
  fi
  SRC=()
  for f in "${EXIST[@]}"; do
    case "$f" in src/*) SRC+=("$f");; esac
  done
  if [ "${#SRC[@]}" -gt 0 ]; then
    if ! uv run ty check "${SRC[@]}" >/dev/null 2>&1; then
      rec ty failed "ty check failed on changed src files: ${SRC[*]}"
    fi
  fi
fi

if [ -f "$TASK_MD" ] || [ "${VERIFY_COMPLETION_FULL:-0}" = "1" ]; then
  # Run the unit suite by PATH, not `-m unit` (issue #22): an UNMARKED test under
  # tests/unit/ is silently DESELECTED by `-m unit`, so a project whose tests lack
  # markers gets a false-green gate (e.g. "2 passed, 134 deselected") while CI runs
  # the full suite. Running the directory includes unmarked tests. Fall back to the
  # full run when there is no tests/unit/ directory.
  PYTEST_TARGET="tests/unit"
  [ -d "$PYTEST_TARGET" ] || PYTEST_TARGET=""
  # Parallelize with pytest-xdist ONLY when secrets are already warmed into the env
  # (e.g. running under `op run --environment <id> --`): xdist workers inherit
  # NOTION_TOKEN and take the auth fast-path, so none of them triggers a fresh
  # 1Password biometric prompt. A COLD parallel run would prompt once PER worker,
  # so default to serial (which resolves op once and caches) when the token is absent.
  XDIST=""
  [ -n "${NOTION_TOKEN:-}" ] && command -v uv >/dev/null 2>&1 && \
    uv run python -c "import xdist" >/dev/null 2>&1 && XDIST="-n auto"
  if ! uv run pytest -q $XDIST $PYTEST_TARGET >/dev/null 2>&1; then
    rec pytest failed "uv run pytest ${PYTEST_TARGET:-(full suite)} failed"
  fi
fi

# ── 3. Outcome-eval regression gate (ADR-0015) ───────────────────────────────
# When an eval kit with cases is deployed and `abstract-data` is runnable, gate
# turn-completion on the committed baseline — the same model as ruff/ty/pytest above.
# Scoped to declared tasks (TASK.md present or VERIFY_COMPLETION_FULL=1) so casual turns
# stay fast; off-switch VERIFY_COMPLETION_EVALS=0. Exit 1 = regression (record + block via
# the gate); exit 2 = no kit/adapter/pydantic-evals → skip silently (never a turn failure).
if { [ -f "$TASK_MD" ] || [ "${VERIFY_COMPLETION_FULL:-0}" = "1" ]; } \
   && [ "${VERIFY_COMPLETION_EVALS:-1}" = "1" ] \
   && command -v abstract-data >/dev/null 2>&1 \
   && compgen -G "$PROJECT_DIR/evals/golden/*.y*ml" >/dev/null 2>&1; then
  # issue #276 defect 3: `eval-outcomes` exits 1 for BOTH a real regression and a crash, so the
  # output has to be captured and inspected — otherwise every failure is filed as a baseline
  # regression and the actual cause (ImportError, missing dep, unreachable judge) is discarded.
  EVAL_OUT="$(mktemp -t ad-eval-outcomes)"
  abstract-data eval-outcomes . --json >"$EVAL_OUT" 2>&1
  EVAL_RC=$?
  case $EVAL_RC in
    1)
      if grep -qE 'Traceback \(most recent call last\)|ModuleNotFoundError|ImportError' "$EVAL_OUT"; then
        EVAL_MSG="$(grep -E '^[A-Za-z_.]*(Error|Exception):' "$EVAL_OUT" | tail -1 | cut -c1-200)"
        rec eval-outcomes failed \
          "eval harness CRASHED (not a baseline regression): ${EVAL_MSG:-see: abstract-data eval-outcomes .}"
      elif grep -qE 'declared but produced no assertion' "$EVAL_OUT"; then
        EVAL_MSG="$(grep -E 'declared but produced no assertion' "$EVAL_OUT" | head -1 | cut -c1-200)"
        rec eval-outcomes failed \
          "eval judge unreachable (check \`ollama serve\`, \`ollama list\`, EVAL_JUDGE_MODEL): ${EVAL_MSG}"
      else
        EVAL_MSG="$(grep -iE 'regression:' "$EVAL_OUT" | head -2 | tr '\n' ' ' | cut -c1-200)"
        rec eval-outcomes failed \
          "outcome-eval regression vs committed baseline: ${EVAL_MSG:-run: abstract-data eval-outcomes .}"
      fi
      ;;
  esac
  rm -f "$EVAL_OUT"
fi

exit 0
