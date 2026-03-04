# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""
Container discovery engine for DNSZoner.

Connects to the container engine socket (Docker/Podman) and discovers
services via labels (dnszoner.enable=true, dnszoner.domain=...).
Uses the Docker-compatible API which works with both Docker and Podman.
"""

import logging
from dataclasses import dataclass

import requests_unixsocket

logger = logging.getLogger("dnszoner")


@dataclass(frozen=True)
class DiscoveredService:
    """A service discovered from container labels."""

    container_id: str
    container_name: str
    domain: str
    ip_address: str
    record_type: str = "A"
    ttl: int = 300


def _socket_path_from_uri(uri: str) -> str:
    """Convert a socket URI to requests_unixsocket format.

    Converts 'http+unix:///var/run/container_engine.sock' to
    'http+unix://%2Fvar%2Frun%2Fcontainer_engine.sock'
    """
    prefix = "http+unix://"
    if uri.startswith(prefix):
        path = uri[len(prefix) :]
        # URL-encode the path slashes
        encoded = path.replace("/", "%2F")
        return f"{prefix}{encoded}"
    return uri


def _get_container_ip(
    networks: dict | None = None,
    preferred_network: str | None = None,
) -> str | None:
    """Extract IP address from container network settings."""
    if not networks:
        return None

    # Try preferred network first
    if preferred_network and preferred_network in networks:
        net = networks[preferred_network]
        ip = net.get("IPAddress", "")
        if ip:
            return ip

    # Fall back to first network with an IP
    for _net_name, net_info in networks.items():
        ip = net_info.get("IPAddress", "")
        if ip:
            return ip

    return None


def discover_services(
    socket_uri: str,
    label_prefix: str = "dnszoner",
    default_ttl: int = 300,
) -> list[DiscoveredService]:
    """Discover services from running containers via labels.

    Scans all running containers for labels matching the pattern:
      - {label_prefix}.enable=true    (required)
      - {label_prefix}.domain=<fqdn>  (required)
      - {label_prefix}.type=A|CNAME   (optional, default: A)
      - {label_prefix}.ttl=<seconds>  (optional)
      - {label_prefix}.network=<name> (optional, preferred network for IP)

    Uses the Docker-compatible API (/containers/json + /containers/{id}/json)
    which works with both Docker Engine and Podman.
    """
    base_url = _socket_path_from_uri(socket_uri)
    session = requests_unixsocket.Session()
    services: list[DiscoveredService] = []

    try:
        # List all running containers
        resp = session.get(
            f"{base_url}/v1.43/containers/json",
            params={"filters": '{"status":["running"]}'},
            timeout=10,
        )
        resp.raise_for_status()
        containers = resp.json()
    except Exception:
        logger.exception("Failed to list containers from %s", socket_uri)
        return services

    for container in containers:
        container_id = container.get("Id", "")[:12]
        labels = container.get("Labels", {})

        # Check if dnszoner is enabled for this container
        enable_key = f"{label_prefix}.enable"
        if labels.get(enable_key, "").lower() != "true":
            continue

        # Get the domain label
        domain_key = f"{label_prefix}.domain"
        domain = labels.get(domain_key, "")
        if not domain:
            logger.warning(
                "Container %s has %s=true but no %s label, skipping",
                container_id,
                enable_key,
                domain_key,
            )
            continue

        # Get optional labels
        record_type = labels.get(f"{label_prefix}.type", "A").upper()
        ttl = int(labels.get(f"{label_prefix}.ttl", str(default_ttl)))
        preferred_network = labels.get(f"{label_prefix}.network")

        # Get container name
        names = container.get("Names", [])
        name = names[0].lstrip("/") if names else container_id

        # Extract IP from network settings
        network_settings = container.get("NetworkSettings", {})
        networks = network_settings.get("Networks", {})
        ip_address = _get_container_ip(networks, preferred_network)

        if not ip_address:
            # Try inspecting the container for more details
            try:
                inspect_resp = session.get(
                    f"{base_url}/v1.43/containers/{container_id}/json",
                    timeout=10,
                )
                inspect_resp.raise_for_status()
                inspect_data = inspect_resp.json()
                net_settings = inspect_data.get("NetworkSettings", {})
                ip_address = _get_container_ip(
                    net_settings.get("Networks", {}),
                    preferred_network,
                )
            except Exception:
                logger.warning("Could not inspect container %s for IP", name)

        if not ip_address:
            logger.warning(
                "Container %s (%s) has no IP address, skipping",
                name,
                domain,
            )
            continue

        service = DiscoveredService(
            container_id=container_id,
            container_name=name,
            domain=domain,
            ip_address=ip_address,
            record_type=record_type,
            ttl=ttl,
        )
        services.append(service)
        logger.debug("Discovered: %s -> %s (%s)", domain, ip_address, name)

    logger.info("Discovered %d services with DNS labels", len(services))
    return services
