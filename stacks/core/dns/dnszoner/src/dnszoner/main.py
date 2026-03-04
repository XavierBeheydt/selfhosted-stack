# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""
DNS-Zoner main entry point.

Runs the discovery loop: periodically scans running containers for
dnszoner labels and regenerates CoreDNS zone files.
"""

import asyncio
import datetime
import logging
import signal
from collections import defaultdict

from dnszoner.cli import cli_parser
from dnszoner.config import DNSZonerConfig
from dnszoner.discovery import discover_services
from dnszoner.health import start_health_server
from dnszoner.logger import setup_logger
from dnszoner.zone import generate_zone_content, write_zone_file

logger = logging.getLogger("dnszoner")


async def discovery_loop(
    config: DNSZonerConfig,
    status: dict,
) -> None:
    """Main discovery loop: scan containers and update zone files."""
    while True:
        try:
            services = discover_services(
                socket_uri=config.container_engine_socket,
                label_prefix=config.label_prefix,
                default_ttl=config.default_ttl,
            )

            # Group services by base domain
            zones: dict[str, list] = defaultdict(list)
            for svc in services:
                # Extract the zone domain (last two parts of FQDN)
                parts = svc.domain.split(".")
                if len(parts) >= 2:
                    zone_domain = ".".join(parts[-2:])
                else:
                    zone_domain = config.base_domain
                zones[zone_domain].append(svc)

            # Generate and write zone files
            for domain, records in zones.items():
                content = generate_zone_content(
                    domain=domain,
                    records=records,
                    default_ttl=config.default_ttl,
                )
                write_zone_file(
                    zone_dir=config.zone_dir,
                    domain=domain,
                    content=content,
                )

            # Update status
            status["last_refresh"] = datetime.datetime.now(
                datetime.UTC
            ).isoformat()
            status["services_count"] = len(services)
            status["zones_count"] = len(zones)
            status["services"] = [
                {
                    "domain": s.domain,
                    "ip": s.ip_address,
                    "container": s.container_name,
                }
                for s in services
            ]

        except Exception:
            logger.exception("Error in discovery loop")

        await asyncio.sleep(config.refresh_interval)


async def async_main(config: DNSZonerConfig) -> None:
    """Async main: start health server and discovery loop."""
    status: dict = {
        "started_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "services_count": 0,
        "zones_count": 0,
        "last_refresh": None,
        "services": [],
    }

    # Start health server
    health_server = await start_health_server(
        host=config.host,
        port=config.port,
        status=status,
    )

    # Setup graceful shutdown
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown() -> None:
        logger.info("Shutdown signal received")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown)

    # Run discovery loop until shutdown
    discovery_task = asyncio.create_task(discovery_loop(config, status))

    await stop_event.wait()

    # Cleanup
    discovery_task.cancel()
    health_server.close()
    await health_server.wait_closed()
    logger.info("DNSZoner stopped")


def main() -> None:
    """Entry point for DNSZoner."""
    args = cli_parser()
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logger(log_level)

    config = DNSZonerConfig()

    # Override config with CLI args if provided
    overrides = {}
    if args.container_engine_socket is not None:
        overrides["container_engine_socket"] = args.container_engine_socket
    if args.host is not None:
        overrides["host"] = args.host
    if args.port is not None:
        overrides["port"] = args.port
    if args.refresh_interval is not None:
        overrides["refresh_interval"] = args.refresh_interval
    if args.base_domain is not None:
        overrides["base_domain"] = args.base_domain
    if args.zone_dir is not None:
        overrides["zone_dir"] = args.zone_dir

    if overrides:
        # Reconstruct config with overrides (frozen dataclass)
        from dataclasses import asdict

        cfg_dict = asdict(config)
        cfg_dict.update(overrides)
        config = DNSZonerConfig(**cfg_dict)

    logger.info("Starting DNSZoner")
    logger.info("  Socket:   %s", config.container_engine_socket)
    logger.info("  Health:   %s:%d", config.host, config.port)
    logger.info("  Zone dir: %s", config.zone_dir)
    logger.info("  Domain:   %s", config.base_domain)
    logger.info("  Interval: %ds", config.refresh_interval)

    asyncio.run(async_main(config))


if __name__ == "__main__":
    main()
