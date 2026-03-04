# AGENTS.md — AI Agent Instructions

This file provides context for AI coding agents (OpenCode, Cursor, Windsurf,
Cline, Aider, etc.) working on the selfhosted-stack repository.

## Project Summary

**selfhosted-stack** is a modular, open-source infrastructure stack for small
businesses. Self-hosted services packaged as Docker Compose files AND Kubernetes
manifests, designed for multi-node deployment over WireGuard VPN.

- **Owner**: Xavier Beheydt
- **License**: MIT
- **Language**: English (all docs, comments, commit messages)
- **Repo**: https://github.com/XavierBeheydt/selfhosted-stack

## Architecture

Two physical nodes connected via WireGuard:

- **VPS** (Ubuntu) — public-facing: Traefik, CoreDNS, WireGuard gateway,
  Dolibarr, n8n, Postiz, Seafile
- **Local PC** (Archlinux + RTX 4090) — GPU workloads: Ollama, Open WebUI,
  TTS, STT, Immich ML

All AI consumers (Open WebUI, OpenClaw, n8n) route through **LiteLLM** (unified
API gateway) to reach Ollama or cloud LLM providers. **Mem0** provides shared
persistent memory across all AI services.

## Key Files

| File                       | Purpose                                     |
| :------------------------- | :------------------------------------------ |
| `docs/ARCHITECTURE.md`     | Network topology, deployment modes, DNS, GPU routing |
| `docs/ROADMAP.md`          | Phased plan with checkboxes — what's done and what's next |
| `justfile`                 | All task runner recipes (30+)               |
| `.env.example`             | Global environment template                 |
| `deploy/deploy.sh`         | SSH-based remote deployment script          |
| `.github/workflows/ci.yml` | CI pipeline: tests, compose lint, k8s lint, shellcheck |
| `shared/networks.yml`      | Shared Docker network definitions           |

## Stack Structure Convention

Every stack **must** follow this layout:

```
stacks/<category>/<service>/
├── compose.yml          # Docker Compose for single-node / development
├── .env.example         # Service-specific environment variables
├── config/              # Configuration files (mounted as volumes)
├── k8s/
│   ├── base/            # Base Kubernetes manifests (Kustomize)
│   └── overlays/        # Kustomize overlays (vps/, local/)
└── README.md            # Service-specific documentation
```

Categories: `core/`, `business/`, `ai/`, `search/`, `storage/`.

## Compose File Conventions

- Use `name:` top-level key matching the service name
- Use `restart: unless-stopped` (not `always`)
- Include `healthcheck:` on every service
- Use `${VAR:-default}` for optional env vars, `${VAR:?error}` for required ones
- Join the `proxy-frontend` external network for Traefik-exposed services
- Use an internal bridge network for inter-service communication (e.g. `<name>-internal`)
- Add Traefik labels: `traefik.enable=true`, `traefik.http.routers.<name>.rule=Host(...)`
- Add DNSZoner labels: `dnszoner.enable=true`, `dnszoner.domain=<fqdn>`
- Name containers explicitly with `container_name:`
- Use named volumes for persistent data

## Kubernetes Conventions

- Each stack gets its own namespace
- `k8s/base/kustomization.yml` lists all resources
- Secrets use `stringData:` with placeholder values (real secrets via sealed-secrets/SOPS)
- Deployments include `resources.requests` and `resources.limits`
- GPU workloads use `nodeSelector` to pin to the local node
- Services use Traefik IngressRoute CRD (not standard Ingress)
- PVCs use `ReadWriteOnce` access mode

## Container Engine

The stack is engine-agnostic — supports both Docker and Podman:

- `justfile`: `CONTAINER_ENGINE=podman just <recipe>`
- `compose.yml`: `CONTAINER_ENGINE_SOCKET` env var for socket path
- `deploy.sh`: auto-detects available engine on remote

## Code Style & Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `style:`, `docs:`, `chore:`)
- **YAML**: 2-space indent, no trailing whitespace
- **Markdown tables**: Format with `python3 scripts/format_md_tables.py --apply --exclude session-`
- **Python** (DNSZoner): Ruff for lint/format, pytest for tests, uv for package management
- **Shell**: Must pass ShellCheck
- **No secrets in repo**: Use `.env` files (gitignored), `.env.example` for templates

## CI Pipeline

Runs on every push/PR to `main`:

1. **DNSZoner tests** — Python 3.12 + 3.13, ruff lint, ruff format check, pytest
2. **Compose validation** — `docker compose config --quiet` for each stack
3. **K8s validation** — `kubectl kustomize` for each stack's k8s/base/
4. **ShellCheck** — all shell scripts

When adding a new stack, add corresponding validation steps to
`.github/workflows/ci.yml`.

## Verification Commands

```bash
# Run all tests
just test

# Lint all code
just lint

# Validate a compose file
docker compose -f stacks/<category>/<service>/compose.yml config --quiet

# Validate k8s manifests
kubectl kustomize stacks/<category>/<service>/k8s/base/

# Format markdown tables
python3 scripts/format_md_tables.py --apply --exclude session-
```

## Current Status

See `docs/ROADMAP.md` for the full phased plan. In brief:

- **Phase 1** (done): Traefik, CoreDNS/DNSZoner, WireGuard, Dolibarr, CI/CD, justfile
- **Phase 2** (next): n8n, Postiz
- **Phase 3** (planned): Ollama, Open WebUI, OpenClaw, SearXNG, TTS, STT, LiteLLM wiring, Mem0 k8s
- **Phase 4** (planned): Seafile, Immich
- **Phase 5** (planned): Full docs, badges, polish

## Important Context

- DNSZoner is a **custom Python project** (not third-party) at `stacks/core/dns/dnszoner/`
- OpenClaw and Open WebUI are **complementary** — OpenClaw is a personal agent
  in messaging apps, Open WebUI is a team web chat UI. Both connect to Ollama.
- LiteLLM sits between all AI consumers and all LLM providers as a unified proxy
- Mem0 provides persistent cross-service memory (pgvector + optional Neo4j)
- GPU services on the local PC are accessed via split DNS + nodeSelector
  (no VPN hairpinning)
- WireGuard has two layers: K3s native (`--flannel-backend=wireguard-native`)
  for cluster mesh, and wg-easy for personal device VPN access
- K3s WireGuard `WG_ALLOWED_IPS` must include pod CIDR `10.42.0.0/16` and
  service CIDR `10.43.0.0/16`
