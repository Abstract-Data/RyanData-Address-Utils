from __future__ import annotations

import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import typer

# The official libpostal data bundles
DATA_ARCHIVES: list[tuple[str, str]] = [
    (
        "libpostal data",
        "https://public-read-libpostal-data.s3.amazonaws.com/v1.1.0/libpostal_data.tar.gz",
    ),
    (
        "language classifier",
        "https://public-read-libpostal-data.s3.amazonaws.com/v1.1.0/language_classifier.tar.gz",
    ),
    (
        "parser model",
        "https://public-read-libpostal-data.s3.amazonaws.com/v1.1.0/parser.tar.gz",
    ),
]

app = typer.Typer(help="Set up libpostal locally without Docker.")


def _init_trogon(app: typer.Typer) -> None:
    """Optionally enable the Trogon TUI when supported."""

    if sys.version_info < (3, 10):
        return
    try:
        from trogon.typer import init_tui
    except Exception:
        return
    init_tui(app, command="tui", help="Open interactive setup UI.")


_init_trogon(app)


def _default_args(argv: list[str]) -> list[str]:
    """Allow running without specifying the 'setup' subcommand.

    If the user passes only options, we prepend the 'setup' command so
    Typer routes arguments correctly. Explicit subcommands still work:
    `uv tool run ryandata_address_utils setup ...`.
    """

    if not argv or argv[0].startswith("-"):
        return ["setup", *argv]
    return argv


@dataclass
class PlatformInfo:
    name: str
    distro: Optional[str] = None


def detect_platform() -> PlatformInfo:
    system = platform.system().lower()
    if system == "darwin":
        return PlatformInfo(name="macos")
    if system == "windows":
        return PlatformInfo(name="windows")
    if system == "linux":
        distro = _read_os_release()
        return PlatformInfo(name="linux", distro=distro)
    return PlatformInfo(name=system or "unknown")


def _read_os_release() -> Optional[str]:
    os_release = Path("/etc/os-release")
    if not os_release.exists():
        return None
    data: dict[str, str] = {}
    for line in os_release.read_text().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"')
    return data.get("ID")


def default_data_dir(info: PlatformInfo) -> Path:
    if info.name == "windows":
        return Path("C:/libpostal")
    if info.name == "macos":
        return Path.home() / ".libpostal-data"
    return Path("/usr/local/share/libpostal")


def run_command(cmd: Iterable[str], *, dry_run: bool = False) -> None:
    display = " ".join(cmd)
    if dry_run:
        typer.echo(f"[dry-run] {display}")
        return
    typer.echo(f"$ {display}")
    subprocess.run(list(cmd), check=True)


def ensure_dir(path: Path) -> None:
    try:
        path.mkdir(parents=True, exist_ok=True)
    except PermissionError as exc:
        raise PermissionError(
            f"Cannot create data directory at '{path}'. "
            "Use a path you have permissions for or re-run with elevated permissions."
        ) from exc


def install_libpostal(info: PlatformInfo, *, dry_run: bool = False) -> None:
    """Attempt to install libpostal system packages where possible."""
    if info.name == "macos":
        if shutil.which("brew"):
            run_command(["brew", "install", "libpostal"], dry_run=dry_run)
        else:
            typer.echo("Homebrew not found. Install Homebrew first: https://brew.sh/")
    elif info.name == "linux":
        distro = (info.distro or "").lower()
        if distro in {"ubuntu", "debian"}:
            run_command(["sudo", "apt-get", "update"], dry_run=dry_run)
            run_command(
                ["sudo", "apt-get", "install", "-y", "libpostal", "libpostal-data"],
                dry_run=dry_run,
            )
        elif distro in {"fedora", "rhel", "centos", "rocky", "almalinux"}:
            if shutil.which("dnf"):
                run_command(
                    ["sudo", "dnf", "install", "-y", "libpostal", "libpostal-data"],
                    dry_run=dry_run,
                )
            else:
                run_command(
                    ["sudo", "yum", "install", "-y", "libpostal", "libpostal-data"],
                    dry_run=dry_run,
                )
        else:
            typer.echo(
                "Unknown Linux distribution. Please install libpostal from source:\n"
                "  git clone https://github.com/openvenues/libpostal\n"
                "  cd libpostal && ./bootstrap.sh && ./configure && make && sudo make install\n"
                "  sudo ldconfig"
            )
    elif info.name == "windows":
        typer.echo("Windows is not officially supported by libpostal. Use WSL for installation.")
    else:
        typer.echo(f"Unsupported platform '{info.name}'. Please install libpostal manually.")


def download_archives(target_dir: Path, *, dry_run: bool = False) -> None:
    ensure_dir(target_dir)
    for label, url in DATA_ARCHIVES:
        typer.echo(f"Downloading {label}...")
        if dry_run:
            typer.echo(f"[dry-run] Would fetch {url} to {target_dir}")
            continue

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            import urllib.request

            with urllib.request.urlopen(url) as response, tmp_path.open("wb") as outf:
                shutil.copyfileobj(response, outf)

            with tarfile.open(tmp_path, "r:gz") as tar:
                tar.extractall(target_dir)
        finally:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)


