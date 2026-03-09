# AGENTS - AI Agent Instructions

- **Owner**: Xavier Beheydt
- **License**: MIT
- **Language**: English (all docs, comments, commit messages)
- **Repo**: [github.com/XavierBeheydt/selfhosted-stack](https://github.com/XavierBeheydt/selfhosted-stack)

## Project Summary

**selfhosted-stack** is a modular, open-source infrastructure stack for small
businesses. Self-hosted services packaged as **Compose files** (Podman by
default, Docker compatible) with deployment scripts for multi-node environments.
Nodes communicate securely over a **WireGuard** hub-spoke VPN, with **Traefik**
as reverse proxy and **CoreDNS** for dynamic service DNS.

## Architecture

Two physical nodes connected via WireGuard (hub-spoke, VPS as hub):

- **VPS** (Ubuntu) -- public-facing: Traefik, CoreDNS, WireGuard (wg-easy),
  Authentik, Dolibarr, n8n, Postiz, Seafile, SearXNG, Meilisearch, Uptime Kuma
- **Local PC** (Archlinux, RTX 4090) -- GPU workloads: Ollama, Open WebUI,
  LiteLLM, mem0, OpenClaw, TTS, STT, Immich/PhotoPrism (testing)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for network topology and
detailed deployment mapping.

## Key Files

| File | Purpose |
| :--- | :------ |
| [README.md](README.md) | Project overview and quickstart |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Network topology, node mapping, DNS |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phased plan with progress |
| [justfile](justfile) | Task runner recipes |
| [.env.example](.env.example) | Global environment template |
| [deploy/inventory.yml](deploy/inventory.yml) | Node inventory (VPS + local) |
| [deploy/deploy.sh](deploy/deploy.sh) | SSH-based deployment script |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | CI pipeline |
| [.github/workflows/deploy.yml](.github/workflows/deploy.yml) | CD pipeline |

## Stack Structure Convention

Every stack **must** follow this layout:

```
stacks/<category>/<service>/
├── compose.yml          # Compose file (podman/docker compatible)
├── .env.example         # Service-specific environment variables
├── config/              # Configuration files (mounted as volumes)
├── ContainerFile        # Custom image build (if needed, not Dockerfile)
└── README.md            # Service-specific documentation
```

Categories: `core/`, `business/`, `ai/`, `search/`, `storage/`.

## Naming Conventions

- `compose.yml` -- not `docker-compose.yml`
- `ContainerFile` -- not `Dockerfile` (engine-agnostic)
- `.containerignore` -- not `.dockerignore`
- Container engine socket referenced via `CONTAINER_ENGINE_SOCKET` env var

## Compose File Conventions

- Top-level `name:` key matching the service name
- `restart: unless-stopped` (not `always`)
- Include `healthcheck:` on every service
- `${VAR:-default}` for optional env vars, `${VAR:?error}` for required
- Join external `proxy` network for Traefik-exposed services
- Internal bridge network `<name>-internal` for inter-service communication
- Traefik labels: `traefik.enable=true`, `traefik.http.routers.<name>.rule=Host(...)`
- Explicit `container_name:` on every service
- Named volumes for persistent data

## Code Style & Conventions

- **YAML**: 2-space indent, no trailing whitespace
- **Python**: Ruff for lint/format, pytest for tests, uv for packages
- **Shell**: Must pass ShellCheck
- **No secrets in repo**: `.env` files (gitignored), `.env.example` for templates
- **Commits**: Conventional Commits (see table below)

| Prefix   | Purpose                                 |
| :------- | :-------------------------------------- |
| feat     | A new feature                           |
| fix      | A bug fix                               |
| docs     | Documentation changes                   |
| style    | Code formatting (no logic changes)      |
| refactor | Code restructuring without feature/fix  |
| perf     | Performance improvements                |
| test     | Adding or updating tests                |
| chore    | Maintenance tasks, dependencies         |
| ci       | CI/CD pipeline changes                  |
| build    | Build system or dependencies            |
| revert   | Reverting a previous commit             |

## Container Engine

Default engine is **Podman**. Override via env var:

```bash
CONTAINER_ENGINE=docker just <recipe>
```

## Important Context

- DNSZoner is a custom Python sidecar at `stacks/core/dns/dnszoner/`
- LiteLLM sits between all AI consumers and LLM providers as unified proxy
- mem0 provides persistent per-user memory across AI services
- OpenClaw is a personal AI coding agent (single instance, WireGuard access)
- Open WebUI is the team-facing LLM chat interface with RAG and MCP tools
- Authentik provides centralized SSO (OIDC/LDAP) for all user-facing services
- Meilisearch provides federated internal search (Dolibarr, Seafile, photos)
- SearXNG handles web meta-search only (privacy-first, not internal data)
- WireGuard uses hub-spoke topology (VPS as hub, all devices connect to VPS)
- System is entirely private -- accessible only via WireGuard
