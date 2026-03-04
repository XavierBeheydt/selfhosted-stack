# Copyright (c) 2026 Xavier Beheydt - All Rights Reserved

"""
Async HTTP health server for DNSZoner.

Provides /health and /status endpoints for health checks and monitoring.
"""

import asyncio
import json
import logging
from typing import Any

logger = logging.getLogger("dnszoner")


async def handle_request(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    status: dict[str, Any],
) -> None:
    """Handle incoming HTTP requests on the health endpoint."""
    try:
        try:
            raw = await asyncio.wait_for(
                reader.readuntil(b"\r\n\r\n"), timeout=5
            )
        except asyncio.IncompleteReadError as exc:
            raw = exc.partial
        except TimeoutError:
            writer.close()
            await writer.wait_closed()
            return

        first_line = raw.split(b"\r\n", 1)[0].decode("ascii", "ignore")
        parts = first_line.split()
        if len(parts) < 2:
            writer.close()
            await writer.wait_closed()
            return

        path = parts[1]

        if path == "/health":
            body = json.dumps({"status": "ok"})
            code = "200 OK"
        elif path == "/status":
            body = json.dumps(status, default=str)
            code = "200 OK"
        else:
            body = json.dumps({"error": "not found"})
            code = "404 Not Found"

        response = (
            f"HTTP/1.1 {code}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Connection: close\r\n"
            f"\r\n"
            f"{body}"
        )
        writer.write(response.encode())
        await writer.drain()

    except Exception:
        logger.exception("Error handling HTTP request")
    finally:
        writer.close()
        await writer.wait_closed()


async def start_health_server(
    host: str,
    port: int,
    status: dict[str, Any],
) -> asyncio.Server:
    """Start the async HTTP health server."""

    async def handler(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        await handle_request(reader, writer, status)

    server = await asyncio.start_server(handler, host, port)
    logger.info("Health server listening on %s:%d", host, port)
    return server
