# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner container discovery."""

from unittest.mock import MagicMock, patch

from dnszoner.discovery import (
    _get_container_ip,
    _socket_path_from_uri,
    discover_services,
)


class TestSocketPath:
    """Test socket URI conversion."""

    def test_convert_unix_socket(self):
        uri = "http+unix:///var/run/container_engine.sock"
        result = _socket_path_from_uri(uri)
        assert result == ("http+unix://%2Fvar%2Frun%2Fcontainer_engine.sock")

    def test_passthrough_other_uri(self):
        uri = "http://localhost:2375"
        assert _socket_path_from_uri(uri) == uri


class TestGetContainerIP:
    """Test IP extraction from network settings."""

    def test_extract_ip_from_network(self):
        networks = {
            "proxy-frontend": {"IPAddress": "10.0.0.5"},
            "backend": {"IPAddress": "172.17.0.2"},
        }
        assert _get_container_ip(networks) == "10.0.0.5"

    def test_preferred_network(self):
        networks = {
            "proxy-frontend": {"IPAddress": "10.0.0.5"},
            "backend": {"IPAddress": "172.17.0.2"},
        }
        assert _get_container_ip(networks, "backend") == "172.17.0.2"

    def test_empty_networks(self):
        assert _get_container_ip({}) is None
        assert _get_container_ip(None) is None

    def test_no_ip(self):
        networks = {"bridge": {"IPAddress": ""}}
        assert _get_container_ip(networks) is None


class TestDiscoverServices:
    """Test service discovery from container API."""

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
                    "Networks": {"proxy-frontend": {"IPAddress": "10.0.0.2"}}
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

        services = discover_services(
            socket_uri="http+unix:///var/run/test.sock"
        )

        assert len(services) == 1
        assert services[0].domain == "traefik.example.com"
        assert services[0].ip_address == "10.0.0.2"
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
                    # Missing dnszoner.domain
                },
                "NetworkSettings": {
                    "Networks": {"bridge": {"IPAddress": "10.0.0.2"}}
                },
            },
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_session.get.return_value = mock_resp

        services = discover_services(
            socket_uri="http+unix:///var/run/test.sock"
        )
        assert len(services) == 0

    @patch("dnszoner.discovery.requests_unixsocket.Session")
    def test_api_failure_returns_empty(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.get.side_effect = ConnectionError("refused")

        services = discover_services(
            socket_uri="http+unix:///var/run/test.sock"
        )
        assert services == []
