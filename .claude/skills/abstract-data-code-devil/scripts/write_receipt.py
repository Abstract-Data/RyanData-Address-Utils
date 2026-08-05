#!/usr/bin/env python3
"""Write an abstract-data-code-devil review receipt.

The receipt is the artifact that confirms a review actually happened and what it covered: which
critics ran, in what mode, whether Context7 grounding was used, the severity tally, and the
surface-area checklist. Treat a run without a receipt as incomplete.

Writes both <out>.json (machine-readable / auditable) and <out>.md (human-readable). The critics'
Synthesizer emits a `RECEIPT_COUNTS: critical=.. high=.. medium=.. low=..` line you can read the
counts from.

Example:
  python scripts/write_receipt.py \
    --target "api/ (auth + billing routes)" \
    --mode security-deep \
    --critics LeadCritic,SecurityAuditor,FailureModeAnalyst,RedTeamAttacker,Synthesizer \
    --context7 used \
    --critical 2 --high 5 --medium 8 --low 3 \
    --checked "auth,input validation,error handling,concurrency,dependencies,tests" \
    --out ./review-receipt
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

SKILL_VERSION = "0.9.1"

# The full council, used to show what was NOT run for the chosen mode.
ALL_CRITICS = [
    "Cartographer",
    "LeadCritic",
    "RedTeamAttacker",
    "SecurityAuditor",
    "MaintainabilityEnforcer",
    "FailureModeAnalyst",
    "Synthesizer",
]

# A default surface-area checklist. The review confirms each item was considered; --checked marks
# which were actively examined for this target.
DEFAULT_SURFACES = [
    "auth",
    "input validation",
    "error handling",
    "concurrency",
    "dependencies",
    "tests",
    "performance",
    "data flow",
]


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Write an abstract-data-code-devil review receipt.")
    p.add_argument("--target", required=True, help="What was reviewed (repo/module/diff).")
    p.add_argument(
        "--mode",
        default="audit-only",
        choices=["audit-only", "full", "security-deep", "maintainability-deep", "quick"],
        help="Review mode that was run.",
    )
    p.add_argument(
        "--critics",
        required=True,
        help="Comma-separated critics that actually ran (e.g., LeadCritic,SecurityAuditor,Synthesizer).",
    )
    p.add_argument(
        "--context7",
        default="unavailable",
        choices=["used", "unavailable", "not-needed"],
        help="Whether Context7 documentation grounding was used.",
    )
    p.add_argument("--critical", type=int, default=0)
    p.add_argument("--high", type=int, default=0)
    p.add_argument("--medium", type=int, default=0)
    p.add_argument("--low", type=int, default=0)
    p.add_argument(
        "--checked",
        default="",
        help="Comma-separated surface areas actively examined. Defaults to the standard checklist.",
    )
    p.add_argument(
        "--reviewer",
        default="abstract-data-code-devil council",
        help="Label for who/what produced the review.",
    )
    p.add_argument("--notes", default="", help="Optional free-text notes.")
    p.add_argument(
        "--out",
        default="./review-receipt",
        help="Output path stem; writes <out>.json and <out>.md.",
    )
    return p.parse_args(argv)


def _split(csv: str) -> list[str]:
    return [item.strip() for item in csv.split(",") if item.strip()]


def build_receipt(args: argparse.Namespace) -> dict:
    critics_ran = _split(args.critics)
    unknown = [c for c in critics_ran if c not in ALL_CRITICS]
    if unknown:
        print(f"warning: unrecognized critic name(s): {', '.join(unknown)}", file=sys.stderr)
    critics_skipped = [c for c in ALL_CRITICS if c not in critics_ran]

    checked = _split(args.checked) or list(DEFAULT_SURFACES)
    surfaces = [{"surface": s, "examined": s in checked} for s in sorted(set(DEFAULT_SURFACES) | set(checked))]

    counts = {
        "critical": args.critical,
        "high": args.high,
        "medium": args.medium,
        "low": args.low,
    }
    counts["total"] = sum(counts.values())

    return {
        "skill": "abstract-data-code-devil",
        "skill_version": SKILL_VERSION,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "target": args.target,
        "mode": args.mode,
        "reviewer": args.reviewer,
        "context7_grounding": args.context7,
        "critics_ran": critics_ran,
        "critics_skipped": critics_skipped,
        "findings": counts,
        "surfaces_reviewed": surfaces,
        "notes": args.notes,
        "review_complete": bool(critics_ran) and "Synthesizer" in critics_ran,
    }


def render_markdown(r: dict) -> str:
    f = r["findings"]
    lines = [
        "# Adversarial Code Critic — Review Receipt",
        "",
        f"- **Target:** {r['target']}",
        f"- **Mode:** {r['mode']}",
        f"- **Reviewer:** {r['reviewer']}",
        f"- **Timestamp (UTC):** {r['timestamp_utc']}",
        f"- **Skill version:** {r['skill_version']}",
        f"- **Context7 grounding:** {r['context7_grounding']}",
        f"- **Review complete:** {'yes' if r['review_complete'] else 'NO — Synthesizer did not run'}",
        "",
        "## Critics",
        f"- **Ran:** {', '.join(r['critics_ran']) or '(none)'}",
        f"- **Skipped (for this mode):** {', '.join(r['critics_skipped']) or '(none)'}",
        "",
        "## Findings",
        f"- Critical: {f['critical']} · High: {f['high']} · Medium: {f['medium']} · Low: {f['low']} "
        f"· **Total: {f['total']}**",
        "",
        "## Surface-area checklist",
    ]
    for s in r["surfaces_reviewed"]:
        lines.append(f"- [{'x' if s['examined'] else ' '}] {s['surface']}")
    if r["notes"]:
        lines += ["", "## Notes", r["notes"]]
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)
    receipt = build_receipt(args)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    json_path = out.with_suffix(".json")
    md_path = out.with_suffix(".md")
    json_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(receipt), encoding="utf-8")

    print(f"Receipt written:\n  {json_path}\n  {md_path}")
    if not receipt["review_complete"]:
        print("NOTE: review marked incomplete (Synthesizer not among critics that ran).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
