from __future__ import annotations

import os
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Optional

import httpx


def _env_flag(name: str, default: str = "1") -> bool:
    value = os.getenv(name, default)
    return value.lower() not in {"0", "false", "no"}


@dataclass
class LibpostalContainerConfig:
    """Configuration for managing the libpostal API container."""

    image: str = field(
        default_factory=lambda: os.getenv(
            "RYANDATA_LIBPOSTAL_IMAGE",
            "ghcr.io/abstract-data/ryandata-addr-utils-libpostal:latest",
        )
    )
    name: str = field(
        default_factory=lambda: os.getenv("RYANDATA_LIBPOSTAL_CONTAINER", "ryandata-libpostal")
    )
    host: str = field(default_factory=lambda: os.getenv("RYANDATA_LIBPOSTAL_HOST", "127.0.0.1"))
    host_port: int = field(
        default_factory=lambda: int(os.getenv("RYANDATA_LIBPOSTAL_PORT", "8000"))
    )
    container_port: int = field(
        default_factory=lambda: int(os.getenv("RYANDATA_LIBPOSTAL_CONTAINER_PORT", "8000"))
    )
    auto_pull: bool = field(default_factory=lambda: _env_flag("RYANDATA_LIBPOSTAL_PULL", "1"))
    environment: Optional[Mapping[str, str]] = None
    command: Optional[Sequence[str]] = None


def _wait_for_health(url: str, *, timeout: float = 60.0) -> None:
    """Poll the API health endpoint until it reports healthy or timeout."""
    deadline = time.time() + timeout
    last_error = ""
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=5.0)
            if response.status_code == 200:
                return
            last_error = f"status {response.status_code}"
        except Exception as exc:  # pragma: no cover - network errors are expected during startup
            last_error = str(exc)
        time.sleep(1.0)

    raise RuntimeError(
        f"Libpostal container did not become healthy within {timeout:.0f}s "
        f"(last error: {last_error or 'no response'})"
    )


def ensure_libpostal_container(config: LibpostalContainerConfig, *, timeout: float = 60.0) -> str:
    """Ensure a libpostal API container is running and healthy.

    Returns:
        Base URL (http://host:port) for the running container.

    Raises:
        RuntimeError: If the container cannot be started or health-checked.
    """
    try:
        import docker
        from docker.errors import NotFound
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError(
            "Docker SDK not available. Install extras with "
            "'ryandata-address-utils[remote]' to enable auto-start."
        ) from exc

    client = docker.from_env()

    try:
        container = client.containers.get(config.name)
        if container.status != "running":
            container.start()
    except NotFound:
        if config.auto_pull:
            client.images.pull(config.image)

        command = list(
            config.command
            or (
                "uvicorn",
                "ryandata_address_utils.api:app",
                "--host",
                "0.0.0.0",
                "--port",
                str(config.container_port),
            )
        )

        container = client.containers.run(
            config.image,
            name=config.name,
            detach=True,
            ports={f"{config.container_port}/tcp": config.host_port},
            environment=config.environment,
            command=command,
            labels={"ryandata.libpostal": "1"},
        )

    base_url = f"http://{config.host}:{config.host_port}"
    _wait_for_health(f"{base_url}/health", timeout=timeout)
    return base_url