def data_present(path: Path) -> bool:
    markers = ["language_classifier", "parser", "libpostal", "libpostal_data"]
    if any((path / marker).exists() for marker in markers):
        return True
    return any(path.glob("*"))


def check_libpostal(data_dir: Path) -> tuple[bool, Optional[str]]:
    """Verify libpostal bindings + data are usable."""
    try:
        if data_dir:
            os.environ.setdefault("LIBPOSTAL_DATA_DIR", str(data_dir))
        from postal.parser import parse_address

        parse_address("10 Downing St, London")
        return True, None
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def ensure_postal_binding(*, dry_run: bool = False) -> None:
    """Ensure the Python bindings are installed; if missing, guide installation."""
    try:
        import postal  # noqa: F401
        return
    except ImportError:
        typer.echo("Python binding 'postal' not found.")
        typer.echo("Install with: pip install postal  (or uv add postal)")
        if not dry_run:
            typer.echo("Attempting installation via pip...")
            try:
                run_command([shutil.which("pip") or "pip", "install", "postal"], dry_run=dry_run)
                return
            except Exception as exc:  # noqa: BLE001
                typer.echo(f"Automatic install failed: {exc}")


@app.command()
def setup(
    data_dir: Optional[Path] = typer.Option(  # noqa: B008
        None,
        "--data-dir",
        help="System-wide libpostal data directory (default depends on OS).",
    ),
    yes: bool = typer.Option(  # noqa: B008
        False,
        "--yes",
        "-y",
        help="Auto-confirm installations/downloads.",
    ),
    check_only: bool = typer.Option(  # noqa: B008
        False,
        "--check-only",
        help="Only check status; do not install or download.",
    ),
    dry_run: bool = typer.Option(  # noqa: B008
        False,
        "--dry-run",
        help="Show actions without executing commands or downloads.",
    ),
) -> None:
    """Detect OS, ensure libpostal is installed, and fetch data files."""
    info = detect_platform()
    typer.echo(f"Detected platform: {info.name}{f' ({info.distro})' if info.distro else ''}")

    resolved_data_dir = data_dir or default_data_dir(info)
    if data_dir is None and not check_only:
        prompt_default = str(resolved_data_dir)
        prompt_msg = (
            "Where should libpostal data be stored? "
            "This should be a system-wide location (not project-specific) so future "
            "projects can reuse it."
        )
        user_input = typer.prompt(prompt_msg, default=prompt_default)
        resolved_data_dir = Path(user_input).expanduser()

    typer.echo(f"Using data directory: {resolved_data_dir}")
    ensure_dir(resolved_data_dir)

    # 1) Python binding
    ensure_postal_binding(dry_run=dry_run)

    if check_only:
        ok, reason = check_libpostal(resolved_data_dir)
        if ok:
            typer.echo("libpostal is available and data checks passed.")
            raise typer.Exit(code=0)
        typer.echo(f"libpostal check failed: {reason}")
        raise typer.Exit(code=1)

    # 2) System packages
    if yes or typer.confirm("Install/verify libpostal system packages?", default=True):
        install_libpostal(info, dry_run=dry_run)

    # 3) Data download
    existing_data = data_present(resolved_data_dir)
    if existing_data:
        typer.echo("Data already present in the chosen directory.")
    should_download = False
    if existing_data:
        should_download = yes or typer.confirm(
            "Re-download libpostal data into this directory?", default=False
        )
    else:
        should_download = yes or typer.confirm(
            "Download libpostal data into the chosen directory?", default=True
        )

    if should_download:
        download_archives(resolved_data_dir, dry_run=dry_run)

    # 4) Final verification
    ok, reason = check_libpostal(resolved_data_dir)
    if ok:
        typer.echo("libpostal is ready to use.")
        typer.echo(
            f"Ensure the environment variable is set: LIBPOSTAL_DATA_DIR={resolved_data_dir}"
        )
        raise typer.Exit(code=0)

    typer.echo("libpostal verification failed.")
    typer.echo(reason or "Unknown error")
    typer.echo(
        "If the error mentions missing data, ensure the data directory contains the "
        "extracted archives and that LIBPOSTAL_DATA_DIR points to it."
    )
    raise typer.Exit(code=1)


def main() -> None:
    app()


def cli_entrypoint() -> None:
    """Wrapper so `uv tool run ryandata_address_utils --setup` works like Ruff."""

    from typer.main import get_command

    cmd = get_command(app)
    argv = _default_args(sys.argv[1:])
    cmd.main(args=argv, prog_name="ryandata_address_utils", standalone_mode=True)


if __name__ == "__main__":
    main()
