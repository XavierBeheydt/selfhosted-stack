# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner configuration."""

from dnszoner.config import DNSZonerConfig


class TestDNSZonerConfig:
    """Test DNSZonerConfig defaults and env override."""

    def test_defaults(self):
        config = DNSZonerConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.refresh_interval == 5
        assert config.label_prefix == "dnszoner"
        assert config.default_ttl == 300

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_HOST", "127.0.0.1")
        monkeypatch.setenv("DNSZONER_PORT", "9090")
        monkeypatch.setenv("DNSZONER_BASE_DOMAIN", "test.local")
        config = DNSZonerConfig()
        assert config.host == "127.0.0.1"
        assert config.port == 9090
        assert config.base_domain == "test.local"
