# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner configuration."""

import pytest

from dnszoner.config import DNSZonerConfig


class TestDNSZonerConfigDefaults:
    """Test all default values are applied correctly."""

    def test_default_container_engine_socket(self):
        config = DNSZonerConfig()
        assert (
            config.container_engine_socket
            == "http+unix:///var/run/container_engine.sock"
        )

    def test_default_host(self):
        config = DNSZonerConfig()
        assert config.host == "0.0.0.0"

    def test_default_port(self):
        config = DNSZonerConfig()
        assert config.port == 8080

    def test_default_refresh_interval(self):
        config = DNSZonerConfig()
        assert config.refresh_interval == 5

    def test_default_zone_dir(self):
        config = DNSZonerConfig()
        assert config.zone_dir == "/etc/coredns/zones"

    def test_default_base_domain(self):
        config = DNSZonerConfig()
        assert config.base_domain == "localhost"

    def test_default_label_prefix(self):
        config = DNSZonerConfig()
        assert config.label_prefix == "dnszoner"

    def test_default_ttl(self):
        config = DNSZonerConfig()
        assert config.default_ttl == 300


class TestDNSZonerConfigEnvOverride:
    """Test environment variable overrides."""

    def test_override_host(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_HOST", "127.0.0.1")
        config = DNSZonerConfig()
        assert config.host == "127.0.0.1"

    def test_override_port(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_PORT", "9090")
        config = DNSZonerConfig()
        assert config.port == 9090

    def test_override_base_domain(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_BASE_DOMAIN", "test.local")
        config = DNSZonerConfig()
        assert config.base_domain == "test.local"

    def test_override_refresh_interval(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_REFRESH_INTERVAL", "30")
        config = DNSZonerConfig()
        assert config.refresh_interval == 30

    def test_override_zone_dir(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_ZONE_DIR", "/tmp/zones")
        config = DNSZonerConfig()
        assert config.zone_dir == "/tmp/zones"

    def test_override_label_prefix(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_LABEL_PREFIX", "myprefix")
        config = DNSZonerConfig()
        assert config.label_prefix == "myprefix"

    def test_override_default_ttl(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_DEFAULT_TTL", "600")
        config = DNSZonerConfig()
        assert config.default_ttl == 600

    def test_override_socket(self, monkeypatch):
        monkeypatch.setenv("CONTAINER_ENGINE_SOCKET", "http://localhost:2375")
        config = DNSZonerConfig()
        assert config.container_engine_socket == "http://localhost:2375"


class TestDNSZonerConfigExplicitValues:
    """Test explicit constructor arguments take priority."""

    def test_explicit_port(self):
        config = DNSZonerConfig(port=3000)
        assert config.port == 3000

    def test_explicit_base_domain(self):
        config = DNSZonerConfig(base_domain="example.com")
        assert config.base_domain == "example.com"


class TestDNSZonerConfigValidation:
    """Test __post_init__ validation errors."""

    def test_port_too_low(self):
        with pytest.raises(ValueError, match="port must be 1-65535"):
            DNSZonerConfig(port=-1)

    def test_port_too_high(self):
        with pytest.raises(ValueError, match="port must be 1-65535"):
            DNSZonerConfig(port=70000)

    def test_refresh_interval_zero(self):
        with pytest.raises(ValueError, match="refresh_interval must be >= 1"):
            DNSZonerConfig(refresh_interval=-1)

    def test_default_ttl_zero(self):
        with pytest.raises(ValueError, match="default_ttl must be >= 1"):
            DNSZonerConfig(default_ttl=-1)

    def test_empty_base_domain(self, monkeypatch):
        monkeypatch.setenv("DNSZONER_BASE_DOMAIN", "")
        # When env is explicitly empty, the sentinel check picks up ""
        # from os.getenv which is still empty — validation rejects it.
        with pytest.raises(ValueError, match="base_domain must not be empty"):
            DNSZonerConfig()
