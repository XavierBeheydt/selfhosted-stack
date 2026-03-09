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
| [traefik](stacks/core/traefik/) | Reverse proxy, TLS termination, routing | Gateway |
| [dns](stacks/core/dns/) | CoreDNS + DNSZoner sidecar (dynamic DNS, DNSSEC, DoT) | Gateway |
| [wireguard](stacks/core/wireguard/) | WireGuard VPN gateway (wg-easy), hub-spoke topology | Gateway |
| [authentik](stacks/core/authentik/) | SSO/OIDC identity provider, user management | Gateway |
| [monitoring](stacks/core/monitoring/) | Uptime Kuma status monitoring | Gateway |

### Business Services

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [dolibarr](stacks/business/dolibarr/) | ERP/CRM + MariaDB | Gateway |
| [n8n](stacks/business/n8n/) | Workflow automation + PostgreSQL | Gateway |
| [postiz](stacks/business/postiz/) | AI social media management | Gateway |

### AI Tools

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [litellm](stacks/ai/litellm/) | API router/aggregator (OpenRouter, Copilot, local) | Gateway |
| [open-webui](stacks/ai/open-webui/) | LLM chat UI with RAG, MCP tools, per-user memory | Gateway |
| [mem0](stacks/ai/mem0/) | Persistent AI memory per user (pgvector) | Gateway |
| [ollama](stacks/ai/ollama/) | LLM inference (GPU) | Compute |
| [openclaw](stacks/ai/openclaw/) | Personal AI coding agent | Gateway |
| [tts](stacks/ai/tts/) | Text-to-speech service | TBD |
| [stt](stacks/ai/stt/) | Speech-to-text service | TBD |

### Search

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [meilisearch](stacks/search/meilisearch/) | Federated internal search (Dolibarr, Seafile, photos) | Gateway |
| [searxng](stacks/search/searxng/) | Privacy-first meta search engine | Gateway |

### Storage

| Stack | Description | Node |
| :---- | :---------- | :--- |
| [seafile](stacks/storage/seafile/) | Cloud file storage (Google Drive alternative) | Gateway |
| [immich](stacks/storage/immich/) | Photo management with ML (Google Photos alt.) | Test |
| [photoprism](stacks/storage/photoprism/) | Photo management with AI (Google Photos alt.) | Test |

> **Immich vs PhotoPrism**: Both are set up for local A/B testing before final selection.

## Architecture

```
                        Internet
                           |
              +------------+------------+
              |      Gateway Node       |
              |   WireGuard Hub + DNS   |
              |   Traefik (proxy)       |
              |   Authentik (SSO)       |
              |   Dolibarr, n8n, Postiz |
              |   Seafile, SearXNG      |
              |   Meilisearch           |
              |   Uptime Kuma           |
              |   LiteLLM, Open WebUI   |
              |   mem0, OpenClaw        |
              +---+-----------------+---+
                  |                 |
           WireGuard VPN     WireGuard VPN
                  |                 |
    +-------------+---+    +-------+-----------+
    |  Compute Node   |    |  Client Devices   |
    |  GPU workloads  |    |  laptops, phones  |
    |                 |    +-------------------+
    |  Ollama (LLM)   |
    |  TTS / STT      |
    |  Immich (test)   |
    |  PhotoPrism (test)|
    +-----------------+
```

See [AGENTS.md](AGENTS.md) for detailed architecture, networking, and node
assignments.

## Requirements

- [Podman](https://podman.io/) (or Docker) with compose plugin
- [just](https://github.com/casey/just) task runner
- WireGuard for inter-node connectivity

## License

[MIT](LICENSE) -- Xavier Beheydt
