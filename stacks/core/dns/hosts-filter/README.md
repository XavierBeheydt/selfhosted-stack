# Hosts Filter Service

Dynamic hosts file generator for DNS filtering. Downloads host files from StevenBlack/hosts repository and generates custom filtered versions based on source IP.

## How it works

The service provides an API to configure DNS filtering per source IP address. It downloads host files from various categories (gambling, fakenews, adware, etc.) and merges them into custom host files that CoreDNS can use for filtering.

```
API Request --> Hosts Filter --> Custom hosts files --> CoreDNS
```

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/configure` | POST | Configure filtering for a specific IP |
| `/health` | GET | Health check endpoint |

## Configuration

Configuration is loaded from environment variables:

| Env variable | Default | Description |
|---|---|---|
| `HOSTSFILTER_HOST` | `0.0.0.0` | API server bind address |
| `HOSTSFILTER_PORT` | `8000` | API server port |
| `HOSTSFILTER_DATA_DIR` | `/data` | Directory to store host files |

## Available Categories

- `gambling`: Gambling-related domains
- `fakenews`: Fake news domains
- `adware`: Adware and malware domains
- `social`: Social media domains
- `porn`: Adult content domains

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
podman build -t hosts-filter:latest -f Containerfile .
```

## License

Copyright (c) 2026 Xavier Beheydt. All Rights Reserved.