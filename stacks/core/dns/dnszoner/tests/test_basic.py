# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""Basic smoke tests for dnszoner package."""

from dnszoner import __version__


def test_version():
    assert __version__ == "0.2.0"


def test_import_main():
    from dnszoner.main import main

    assert callable(main)


def test_import_discovery():
    from dnszoner.discovery import discover_services

    assert callable(discover_services)
