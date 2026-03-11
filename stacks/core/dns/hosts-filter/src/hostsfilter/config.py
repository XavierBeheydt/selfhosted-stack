"""Configuration management for Hosts Filter service."""

import os
from typing import Optional


class Config:
    """Configuration for Hosts Filter service."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        data_dir: Optional[str] = None,
    ) -> None:
        self.host = host or os.environ.get("HOSTSFILTER_HOST", "0.0.0.0")
        self.port = port or int(os.environ.get("HOSTSFILTER_PORT", "8000"))
        self.data_dir = data_dir or os.environ.get(
            "HOSTSFILTER_DATA_DIR", "/data"
        )

    def __repr__(self) -> str:
        return (
            f"Config(host={self.host!r}, port={self.port!r}, "
            f"data_dir={self.data_dir!r})"
        )
