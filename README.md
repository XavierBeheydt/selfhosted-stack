# Self-Hosted Stack

[![CI](https://github.com/XavierBeheydt/selfhosted-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/XavierBeheydt/selfhosted-stack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Modular, self-hosted infrastructure stack for small businesses. Compose-based
(Podman default, Docker compatible), deployed across nodes over WireGuard VPN.

## Quick Start

```bash
# Copy and edit global config
cp .env.example .env

# Start core infrastructure
just up-core

# Start a specific stack
just up traefik
```

## Stacks

### Core Infrastructure

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [traefik](stacks/core/traefik/) | Reverse proxy, TLS termination, routing | VPS |
| [dns](stacks/core/dns/) | CoreDNS + DNSZoner sidecar (dynamic DNS, DNSSEC, DoT) | VPS |
| [wireguard](stacks/core/wireguard/) | WireGuard VPN gateway (wg-easy), hub-spoke topology | VPS |
| [authentik](stacks/core/authentik/) | SSO/OIDC identity provider, user management | VPS |
| [monitoring](stacks/core/monitoring/) | Uptime Kuma status monitoring | VPS |

### Business Services

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [dolibarr](stacks/business/dolibarr/) | ERP/CRM + MariaDB | VPS |
| [n8n](stacks/business/n8n/) | Workflow automation + PostgreSQL | VPS |
| [postiz](stacks/business/postiz/) | AI social media management | VPS |

### AI Tools

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [litellm](stacks/ai/litellm/) | API router/aggregator (OpenRouter, Copilot, local) | VPS |
| [open-webui](stacks/ai/open-webui/) | LLM chat UI with RAG, MCP tools, per-user memory | VPS |
| [mem0](stacks/ai/mem0/) | Persistent AI memory per user (pgvector) | VPS |
| [ollama](stacks/ai/ollama/) | LLM inference (GPU: RTX 4090) | Local |
| [openclaw](stacks/ai/openclaw/) | Personal AI coding agent | VPS |
| [tts](stacks/ai/tts/) | Text-to-speech service | TBD |
| [stt](stacks/ai/stt/) | Speech-to-text service | TBD |

### Search

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [meilisearch](stacks/search/meilisearch/) | Federated internal search (Dolibarr, Seafile, photos) | VPS |
| [searxng](stacks/search/searxng/) | Privacy-first meta search engine | VPS |

### Storage

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [seafile](stacks/storage/seafile/) | Cloud file storage (Google Drive alternative) | VPS |
| [immich](stacks/storage/immich/) | Photo management with ML (Google Photos alt.) | Test |
| [photoprism](stacks/storage/photoprism/) | Photo management with AI (Google Photos alt.) | Test |

> **Immich vs PhotoPrism**: Both are set up for local A/B testing before final selection.

## Architecture

```
                    Internet
                       |
                   [VPS Node]
              WireGuard Hub + Traefik
              CoreDNS + Authentik (SSO)
            Dolibarr, n8n, Postiz, Seafile
          Meilisearch, SearXNG, Uptime Kuma
          LiteLLM (API router), Open WebUI
           mem0, OpenClaw, Monitoring
                       |
                  WireGuard VPN
                       |
                 [Local PC Node]
              RTX 4090 GPU workloads
             Ollama (LLM inference)
           Immich/PhotoPrism (testing)
              TTS/STT (if GPU needed)
                       |
                  WireGuard VPN
                       |
                 [Client Devices]
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Requirements

- [Podman](https://podman.io/) (or Docker) with compose plugin
- [just](https://github.com/casey/just) task runner
- WireGuard for inter-node connectivity

## License

[MIT](LICENSE) -- Xavier Beheydt
