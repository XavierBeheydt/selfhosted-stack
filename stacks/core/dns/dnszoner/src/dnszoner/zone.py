# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""
DNS zone file generator for DNSZoner.

Generates RFC 1035-compliant zone files from discovered services,
writing them to the CoreDNS zones directory.
"""

import datetime
import logging
import os
from pathlib import Path

from dnszoner.discovery import DiscoveredService

logger = logging.getLogger("dnszoner")


def _generate_serial() -> str:
    """Generate a SOA serial number in YYYYMMDDnn format."""
    now = datetime.datetime.now(datetime.UTC)
    return now.strftime("%Y%m%d%H")


def generate_zone_content(
    domain: str,
    records: list[DiscoveredService],
    default_ttl: int = 300,
) -> str:
    """Generate a DNS zone file content for a given domain.

    Args:
        domain: The zone domain (e.g., 'example.com').
        records: List of discovered services for this zone.
        default_ttl: Default TTL for records.

    Returns:
        The zone file content as a string.
    """
    serial = _generate_serial()

    lines = [
        f"$TTL {default_ttl}",
        f"$ORIGIN {domain}.",
        "",
        f"@  IN  SOA  ns1.{domain}. hostmaster.{domain}. (",
        f"    {serial}  ; serial",
        "    3600       ; refresh",
        "    900        ; retry",
        "    604800     ; expire",
        "    86400      ; minimum",
        ")",
        "",
        f"    IN  NS  ns1.{domain}.",
        "",
        "; Auto-generated records from container labels",
    ]

    for record in records:
        # Extract the subdomain part
        if record.domain == domain:
            name = "@"
        elif record.domain.endswith(f".{domain}"):
            name = record.domain[: -(len(domain) + 1)]
        else:
            # Domain doesn't belong to this zone, use FQDN
            name = record.domain

        ttl = record.ttl if record.ttl != default_ttl else ""
        ttl_str = f"{ttl}  " if ttl else ""

        if record.record_type == "A":
            lines.append(
                f"{name:<20s} {ttl_str}IN  A     {record.ip_address}"
                f"  ; {record.container_name}"
            )
        elif record.record_type == "CNAME":
            lines.append(
                f"{name:<20s} {ttl_str}IN  CNAME {record.ip_address}."
                f"  ; {record.container_name}"
            )

    lines.append("")
    return "\n".join(lines)


def write_zone_file(
    zone_dir: str,
    domain: str,
    content: str,
) -> Path:
    """Write zone file to the zone directory.

    Args:
        zone_dir: Path to the zones directory.
        domain: The domain name (used as filename).
        content: The zone file content.

    Returns:
        Path to the written zone file.
    """
    zone_path = Path(zone_dir) / f"{domain}.db"
    os.makedirs(zone_dir, exist_ok=True)

    # Only write if content has changed
    if zone_path.exists():
        existing = zone_path.read_text()
        # Compare ignoring the serial line (changes every refresh)
        existing_lines = [
            line for line in existing.splitlines() if "; serial" not in line
        ]
        new_lines = [
            line for line in content.splitlines() if "; serial" not in line
        ]
        if existing_lines == new_lines:
            logger.debug("Zone %s unchanged, skipping write", domain)
            return zone_path

    zone_path.write_text(content)
    logger.info("Wrote zone file: %s", zone_path)
    return zone_path


def generate_corefile_includes(
    zone_dir: str,
    domains: list[str],
) -> str:
    """Generate CoreDNS file plugin configuration for discovered zones.

    This generates config blocks that can be included in the Corefile
    or used as a separate config file loaded by CoreDNS.
    """
    blocks = []
    for domain in sorted(domains):
        zone_path = f"{zone_dir}/{domain}.db"
        blocks.append(
            f"{domain} {{\n    file {zone_path}\n    log\n    errors\n}}\n"
        )
    return "\n".join(blocks)
