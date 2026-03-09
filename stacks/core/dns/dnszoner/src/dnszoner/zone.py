"""RFC 1035 zone file generation and management."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from dnszoner.discovery import DiscoveredService

logger = logging.getLogger("dnszoner")

_SERIAL_RE = re.compile(r"(\d{10})\s*;\s*serial", re.IGNORECASE)


def _generate_serial(existing_serial: str | None = None) -> str:
    """Generate an SOA serial in ``YYYYMMDDnn`` format.

    If *existing_serial* starts with today's date prefix, the sequence
    number is incremented (up to 99).  Otherwise a fresh serial for
    today starting at ``01`` is returned.
    """
    today = datetime.now(UTC).strftime("%Y%m%d")
    if existing_serial and existing_serial[:8] == today:
        seq = int(existing_serial[8:10]) + 1
        if seq > 99:
            seq = 99  # cap at 99 per day
        return f"{today}{seq:02d}"
    return f"{today}01"


def _read_existing_serial(zone_path: Path) -> str | None:
    """Extract the SOA serial from an existing zone file, if present."""
    if not zone_path.exists():
        return None
    try:
        content = zone_path.read_text(encoding="utf-8")
        match = _SERIAL_RE.search(content)
        if match:
            return match.group(1)
    except OSError:
        pass
    return None


def generate_zone_content(
    domain: str,
    records: list[DiscoveredService],
    default_ttl: int = 300,
    existing_serial: str | None = None,
) -> str:
    """Generate RFC 1035 zone file content for *domain*."""
    serial = _generate_serial(existing_serial)
    lines = [
        f"$ORIGIN {domain}.",
        f"$TTL {default_ttl}",
        "",
        f"@  IN  SOA  ns1.{domain}. admin.{domain}. (",
        f"    {serial}  ; serial",
        "    3600      ; refresh",
        "    900       ; retry",
        "    604800    ; expire",
        "    86400     ; minimum",
        ")",
        "",
        f"@  IN  NS  ns1.{domain}.",
        "ns1  IN  A  127.0.0.1",
        "",
    ]

    for rec in sorted(records, key=lambda r: r.domain):
        # Determine the record name relative to the zone origin
        if rec.domain == domain:
            name = "@"
        elif rec.domain.endswith(f".{domain}"):
            name = rec.domain[: -(len(domain) + 1)]
        else:
            # Record doesn't belong in this zone — shouldn't happen
            # if grouping is correct, but be defensive.
            logger.warning(
                "Record %s does not belong in zone %s, skipping",
                rec.domain,
                domain,
            )
            continue

        ttl_str = f"{rec.ttl}" if rec.ttl != default_ttl else ""

        if rec.record_type == "CNAME":
            target = rec.target
            if not target.endswith("."):
                target += "."
            lines.append(f"{name}  {ttl_str}  IN  CNAME  {target}")
        else:
            lines.append(f"{name}  {ttl_str}  IN  A  {rec.target}")

    lines.append("")  # trailing newline
    return "\n".join(lines)


def _content_without_serial(content: str) -> str:
    """Return zone content with the serial number zeroed out.

    Used for change detection — we don't want serial differences alone
    to trigger a rewrite.
    """
    return _SERIAL_RE.sub("0000000000 ; serial", content)


def write_zone_file(
    zone_dir: str,
    domain: str,
    content: str,
) -> Path:
    """Write a zone file atomically.

    Returns the path to the written file.  If the records haven't
    changed (ignoring serial), the file is left untouched.
    """
    zone_path = Path(zone_dir) / f"{domain}.db"

    # Check for actual content change (ignore serial)
    if zone_path.exists():
        try:
            existing = zone_path.read_text(encoding="utf-8")
            if _content_without_serial(existing) == _content_without_serial(
                content
            ):
                logger.debug("Zone %s unchanged, skipping write", domain)
                return zone_path
        except OSError:
            pass

    # Atomic write: write to temp file in same directory, then rename
    os.makedirs(zone_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=zone_dir, prefix=f".{domain}.", suffix=".tmp"
    )
    try:
        os.write(fd, content.encode("utf-8"))
        os.close(fd)
        os.replace(tmp_path, zone_path)
    except Exception:
        os.close(fd) if not os.get_inheritable(fd) else None
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise

    logger.info("Wrote zone file %s", zone_path)
    return zone_path


def cleanup_stale_zones(
    zone_dir: str,
    active_domains: set[str],
) -> list[Path]:
    """Remove zone files for domains no longer present.

    Returns list of removed file paths.
    """
    removed: list[Path] = []
    zone_path = Path(zone_dir)
    if not zone_path.is_dir():
        return removed

    for f in zone_path.glob("*.db"):
        domain = f.stem  # e.g. "example.com" from "example.com.db"
        if domain not in active_domains:
            try:
                f.unlink()
                logger.info("Removed stale zone file %s", f)
                removed.append(f)
            except OSError as e:
                logger.warning("Failed to remove %s: %s", f, e)

    return removed
