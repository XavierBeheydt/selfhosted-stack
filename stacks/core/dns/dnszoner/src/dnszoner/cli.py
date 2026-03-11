"""CLI argument parser for dnszoner."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from dnszoner import __version__


def cli_parser(args: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Parameters
    ----------
    args:
        Argument list to parse.  Defaults to ``sys.argv[1:]`` when *None*.
    """
    parser = argparse.ArgumentParser(
        prog="dnszoner",
        description="Dynamic DNS zone generator for container environments",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "-s",
        "--container-engine-socket",
        default=None,
        help="Container engine socket URI",
    )
    parser.add_argument(
        "-H",
        "--host",
        default=None,
        help="Health server bind address",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="Health server port",
    )
    parser.add_argument(
        "-i",
        "--refresh-interval",
        type=int,
        default=None,
        help="Discovery poll interval in seconds",
    )
    parser.add_argument(
        "-d",
        "--base-domain",
        default=None,
        help="Base domain for zone grouping",
    )
    parser.add_argument(
        "-z",
        "--zone-dir",
        default=None,
        help="Directory to write zone files",
    )
    parser.add_argument(
        "--label-prefix",
        default=None,
        help="Container label prefix (default: dnszoner)",
    )
    parser.add_argument(
        "--default-ttl",
        type=int,
        default=None,
        help="Default record TTL in seconds",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args(args)
