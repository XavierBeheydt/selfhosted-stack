# Architecture

## Overview

selfhosted-stack is a modular, multi-node infrastructure designed for small businesses. It runs across two machines connected via WireGuard:

- **VPS** (Ubuntu) — public-facing services, reverse proxy, DNS, VPN gateway, ERP
- **Local PC** (Archlinux + RTX 4090) — GPU workloads: LLM inference, TTS, STT, image processing

## Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                          Internet                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                    ┌──────┴──────┐
                    │   Traefik   │  :80 / :443
                    │  (reverse   │  Let's Encrypt TLS
                    │   proxy)    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
        ┌─────┴─────┐ ┌───┴────┐   ┌───────┴──────┐
        │  CoreDNS   │ │ wg-easy│   │   Dolibarr   │
        │ + DNSZoner │ │  (VPN) │   │  (ERP/CRM)   │
        └────────────┘ └───┬────┘   └──────────────┘
                           │
                    WireGuard tunnel
                    (51820/udp)
                           │
              ┌────────────┼────────────────┐
              │            │                │
        ┌─────┴─────┐ ┌───┴────┐   ┌───────┴──────┐
        │  Ollama    │ │Open    │   │   Immich /    │
        │  (GPU)     │ │WebUI   │   │   Seafile     │
        └────────────┘ └────────┘   └──────────────┘

        └───────── Local PC (RTX 4090) ─────────────┘
```

## Deployment Modes

### Docker Compose (single-node / development)

Each stack has a `compose.yml` for standalone operation. Stacks communicate via a shared `proxy-frontend` Docker network.

```bash
# Create shared network
docker network create proxy-frontend

# Start a stack
docker compose -f stacks/core/traefik/compose.yml up -d
```

### Kubernetes / K3s (multi-node / production)

Each stack has Kustomize manifests in `k8s/base/`. K3s uses WireGuard natively for inter-node communication (`--flannel-backend=wireguard-native`).

```bash
# Apply a stack
kubectl apply -k stacks/core/traefik/k8s/base/
```

## Stack Categories

### Core (`stacks/core/`)

| Stack     | Purpose                           | Port(s)         |
|-----------|-----------------------------------|-----------------|
| traefik   | Reverse proxy, TLS termination    | 80, 443         |
| dns       | CoreDNS + DNSZoner (zone gen)     | 53 TCP/UDP      |
| wireguard | VPN gateway for personal devices  | 51820 UDP       |

### Business (`stacks/business/`)

| Stack    | Purpose                          |
|----------|----------------------------------|
| dolibarr | ERP/CRM with MariaDB             |
| n8n      | Workflow automation (Phase 2)    |
| postiz   | Social media management (Phase 2)|

### AI (`stacks/ai/`)

| Stack     | Purpose                          | Node  |
|-----------|----------------------------------|-------|
| ollama    | LLM inference (GPU)              | local |
| open-webui| Chat UI with RAG, MCP, memory    | local |
| tts       | Piper (fast) + XTTS-v2 (clone)  | local |
| stt       | Faster-Whisper                   | local |

### Search (`stacks/search/`)

| Stack   | Purpose                          |
|---------|----------------------------------|
| searxng  | Meta search engine              |

### Storage (`stacks/storage/`)

| Stack   | Purpose                          |
|---------|----------------------------------|
| seafile  | Cloud file storage              |
| immich   | Photo/video management          |

## Container Engine Agnostic

The stack supports both Docker and Podman. The container engine is configurable:

- **justfile**: `CONTAINER_ENGINE=podman just up`
- **compose.yml**: Uses `CONTAINER_ENGINE_SOCKET` env var for socket path
- **CI/CD**: Auto-detects available engine on remote servers

## DNS Architecture

DNSZoner is a custom Python service that:

1. Connects to the Docker/Podman socket
2. Watches for containers with `dnszoner.enable=true` labels
3. Generates CoreDNS zone files from `dnszoner.domain=<fqdn>` labels
4. CoreDNS reloads zone files every 5 seconds

This provides automatic DNS resolution for all services without manual zone file management.

## GPU Routing Strategy

GPU services on the local PC are accessed without VPN hairpinning:

1. Services bind to `NodePort` or `HostPort` on the local machine
2. K3s `nodeSelector` pins GPU workloads to the local node
3. Split DNS resolves AI subdomains directly to the local PC's WireGuard IP
4. VPN clients route through WireGuard to reach the local PC

## Security Notes

- All secrets should use `.env` files (not committed) for Compose, and sealed-secrets / external-secrets / SOPS for Kubernetes
- TLS is handled by Traefik with Let's Encrypt (ACME)
- WireGuard provides encrypted inter-node and device-to-network communication
- Container engine sockets are mounted read-only where possible
- K8s manifests include resource limits and security contexts
