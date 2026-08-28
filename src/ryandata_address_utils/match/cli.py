"""Typer commands: uniqueness against a voter file."""

from __future__ import annotations

from pathlib import Path

import typer

from ryandata_address_utils.match.run import run_uniqueness


def uniqueness(
    voterfile: Path = typer.Option(  # noqa: B008
        ...,
        "--voterfile",
        exists=True,
        readable=True,
        help="Texas SOS voter extract (CSV).",
    ),
    sources: str = typer.Option(  # noqa: B008
        "txgio",
        "--sources",
        help="Comma-separated match universes: txgio, tiger, or both.",
    ),
    cache_dir: Path | None = typer.Option(  # noqa: B008
        None,
        "--cache-dir",
        help="Reference cache (default ~/.cache/ryandata-address-utils).",
    ),
    out: Path | None = typer.Option(  # noqa: B008
        None,
        "--out",
        help="Output directory for outcomes.csv and summary.json.",
    ),
    counties: str | None = typer.Option(  # noqa: B008
        None,
        "--counties",
        help="Optional county-name subset. Default: every COUNTY on the voter file.",
    ),
    force_fetch: bool = typer.Option(  # noqa: B008
        False,
        "--force-fetch",
        help="Re-download shapefiles even when the cache looks complete.",
    ),
) -> None:
    """Fetch TxGIO / TIGER ADDRFEAT / TLC precincts as needed and run uniqueness."""
    county_tuple = None
    if counties:
        county_tuple = tuple(
            c.strip().upper().replace("_", " ") for c in counties.split(",") if c.strip()
        )
    summary = run_uniqueness(
        voterfile,
        sources=sources,
        cache_dir=cache_dir,
        out_dir=out,
        counties=county_tuple,
        force_fetch=force_fetch,
    )
    typer.echo(f"wrote {summary['outcomes']} (n={summary['n']}, sources={summary['sources']})")
