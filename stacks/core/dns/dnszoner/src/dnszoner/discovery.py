"""Container discovery via Docker/Podman socket API."""

from __future__ import annotations

import json
import logging
import re
import urllib.parse
from dataclasses import dataclass, field

import requests_unixsocket

logger = logging.getLogger("dnszoner")

# Hostname regex (RFC 952 / RFC 1123, simplified)
_HOSTNAME_RE = re.compile(
    r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$"
)

_VALID_RECORD_TYPES = frozenset({"A", "CNAME"})


def _is_valid_hostname(name: str) -> bool:
    """Return *True* if *name* looks like a valid DNS hostname."""
    return bool(_HOSTNAME_RE.match(name))


@dataclass(frozen=True)
class DiscoveredService:
    """A DNS record discovered from a running container."""

    container_id: str
    container_name: str
    domain: str
    target: str  # IP address for A records, hostname for CNAME
    record_type: str = "A"
    ttl: int = 300

    def __post_init__(self) -> None:
        if self.record_type not in _VALID_RECORD_TYPES:
            raise ValueError(f"Unsupported record type: {self.record_type!r}")


@dataclass
class DiscoveryClient:
    """Reusable discovery client that holds a persistent HTTP session.

    Create one instance and call :meth:`discover` on each poll cycle.
    Call :meth:`close` (or use as a context manager) when done.
    """

    socket_uri: str
    label_prefix: str = "dnszoner"
    default_ttl: int = 300
    _session: requests_unixsocket.Session = field(
        init=False,
        repr=False,
        default=None,  # type: ignore[assignment]
    )

    def __post_init__(self) -> None:
        self._session = requests_unixsocket.Session()

    # -- context manager --------------------------------------------------

    def __enter__(self) -> DiscoveryClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._session is not None:
            self._session.close()

    # -- public API -------------------------------------------------------

    def discover(self) -> list[DiscoveredService]:
        """Poll the container engine and return discovered services."""
        try:
            return self._discover()
        except Exception:
            logger.exception("Discovery failed")
            return []

    # -- internals --------------------------------------------------------

    def _base_url(self) -> str:
        """Translate a socket URI to the ``requests_unixsocket`` format."""
        if self.socket_uri.startswith("http+unix://"):
            path = self.socket_uri.removeprefix("http+unix://")
            encoded = urllib.parse.quote(path, safe="")
            return f"http+unix://{encoded}"
        return self.socket_uri

    def _api(self, path: str) -> str:
        return f"{self._base_url()}/v1.43{path}"

    def _discover(self) -> list[DiscoveredService]:
        filters = json.dumps({"status": ["running"]})
        resp = self._session.get(
            self._api("/containers/json"),
            params={"filters": filters},
            timeout=10,
        )
        resp.raise_for_status()
        containers: list[dict] = resp.json()

        services: list[DiscoveredService] = []
        for ct in containers:
            svc = self._process_container(ct)
            if svc is not None:
                services.append(svc)
        return services

    def _process_container(self, ct: dict) -> DiscoveredService | None:
        labels: dict[str, str] = ct.get("Labels") or {}
        prefix = self.label_prefix

        # Must be explicitly enabled
        enabled = labels.get(f"{prefix}.enable", "").lower()
        if enabled != "true":
            return None

        # Domain is required
        domain = labels.get(f"{prefix}.domain", "").strip()
        if not domain:
            name = (ct.get("Names") or ["?"])[0].lstrip("/")
            logger.warning(
                "Container %s has %s.enable=true but no domain, skipping",
                name,
                prefix,
            )
            return None

        if not _is_valid_hostname(domain):
            logger.warning("Invalid domain %r, skipping", domain)
            return None

        # Record type
        record_type = labels.get(f"{prefix}.type", "A").upper()
        if record_type not in _VALID_RECORD_TYPES:
            logger.warning(
                "Unsupported record type %r for %s, skipping",
                record_type,
                domain,
            )
            return None

        # TTL
        ttl = self.default_ttl
        ttl_raw = labels.get(f"{prefix}.ttl", "")
        if ttl_raw:
            try:
                ttl = int(ttl_raw)
                if ttl < 1:
                    raise ValueError("TTL must be positive")
            except ValueError:
                logger.warning(
                    "Invalid TTL %r for %s, using default %d",
                    ttl_raw,
                    domain,
                    self.default_ttl,
                )
                ttl = self.default_ttl

        # Preferred network
        preferred_net = labels.get(f"{prefix}.network")

        # Resolve target (IP for A, hostname for CNAME)
        if record_type == "CNAME":
            target = domain  # CNAME target comes from a separate label
            cname_target = labels.get(f"{prefix}.target", "").strip()
            if cname_target:
                target = cname_target
        else:
            target = self._resolve_ip(ct, preferred_net)
            if not target:
                name = (ct.get("Names") or ["?"])[0].lstrip("/")
                logger.warning(
                    "No IP found for container %s (%s), skipping",
                    name,
                    domain,
                )
                return None

        container_id = ct.get("Id", "")[:12]
        container_name = (ct.get("Names") or ["?"])[0].lstrip("/")

        return DiscoveredService(
            container_id=container_id,
            container_name=container_name,
            domain=domain,
            target=target,
            record_type=record_type,
            ttl=ttl,
        )

    def _resolve_ip(
        self,
        ct: dict,
        preferred_network: str | None = None,
    ) -> str | None:
        """Extract a container IP from network settings."""
        networks: dict | None = ct.get("NetworkSettings", {}).get("Networks")
        ip = _get_container_ip(networks, preferred_network)
        if ip:
            return ip

        # Fallback: inspect the container for more detail
        container_id = ct.get("Id", "")[:12]
        try:
            resp = self._session.get(
                self._api(f"/containers/{container_id}/json"),
                timeout=10,
            )
            resp.raise_for_status()
            detail = resp.json()
            networks = detail.get("NetworkSettings", {}).get("Networks")
            return _get_container_ip(networks, preferred_network)
        except Exception:
            logger.debug("Inspect fallback failed for %s", container_id)
            return None


def _get_container_ip(
    networks: dict | None = None,
    preferred_network: str | None = None,
) -> str | None:
    """Extract an IP address from container network settings."""
    if not networks:
        return None

    # Try preferred network first
    if preferred_network and preferred_network in networks:
        ip = networks[preferred_network].get("IPAddress", "")
        if ip:
            return ip

    # Fall back to first network with an IP
    for net_info in networks.values():
        ip = net_info.get("IPAddress", "")
        if ip:
            return ip

    return None
