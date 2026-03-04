# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""Tests for DNSZoner zone generation."""

from dnszoner.discovery import DiscoveredService
from dnszoner.zone import generate_zone_content, write_zone_file


class TestZoneGeneration:
    """Test zone file content generation."""

    def test_generate_basic_zone(self):
        records = [
            DiscoveredService(
                container_id="abc123",
                container_name="traefik",
                domain="traefik.example.com",
                ip_address="10.0.0.2",
                record_type="A",
                ttl=300,
            ),
            DiscoveredService(
                container_id="def456",
                container_name="dolibarr-web",
                domain="erp.example.com",
                ip_address="10.0.0.3",
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
                ip_address="10.0.0.2",
            ),
        ]

        content = generate_zone_content(
            domain="example.com",
            records=records,
        )

        assert "@" in content
        assert "10.0.0.2" in content

    def test_write_zone_file(self, tmp_path):
        content = "$TTL 300\ntest record\n"
        path = write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        assert path.exists()
        assert path.read_text() == content
        assert path.name == "example.com.db"

    def test_write_zone_file_no_rewrite_if_unchanged(self, tmp_path):
        content = "$TTL 300\ntest record\n"
        path = write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        mtime1 = path.stat().st_mtime

        # Write same content again
        write_zone_file(
            zone_dir=str(tmp_path),
            domain="example.com",
            content=content,
        )
        mtime2 = path.stat().st_mtime

        assert mtime1 == mtime2
