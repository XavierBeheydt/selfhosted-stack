# DNSZoner

Dynamic DNS zone generator for container environments. Discovers services via container labels and generates [CoreDNS](https://coredns.io/) zone files.

## How it works

DNSZoner polls the container engine API (Podman or Docker) on a configurable interval, discovers running containers with `dnszoner.*` labels, and writes RFC 1035 zone files that CoreDNS can serve.

```
Container Engine API  -->  DNSZoner  -->  Zone files  -->  CoreDNS
```

## Container labels

| Label | Required | Default | Description |
|---|---|---|---|
| `dnszoner.enable` | Yes | — | Set to `true` to register the container |
| `dnszoner.domain` | Yes | — | FQDN for the DNS record |
| `dnszoner.type` | No | `A` | Record type: `A` or `CNAME` |
| `dnszoner.ttl` | No | `300` | TTL in seconds |
| `dnszoner.target` | No | — | CNAME target (only for `CNAME` records) |
| `dnszoner.network` | No | — | Preferred container network for IP resolution |

## Configuration

Configuration is loaded from environment variables with sensible defaults. CLI flags override environment variables.

| Env variable | CLI flag | Default | Description |
|---|---|---|---|
| `CONTAINER_ENGINE_SOCKET` | `-s` | `http+unix:///var/run/container_engine.sock` | Container engine socket URI |
| `DNSZONER_HOST` | `-H` | `0.0.0.0` | Health server bind address |
| `DNSZONER_PORT` | `-p` | `8080` | Health server port |
| `DNSZONER_REFRESH_INTERVAL` | `-i` | `5` | Discovery poll interval (seconds) |
| `DNSZONER_BASE_DOMAIN` | `-d` | `localhost` | Base domain for zone grouping |
| `DNSZONER_ZONE_DIR` | `-z` | `/etc/coredns/zones` | Directory to write zone files |
| `DNSZONER_LABEL_PREFIX` | `--label-prefix` | `dnszoner` | Container label prefix |
| `DNSZONER_DEFAULT_TTL` | `--default-ttl` | `300` | Default record TTL |

## Health endpoints

| Endpoint | Description |
|---|---|
| `GET /health` | Returns `{"status": "ok"}` |
| `GET /status` | Returns current discovery state (services, zones, last refresh) |

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```sh
# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linter
uv run ruff check src/ tests/

# Run formatter
uv run ruff format src/ tests/
```

## Container build

```sh
podman build -t dnszoner:latest -f Containerfile .
```

## License

Copyright (c) 2026 Xavier Beheydt. All Rights Reserved.
