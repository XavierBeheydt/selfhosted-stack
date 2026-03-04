# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""
Command-line parser for DNSZoner.
"""

from argparse import ArgumentParser, Namespace


def cli_parser() -> Namespace:
    """Parse command-line arguments for DNS-Zoner."""
    parser = ArgumentParser(
        description=(
            "DNS-Zoner: Generate DNS zone files by detecting running "
            "containers via labels, similar to Traefik service discovery."
        )
    )
    parser.add_argument(
        "-s",
        "--container-engine-socket",
        type=str,
        default=None,
        help=("Container engine socket URL. (env: CONTAINER_ENGINE_SOCKET)"),
    )
    parser.add_argument(
        "-H",
        "--host",
        type=str,
        default=None,
        help="Host to bind health endpoint to. (env: DNSZONER_HOST)",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=None,
        help="Port for health endpoint. (env: DNSZONER_PORT)",
    )
    parser.add_argument(
        "-i",
        "--refresh-interval",
        type=int,
        default=None,
        help=(
            "Interval in seconds between zone refreshes. "
            "(env: DNSZONER_REFRESH_INTERVAL)"
        ),
    )
    parser.add_argument(
        "-d",
        "--base-domain",
        type=str,
        default=None,
        help="Base domain for DNS zones. (env: DNSZONER_BASE_DOMAIN)",
    )
    parser.add_argument(
        "-z",
        "--zone-dir",
        type=str,
        default=None,
        help=("Directory to write zone files. (env: DNSZONER_ZONE_DIR)"),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable debug logging.",
    )
    return parser.parse_args()
