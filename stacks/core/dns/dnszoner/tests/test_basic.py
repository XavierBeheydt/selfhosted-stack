# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""Basic smoke tests for dnszoner package."""

from dnszoner import __version__


def test_version():
    assert __version__ == "0.3.0"


def test_import_main():
    from dnszoner.main import main

    assert callable(main)


def test_import_discovery():
    from dnszoner.discovery import DiscoveryClient

    assert DiscoveryClient is not None


def test_import_zone():
    from dnszoner.zone import generate_zone_content, write_zone_file

    assert callable(generate_zone_content)
    assert callable(write_zone_file)


def test_import_health():
    from dnszoner.health import start_health_server

    assert callable(start_health_server)


def test_import_config():
    from dnszoner.config import DNSZonerConfig

    assert DNSZonerConfig is not None


def test_import_cli():
    from dnszoner.cli import cli_parser

    assert callable(cli_parser)
