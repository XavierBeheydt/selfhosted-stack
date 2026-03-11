# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Tests for DNSZoner CLI argument parser."""

import pytest

from dnszoner.cli import cli_parser


class TestCLIParser:
    """Test CLI argument parsing."""

    def test_no_args(self):
        args = cli_parser([])
        assert args.host is None
        assert args.port is None
        assert args.verbose is False

    def test_verbose(self):
        args = cli_parser(["-v"])
        assert args.verbose is True

    def test_verbose_long(self):
        args = cli_parser(["--verbose"])
        assert args.verbose is True

    def test_host(self):
        args = cli_parser(["-H", "127.0.0.1"])
        assert args.host == "127.0.0.1"

    def test_host_long(self):
        args = cli_parser(["--host", "0.0.0.0"])
        assert args.host == "0.0.0.0"

    def test_port(self):
        args = cli_parser(["-p", "9090"])
        assert args.port == 9090

    def test_port_long(self):
        args = cli_parser(["--port", "3000"])
        assert args.port == 3000

    def test_refresh_interval(self):
        args = cli_parser(["-i", "30"])
        assert args.refresh_interval == 30

    def test_base_domain(self):
        args = cli_parser(["-d", "example.com"])
        assert args.base_domain == "example.com"

    def test_zone_dir(self):
        args = cli_parser(["-z", "/tmp/zones"])
        assert args.zone_dir == "/tmp/zones"

    def test_container_engine_socket(self):
        args = cli_parser(["-s", "http://localhost:2375"])
        assert args.container_engine_socket == "http://localhost:2375"

    def test_label_prefix(self):
        args = cli_parser(["--label-prefix", "myprefix"])
        assert args.label_prefix == "myprefix"

    def test_default_ttl(self):
        args = cli_parser(["--default-ttl", "600"])
        assert args.default_ttl == 600

    def test_version(self, capsys):
        with pytest.raises(SystemExit) as exc:
            cli_parser(["--version"])
        assert exc.value.code == 0
        captured = capsys.readouterr()
        assert "0.3.0" in captured.out

    def test_combined_args(self):
        args = cli_parser(
            [
                "-H",
                "127.0.0.1",
                "-p",
                "9090",
                "-d",
                "test.local",
                "-i",
                "10",
                "-v",
                "--label-prefix",
                "custom",
                "--default-ttl",
                "600",
            ]
        )
        assert args.host == "127.0.0.1"
        assert args.port == 9090
        assert args.base_domain == "test.local"
        assert args.refresh_interval == 10
        assert args.verbose is True
        assert args.label_prefix == "custom"
        assert args.default_ttl == 600

    def test_all_defaults_none(self):
        """All optional args default to None (not zero-values)."""
        args = cli_parser([])
        assert args.container_engine_socket is None
        assert args.host is None
        assert args.port is None
        assert args.refresh_interval is None
        assert args.base_domain is None
        assert args.zone_dir is None
        assert args.label_prefix is None
        assert args.default_ttl is None
