"""Typed configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DNSZonerConfig:
    """DNSZoner runtime configuration.

    Values come from environment variables with sensible defaults.
    Validated at construction time via ``__post_init__``.
    """

    container_engine_socket: str = ""
    host: str = ""
    port: int = 0
    refresh_interval: int = 0
    zone_dir: str = ""
    base_domain: str = ""
    label_prefix: str = ""
    default_ttl: int = 0

    def __post_init__(self) -> None:
        defaults: dict[str, str | int] = {
            "container_engine_socket": os.getenv(
                "CONTAINER_ENGINE_SOCKET",
                "http+unix:///var/run/container_engine.sock",
            ),
            "host": os.getenv("DNSZONER_HOST", "0.0.0.0"),
            "port": int(os.getenv("DNSZONER_PORT", "8080")),
            "refresh_interval": int(
                os.getenv("DNSZONER_REFRESH_INTERVAL", "5")
            ),
            "zone_dir": os.getenv("DNSZONER_ZONE_DIR", "/etc/coredns/zones"),
            "base_domain": os.getenv("DNSZONER_BASE_DOMAIN", "localhost"),
            "label_prefix": os.getenv("DNSZONER_LABEL_PREFIX", "dnszoner"),
            "default_ttl": int(os.getenv("DNSZONER_DEFAULT_TTL", "300")),
        }

        # Apply defaults where the caller left the zero-value sentinel.
        for field, default in defaults.items():
            current = getattr(self, field)
            sentinel = "" if isinstance(default, str) else 0
            if current == sentinel:
                object.__setattr__(self, field, default)

        # Validate
        if not 1 <= self.port <= 65535:
            raise ValueError(f"port must be 1-65535, got {self.port}")
        if self.refresh_interval < 1:
            raise ValueError(
                f"refresh_interval must be >= 1, got {self.refresh_interval}"
            )
        if self.default_ttl < 1:
            raise ValueError(
                f"default_ttl must be >= 1, got {self.default_ttl}"
            )
        if not self.base_domain:
            raise ValueError("base_domain must not be empty")
