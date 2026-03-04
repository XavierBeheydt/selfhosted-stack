# selfhosted-stack

[![CI](https://github.com/XavierBeheydt/selfhosted-stack/actions/workflows/ci.yml/badge.svg)](https://github.com/XavierBeheydt/selfhosted-stack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Open-source infrastructure stack for small businesses. Self-hosted services
with Docker Compose and K3s, designed for multi-node deployment over WireGuard
VPN.

## Overview

A modular, production-ready collection of self-hosted services organized into
composable stacks. Each stack provides both **Docker Compose** files (for
single-node or development use) and **Kubernetes manifests** (for multi-node
K3s deployment).

### Architecture

```
┌─────────────────────────────────┐     ┌──────────────────────────────────┐
│  VPS (Ubuntu)                   │     │  Local PC (Archlinux + GPU)      │
│  K3s Server Node                │     │  K3s Agent Node                  │
│                                 │     │                                  │
│  ┌─────────┐  ┌──────────────┐  │     │  ┌───────────┐  ┌────────────┐   │
│  │ Traefik │  │ CoreDNS      │  │     │  │ Traefik   │  │ CoreDNS    │   │
│  │         │  │ + DNSZoner   │  │     │  │ (local)   │  │ (local)    │   │
│  └─────────┘  └──────────────┘  │     │  └───────────┘  └────────────┘   │
│  ┌─────────┐  ┌──────────────┐  │     │  ┌───────────┐  ┌────────────┐   │
│  │Dolibarr │  │ n8n          │  │     │  │ Open      │  │ Ollama     │   │
│  │+ MariaDB│  │ + Postgres   │  │     │  │ WebUI     │  │ (GPU)      │   │
│  └─────────┘  └──────────────┘  │     │  └───────────┘  └────────────┘   │
│  ┌─────────┐  ┌──────────────┐  │     │  ┌───────────┐  ┌────────────┐   │
│  │ Postiz  │  │ SearXNG      │  │     │  │ TTS/STT   │  │ SearXNG    │   │
│  │ (social)│  │ (search)     │  │     │  │ (GPU)     │  │ (optional) │   │
│  └─────────┘  └──────────────┘  │     │  └───────────┘  └────────────┘   │
│  ┌─────────┐  ┌──────────────┐  │     │                                  │
│  │ Seafile │  │ Immich       │  │     │  GPU services are accessible     │
│  │ (files) │  │ (photos)     │  │     │  locally without VPN hairpin     │
│  └─────────┘  └──────────────┘  │     │                                  │
│  ┌──────────────────────────┐   │     │                                  │
│  │ WireGuard VPN Gateway    │   │     │                                  │
│  │ (wg-easy for devices)    │   │     │                                  │
│  └──────────────────────────┘   │     │                                  │
└────────────────┬────────────────┘     └───────────────┬──────────────────┘
                 │                                      │
                 └────── WireGuard (K3s native) ────────┘
                         Flannel VXLAN over WG
```

### Network Layers

| Layer              | Purpose                                   | Technology                            |
| :----------------- | :---------------------------------------- | :------------------------------------ |
| **Cluster mesh**   | Pod-to-pod across nodes                   | K3s Flannel + WireGuard native        |
| **Device VPN**     | iPhone, laptop access to private services | wg-easy (standalone WireGuard)        |
| **Public gateway** | Future: expose selected services publicly | Traefik Ingress + DNS + Let's Encrypt |

## Stacks

### Core Infrastructure

| Stack                               | Description                                        | Compose | K8s |
| :---------------------------------- | :------------------------------------------------- | :-----: | :-: |
| [traefik](stacks/core/traefik/)     | Reverse proxy with auto-TLS and service discovery  |    x    |  x  |
| [dns](stacks/core/dns/)             | CoreDNS + DNSZoner for dynamic DNS zone management |    x    |  x  |
| [wireguard](stacks/core/wireguard/) | VPN gateway for device access (wg-easy)            |    x    |  x  |

### Business Services

| Stack                                 | Description                                       | Compose | K8s |
| :------------------------------------ | :------------------------------------------------ | :-----: | :-: |
| [dolibarr](stacks/business/dolibarr/) | ERP/CRM with MariaDB                              |    x    |  x  |
| [n8n](stacks/business/n8n/)           | Low-code workflow automation with Postgres        |    -    |  -  |
| [postiz](stacks/business/postiz/)     | AI-powered social media management (20+ channels) |    -    |  -  |

### AI & Machine Learning

| Stack                               | Description                                        | Compose | K8s |
| :---------------------------------- | :------------------------------------------------- | :-----: | :-: |
| [open-webui](stacks/ai/open-webui/) | LLM chat UI with RAG, MCP, per-user memory         |    -    |  -  |
| [openclaw](stacks/ai/openclaw/)     | Personal AI agent gateway (20+ messaging channels) |    -    |  -  |
| [ollama](stacks/ai/ollama/)         | Local LLM inference (GPU)                          |    -    |  -  |
| [tts](stacks/ai/tts/)               | Text-to-Speech: Piper (fast) + XTTS-v2 (quality)   |    -    |  -  |
| [stt](stacks/ai/stt/)               | Speech-to-Text: Faster-Whisper                     |    -    |  -  |

### Search & Storage

| Stack                              | Description                                            | Compose | K8s |
| :--------------------------------- | :----------------------------------------------------- | :-----: | :-: |
| [searxng](stacks/search/searxng/)  | Privacy-respecting meta search engine (70+ sources)    |    -    |  -  |
| [seafile](stacks/storage/seafile/) | Cloud file storage and sync (Google Drive alternative) |    -    |  -  |
| [immich](stacks/storage/immich/)   | Photo management with ML (Google Photos alternative)   |    -    |  -  |

> Stacks marked with `-` are planned for upcoming phases.

## Quick Start

### Prerequisites

- Docker or Podman (for compose-based deployment)
- [just](https://github.com/casey/just) command runner (optional but recommended)
- K3s (for multi-node deployment)

### Single-Node (Docker Compose)

```bash
# Clone the repository
git clone https://github.com/XavierBeheydt/selfhosted-stack.git
cd selfhosted-stack

# Copy and configure environment
cp .env.example .env
# Edit .env with your settings

# Start core infrastructure
just traefik-up
just dns-up

# Start business services
just dolibarr-up
```

### Multi-Node (K3s)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full K3s setup guide
covering:

- K3s server/agent installation with WireGuard backend
- GPU node labeling and NVIDIA device plugin
- Stack deployment with Kustomize overlays
- WireGuard VPN gateway for device access

## Stack Structure

Each stack follows a consistent layout:

```
stacks/<category>/<service>/
├── compose.yml          # Docker Compose for single-node / development
├── .env.example         # Service-specific environment variables
├── config/              # Configuration files
├── k8s/
│   ├── base/            # Base Kubernetes manifests
│   └── overlays/        # Kustomize overlays (vps/, local/)
└── README.md            # Service-specific documentation
```

## Development

```bash
# List all available commands
just --list

# Run all tests
just test

# Lint code
just lint

# Deploy to VPS
just deploy-vps
```

## Deployment

Deployment is handled via GitHub Actions:

- **CI** (`ci.yml`): Runs on every push/PR to `main`. Lints, tests, and
  validates all compose files.
- **CD** (`deploy.yml`): Auto-deploys to VPS on push to `main`. Supports
  manual dispatch for selective service deployment.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Alternatives

This stack uses opinionated defaults, but alternatives are documented in each
service README:

| Category      | Default    | Alternatives                                                                   |
| :------------ | :--------- | :----------------------------------------------------------------------------- |
| Automation    | n8n        | [Activepieces](https://www.activepieces.com/) (MIT license)                    |
| LLM Chat UI   | Open WebUI | [LibreChat](https://www.librechat.ai/) (MIT), [LobeChat](https://lobehub.com/) |
| AI Agent      | OpenClaw   | [Open WebUI](https://openwebui.com/) (chat-focused), [Jan](https://jan.ai/)    |
| Cloud Storage | Seafile    | [Nextcloud](https://nextcloud.com/) (full suite)                               |
| Photos        | Immich     | [Ente](https://ente.io/) (E2E encrypted)                                       |
| Orchestration | K3s        | Docker Swarm (simpler), Nomad                                                  |
| Reverse Proxy | Traefik    | [Caddy](https://caddyserver.com/)                                              |
| Social Media  | Postiz     | [Mixpost](https://mixpost.app/) (MIT Lite)                                     |

## Contributing

1. Keep secrets out of the repository -- use `.env` files
2. Every stack must include both `compose.yml` and K8s manifests
3. Document environment variables in `.env.example`
4. Test compose files with `docker compose config --quiet`

## License

[MIT](LICENSE) - Xavier Beheydt
