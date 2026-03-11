"""Entry point: wires CLI, config, health server, and discovery loop."""

from __future__ import annotations

import asyncio
import contextlib
import logging
import signal
from collections import defaultdict
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from dnszoner.cli import cli_parser
from dnszoner.config import DNSZonerConfig
from dnszoner.discovery import DiscoveryClient
from dnszoner.health import start_health_server
from dnszoner.logger import setup_logger
from dnszoner.zone import (
    _read_existing_serial,
    cleanup_stale_zones,
    generate_zone_content,
    write_zone_file,
)

logger = logging.getLogger("dnszoner")


def _group_by_zone(
    services: list,
    base_domain: str,
) -> dict[str, list]:
    """Group discovered services by zone domain.

    Uses *base_domain* as the zone when a service domain is a subdomain
    of it (or equals it).  For domains outside *base_domain*, falls back
    to the last two labels.
    """
    zones: dict[str, list] = defaultdict(list)
    for svc in services:
        domain = svc.domain
        if domain == base_domain or domain.endswith(f".{base_domain}"):
            zones[base_domain].append(svc)
        else:
            # Fallback: last two labels
            parts = domain.rsplit(".", 2)
            zone = ".".join(parts[-2:]) if len(parts) >= 2 else domain
            zones[zone].append(svc)
    return dict(zones)


async def discovery_loop(
    config: DNSZonerConfig,
    status: dict[str, Any],
    stop_event: asyncio.Event,
) -> None:
    """Continuously discover containers and update zone files."""
    with DiscoveryClient(
        socket_uri=config.container_engine_socket,
        label_prefix=config.label_prefix,
        default_ttl=config.default_ttl,
    ) as client:
        while not stop_event.is_set():
            try:
                services = client.discover()
                zones = _group_by_zone(services, config.base_domain)

                # Write/update zone files
                from pathlib import Path

                for zone_domain, records in zones.items():
                    zone_path = Path(config.zone_dir) / f"{zone_domain}.db"
                    existing_serial = _read_existing_serial(zone_path)
                    content = generate_zone_content(
                        zone_domain,
                        records,
                        config.default_ttl,
                        existing_serial,
                    )
                    write_zone_file(config.zone_dir, zone_domain, content)

                # Remove stale zone files
                active_domains = set(zones.keys())
                cleanup_stale_zones(config.zone_dir, active_domains)

                # Update status
                now = datetime.now(UTC).isoformat()
                status["last_refresh"] = now
                status["services_count"] = len(services)
                status["zones"] = list(zones.keys())
                status["services"] = [
                    {
                        "domain": s.domain,
                        "target": s.target,
                        "type": s.record_type,
                    }
                    for s in services
                ]

            except Exception:
                logger.exception("Error in discovery loop")

            # Wait for the refresh interval or stop signal
            try:
                await asyncio.wait_for(
                    stop_event.wait(),
                    timeout=config.refresh_interval,
                )
                break  # stop_event was set
            except TimeoutError:
                continue  # normal poll cycle


async def async_main(config: DNSZonerConfig) -> None:
    """Run the health server and discovery loop until signalled."""
    status: dict[str, Any] = {
        "started": datetime.now(UTC).isoformat(),
        "config": {
            "base_domain": config.base_domain,
            "refresh_interval": config.refresh_interval,
            "label_prefix": config.label_prefix,
        },
    }

    server = await start_health_server(config.host, config.port, status)
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    logger.info(
        "DNSZoner started — polling every %ds for '%s.*' labels",
        config.refresh_interval,
        config.label_prefix,
    )

    task = asyncio.create_task(discovery_loop(config, status, stop_event))

    # Wait until stopped
    await stop_event.wait()
    logger.info("Shutting down...")

    # Clean up
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    server.close()
    await server.wait_closed()
    logger.info("DNSZoner stopped")


def main() -> None:
    """CLI entry point."""
    args = cli_parser()
    level = "DEBUG" if args.verbose else "INFO"
    setup_logger(level)

    # Build config with CLI overrides
    overrides: dict[str, Any] = {}
    cli_map = {
        "container_engine_socket": args.container_engine_socket,
        "host": args.host,
        "port": args.port,
        "refresh_interval": args.refresh_interval,
        "base_domain": args.base_domain,
        "zone_dir": args.zone_dir,
        "label_prefix": args.label_prefix,
        "default_ttl": args.default_ttl,
    }
    for key, value in cli_map.items():
        if value is not None:
            overrides[key] = value

    # Create base config from env, then apply overrides
    base = DNSZonerConfig()
    if overrides:
        config_dict = asdict(base)
        config_dict.update(overrides)
        config = DNSZonerConfig(**config_dict)
    else:
        config = base

    logger.debug("Config: %s", asdict(config))
    asyncio.run(async_main(config))
