# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

"""Tests for DNSZoner health server."""

import asyncio
import json

from dnszoner.health import start_health_server


class TestHealthServer:
    """Test the async health HTTP server."""

    async def test_health_endpoint(self):
        status = {"services_count": 0}
        server = await start_health_server("127.0.0.1", 0, status)
        port = server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET /health HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        data = await asyncio.wait_for(reader.read(4096), timeout=5)
        response = data.decode()

        assert "200 OK" in response
        body = response.split("\r\n\r\n", 1)[1]
        parsed = json.loads(body)
        assert parsed["status"] == "ok"

        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()

    async def test_status_endpoint(self):
        status = {"services_count": 3, "zones_count": 1}
        server = await start_health_server("127.0.0.1", 0, status)
        port = server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET /status HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        data = await asyncio.wait_for(reader.read(4096), timeout=5)
        response = data.decode()

        assert "200 OK" in response
        body = response.split("\r\n\r\n", 1)[1]
        parsed = json.loads(body)
        assert parsed["services_count"] == 3

        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()

    async def test_404_endpoint(self):
        status = {}
        server = await start_health_server("127.0.0.1", 0, status)
        port = server.sockets[0].getsockname()[1]

        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        writer.write(b"GET /unknown HTTP/1.1\r\nHost: localhost\r\n\r\n")
        await writer.drain()

        data = await asyncio.wait_for(reader.read(4096), timeout=5)
        response = data.decode()

        assert "404 Not Found" in response

        writer.close()
        await writer.wait_closed()
        server.close()
        await server.wait_closed()
