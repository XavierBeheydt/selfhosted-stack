# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""
Default values and typed config for DNSZoner.
"""

from dataclasses import dataclass, field
from os import getenv


@dataclass(frozen=True)
class DNSZonerConfig:
    """Configuration for DNS-Zoner, populated from environment variables."""

    container_engine_socket: str = field(
        default_factory=lambda: getenv(
            "CONTAINER_ENGINE_SOCKET",
            "http+unix:///var/run/container_engine.sock",
        )
    )
    host: str = field(
        default_factory=lambda: getenv("DNSZONER_HOST", "0.0.0.0")
    )
    port: int = field(
        default_factory=lambda: int(getenv("DNSZONER_PORT", "8080"))
    )
    refresh_interval: int = field(
        default_factory=lambda: int(getenv("DNSZONER_REFRESH_INTERVAL", "5"))
    )
    zone_dir: str = field(
        default_factory=lambda: getenv(
            "DNSZONER_ZONE_DIR", "/etc/coredns/zones"
        )
    )
    base_domain: str = field(
        default_factory=lambda: getenv("DNSZONER_BASE_DOMAIN", "localhost")
    )
    label_prefix: str = field(
        default_factory=lambda: getenv("DNSZONER_LABEL_PREFIX", "dnszoner")
    )
    default_ttl: int = field(
        default_factory=lambda: int(getenv("DNSZONER_DEFAULT_TTL", "300"))
    )
