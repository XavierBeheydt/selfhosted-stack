# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner zone generation."""

import time
from datetime import UTC, datetime

from dnszoner.discovery import DiscoveredService
from dnszoner.zone import (
    _generate_serial,
    _read_existing_serial,
    cleanup_stale_zones,
    generate_zone_content,
    write_zone_file,
)


class TestSerialGeneration:
    """Test SOA serial number generation."""

    def test_fresh_serial(self):
        serial = _generate_serial()
        today = datetime.now(UTC).strftime("%Y%m%d")
        assert serial == f"{today}01"

    def test_increment_existing(self):
        today = datetime.now(UTC).strftime("%Y%m%d")
        serial = _generate_serial(f"{today}01")
        assert serial == f"{today}02"

    def test_increment_wraps_at_99(self):
        today = datetime.now(UTC).strftime("%Y%m%d")
        serial = _generate_serial(f"{today}99")
        assert serial == f"{today}99"  # capped at 99

    def test_new_day_resets(self):
        serial = _generate_serial("2025010199")
        today = datetime.now(UTC).strftime("%Y%m%d")
        assert serial == f"{today}01"

    def test_none_existing(self):
        serial = _generate_serial(None)
        today = datetime.now(UTC).strftime("%Y%m%d")
        assert serial == f"{today}01"


class TestReadExistingSerial:
    """Test reading serial from existing zone files."""

    def test_read_from_file(self, tmp_path):
        zone_file = tmp_path / "example.com.db"
        zone_file.write_text(
            "$ORIGIN example.com.\n"
            "@  IN  SOA  ns1.example.com. admin.example.com. (\n"
            "    2026030901  ; serial\n"
            ")\n"
        )
        assert _read_existing_serial(zone_file) == "2026030901"

    def test_no_file(self, tmp_path):
        zone_file = tmp_path / "nonexistent.db"
        assert _read_existing_serial(zone_file) is None

    def test_no_serial_in_file(self, tmp_path):
        zone_file = tmp_path / "example.com.db"
        zone_file.write_text("just some text\n")
        assert _read_existing_serial(zone_file) is None


class TestZoneGeneration:
    """Test zone file content generation."""

    def test_generate_basic_zone(self):
        records = [
            DiscoveredService(
                container_id="abc123",
                container_name="traefik",
                domain="traefik.example.com",
                target="10.0.0.2",
                record_type="A",
                ttl=300,
            ),
            DiscoveredService(
                container_id="def456",
                container_name="dolibarr-web",
                domain="erp.example.com",
                target="10.0.0.3",
                record_type="A",
                ttl=300,
            ),
        ]

        content = generate_zone_content(
            domain="example.com",
            records=records,
            default_ttl=300,
        )

        assert "$TTL 300" in content
        assert "$ORIGIN example.com." in content
        assert "SOA" in content
        assert "traefik" in content
        assert "10.0.0.2" in content
        assert "erp" in content
        assert "10.0.0.3" in content

    def test_generate_zone_root_record(self):
        records = [
            DiscoveredService(
                container_id="abc123",
                container_name="web",
                domain="example.com",
                target="10.0.0.2",
            ),
        ]

        content = generate_zone_content(
            domain="example.com",
            records=records,
        )

        assert "@" in content
        assert "10.0.0.2" in content

    def test_generate_cname_record(self):
        records = [
            DiscoveredService(
                container_id="abc123",
                container_name="alias",
                domain="alias.example.com",
                target="real.example.com",
                record_type="CNAME",
                ttl=600,
            ),
        ]

        content = generate_zone_content(
            domain="example.com",
            records=records,
            default_ttl=300,
        )

        assert "CNAME" in content
        assert "real.example.com." in content
        assert "600" in content  # custom TTL

    def test_custom_ttl_not_printed_when_default(self):
        records = [
            DiscoveredService(
                container_id="abc123",
                container_name="web",
                domain="web.example.com",
                target="10.0.0.2",
                ttl=300,
            ),
        ]

        content = generate_zone_content(
            domain="example.com",
            records=records,
            default_ttl=300,
        )

        # The record line should NOT have an explicit TTL
        for line in content.split("\n"):
            if "10.0.0.2" in line:
                assert "300" not in line.split("IN")[0]

    def test_sequential_serial_with_existing(self):
        today = datetime.now(UTC).strftime("%Y%m%d")
        content = generate_zone_content(
            domain="example.com",
            records=[],
            existing_serial=f"{today}01",
        )
        assert f"{today}02" in content


class TestWriteZoneFile:
    """Test zone file writing."""

    def test_write_new_zone(self, tmp_path):
        content = "$TTL 300\ntest record\n"
        path = write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        assert path.exists()
        assert path.read_text() == content
        assert path.name == "example.com.db"

    def test_no_rewrite_if_unchanged(self, tmp_path):
        content = "$TTL 300\ntest record\n"
        path = write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        mtime1 = path.stat().st_mtime

        # Tiny sleep to ensure mtime would differ
        time.sleep(0.01)

        write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        mtime2 = path.stat().st_mtime

        assert mtime1 == mtime2

    def test_creates_zone_dir(self, tmp_path):
        zone_dir = str(tmp_path / "new" / "zones")
        content = "test\n"
        path = write_zone_file(
            zone_dir=zone_dir,
            domain="example.com",
            content=content,
        )
        assert path.exists()


class TestCleanupStaleZones:
    """Test stale zone file removal."""

    def test_remove_stale(self, tmp_path):
        # Create zone files
        (tmp_path / "active.com.db").write_text("zone data")
        (tmp_path / "stale.com.db").write_text("old zone data")

        removed = cleanup_stale_zones(
            zone_dir=str(tmp_path),
            active_domains={"active.com"},
        )

        assert len(removed) == 1
        assert removed[0].name == "stale.com.db"
        assert not (tmp_path / "stale.com.db").exists()
        assert (tmp_path / "active.com.db").exists()

    def test_no_stale(self, tmp_path):
        (tmp_path / "active.com.db").write_text("zone data")

        removed = cleanup_stale_zones(
            zone_dir=str(tmp_path),
            active_domains={"active.com"},
        )

        assert len(removed) == 0

    def test_empty_dir(self, tmp_path):
        removed = cleanup_stale_zones(
            zone_dir=str(tmp_path),
            active_domains=set(),
        )
        assert len(removed) == 0

    def test_nonexistent_dir(self):
        removed = cleanup_stale_zones(
            zone_dir="/nonexistent/path",
            active_domains=set(),
        )
        assert len(removed) == 0

    def test_ignores_non_db_files(self, tmp_path):
        (tmp_path / "notes.txt").write_text("not a zone")
        (tmp_path / "stale.com.db").write_text("old zone")

        removed = cleanup_stale_zones(
            zone_dir=str(tmp_path),
            active_domains=set(),
        )

        # Only .db files should be cleaned
        assert len(removed) == 1
        assert (tmp_path / "notes.txt").exists()
