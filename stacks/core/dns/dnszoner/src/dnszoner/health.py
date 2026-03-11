"""Async HTTP health/status server (lightweight, no framework)."""

from __future__ import annotations

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
    """Handle a single HTTP request on the health server."""
    try:
        data = await asyncio.wait_for(
            reader.readuntil(b"\r\n\r\n"), timeout=5.0
        )
    except (TimeoutError, asyncio.IncompleteReadError):
        writer.close()
        await writer.wait_closed()
        return

    request_line = data.split(b"\r\n")[0].decode("ascii", errors="replace")
    parts = request_line.split()
    path = parts[1] if len(parts) >= 2 else "/"

    if path == "/health":
        body = json.dumps({"status": "ok"})
        status_code = 200
    elif path == "/status":
        body = json.dumps(status)
        status_code = 200
    else:
        body = json.dumps({"error": "not found"})
        status_code = 404

    status_text = {200: "OK", 404: "Not Found"}.get(status_code, "Unknown")
    body_bytes = body.encode("utf-8")
    response = (
        f"HTTP/1.1 {status_code} {status_text}\r\n"
        f"Content-Type: application/json\r\n"
        f"Content-Length: {len(body_bytes)}\r\n"
        f"Connection: close\r\n"
        f"\r\n"
    ).encode("ascii") + body_bytes

    writer.write(response)
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def start_health_server(
    host: str,
    port: int,
    status: dict[str, Any],
) -> asyncio.Server:
    """Start the health HTTP server.

    Returns the ``asyncio.Server`` instance.
    """

    async def handler(
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        await handle_request(reader, writer, status)

    server = await asyncio.start_server(handler, host, port)
    logger.info("Health server listening on %s:%d", host, port)
    return server
