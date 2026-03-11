# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner container discovery."""

from unittest.mock import MagicMock, patch

import pytest

from dnszoner.discovery import (
    DiscoveredService,
    DiscoveryClient,
    _get_container_ip,
    _is_valid_hostname,
)


class TestHostnameValidation:
    """Test hostname validation regex."""

    def test_valid_simple(self):
        assert _is_valid_hostname("traefik.example.com")

    def test_valid_short(self):
        assert _is_valid_hostname("a")

    def test_valid_with_hyphen(self):
        assert _is_valid_hostname("my-service.example.com")

    def test_invalid_starts_with_hyphen(self):
        assert not _is_valid_hostname("-bad.example.com")

    def test_invalid_ends_with_hyphen(self):
        assert not _is_valid_hostname("bad-.example.com")

    def test_invalid_empty(self):
        assert not _is_valid_hostname("")

    def test_invalid_space(self):
        assert not _is_valid_hostname("has space.com")

    def test_invalid_underscore(self):
        assert not _is_valid_hostname("has_underscore.com")


class TestDiscoveredService:
    """Test DiscoveredService dataclass."""

    def test_create_a_record(self):
        svc = DiscoveredService(
            container_id="abc123",
            container_name="web",
            domain="web.example.com",
            target="10.0.0.2",
            record_type="A",
            ttl=300,
        )
        assert svc.record_type == "A"
        assert svc.target == "10.0.0.2"

    def test_create_cname_record(self):
        svc = DiscoveredService(
            container_id="abc123",
            container_name="web",
            domain="web.example.com",
            target="other.example.com",
            record_type="CNAME",
            ttl=600,
        )
        assert svc.record_type == "CNAME"
        assert svc.target == "other.example.com"

    def test_invalid_record_type(self):
        with pytest.raises(ValueError, match="Unsupported record type"):
            DiscoveredService(
                container_id="abc123",
                container_name="web",
                domain="web.example.com",
                target="10.0.0.2",
                record_type="MX",
            )

    def test_default_record_type(self):
        svc = DiscoveredService(
            container_id="abc123",
            container_name="web",
            domain="web.example.com",
            target="10.0.0.2",
        )
        assert svc.record_type == "A"
        assert svc.ttl == 300


class TestGetContainerIP:
    """Test IP extraction from network settings."""

    def test_extract_ip_from_network(self):
        networks = {
            "proxy": {"IPAddress": "10.0.0.5"},
            "backend": {"IPAddress": "172.17.0.2"},
        }
        assert _get_container_ip(networks) == "10.0.0.5"

    def test_preferred_network(self):
        networks = {
            "proxy": {"IPAddress": "10.0.0.5"},
            "backend": {"IPAddress": "172.17.0.2"},
        }
        assert _get_container_ip(networks, "backend") == "172.17.0.2"

    def test_empty_networks(self):
        assert _get_container_ip({}) is None
        assert _get_container_ip(None) is None

    def test_no_ip(self):
        networks = {"bridge": {"IPAddress": ""}}
        assert _get_container_ip(networks) is None


class TestDiscoveryClient:
    """Test DiscoveryClient session management and discovery."""

    def test_context_manager(self):
        with DiscoveryClient(socket_uri="http://localhost:2375") as client:
            assert client._session is not None
        # After exiting, session should be closed (no error)

    def test_close(self):
        client = DiscoveryClient(socket_uri="http://localhost:2375")
        assert client._session is not None
        client.close()
        # Should not raise

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_discover_labeled_containers(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/traefik"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "traefik.example.com",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.2"}}
                },
            },
            {
                "Id": "xyz789abc123456",
                "Names": ["/nginx"],
                "Labels": {
                    "some.other.label": "value",
                },
                "NetworkSettings": {
                    "Networks": {"bridge": {"IPAddress": "172.17.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()

        assert len(services) == 1
        assert services[0].domain == "traefik.example.com"
        assert services[0].target == "10.0.0.2"
        assert services[0].container_name == "traefik"

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_skip_container_without_domain(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/broken"],
                "Labels": {
                    "dnszoner.enable": "true",
                },
                "NetworkSettings": {
                    "Networks": {"bridge": {"IPAddress": "10.0.0.2"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()
        assert len(services) == 0

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_api_failure_returns_empty(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.get.side_effect = ConnectionError("refused")

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()
        assert services == []

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_safe_ttl_parsing_invalid(self, mock_session_cls):
        """Invalid TTL falls back to default instead of crashing."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/myapp"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "myapp.example.com",
                    "dnszoner.ttl": "not-a-number",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(
            socket_uri="http+unix:///var/run/test.sock",
            default_ttl=300,
        )
        services = client.discover()

        assert len(services) == 1
        assert services[0].ttl == 300  # fell back to default

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_safe_ttl_parsing_negative(self, mock_session_cls):
        """Negative TTL falls back to default."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/myapp"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "myapp.example.com",
                    "dnszoner.ttl": "-5",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(
            socket_uri="http+unix:///var/run/test.sock",
            default_ttl=300,
        )
        services = client.discover()

        assert len(services) == 1
        assert services[0].ttl == 300

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_cname_record_with_target_label(self, mock_session_cls):
        """CNAME records use dnszoner.target label."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/alias"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "alias.example.com",
                    "dnszoner.type": "CNAME",
                    "dnszoner.target": "real.example.com",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()

        assert len(services) == 1
        assert services[0].record_type == "CNAME"
        assert services[0].target == "real.example.com"

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_invalid_record_type_skipped(self, mock_session_cls):
        """Unsupported record types are skipped."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/mail"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "mail.example.com",
                    "dnszoner.type": "MX",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()
        assert len(services) == 0

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_invalid_hostname_skipped(self, mock_session_cls):
        """Invalid hostnames are skipped."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/bad"],
                "Labels": {
                    "dnszoner.enable": "true",
                    "dnszoner.domain": "-invalid.example.com",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(socket_uri="http+unix:///var/run/test.sock")
        services = client.discover()
        assert len(services) == 0

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_custom_label_prefix(self, mock_session_cls):
        """Custom label prefix is used for discovery."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "Id": "abc123def456789",
                "Names": ["/web"],
                "Labels": {
                    "myprefix.enable": "true",
                    "myprefix.domain": "web.example.com",
                },
                "NetworkSettings": {
                    "Networks": {"proxy": {"IPAddress": "10.0.0.5"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        client = DiscoveryClient(
            socket_uri="http+unix:///var/run/test.sock",
            label_prefix="myprefix",
        )
        services = client.discover()

        assert len(services) == 1
        assert services[0].domain == "web.example.com"
