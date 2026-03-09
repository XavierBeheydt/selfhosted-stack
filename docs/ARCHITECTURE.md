# Architecture

Network topology, node assignments, and design decisions for the
selfhosted-stack.

## Overview

Two physical nodes connected via WireGuard hub-spoke VPN. The VPS is the
public-facing entry point and WireGuard hub. The Local PC provides GPU
compute for LLM inference and heavy ML workloads. All services are
container-based (Podman/Docker Compose) with Traefik as the shared reverse
proxy.

## Network Topology

```
                ┌──────────────────────────────────┐
                │             Internet             │
                └────────────────┬─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      VPS (Ubuntu)       │
                    │   WireGuard Hub + DNS   │
                    │                         │
                    │  ┌───────────────────┐  │
                    │  │    Traefik        │  │
                    │  │  (reverse proxy)  │  │
                    │  └─────────┬─────────┘  │
                    │            │            │
                    │  ┌─────────┴─────────┐  │
                    │  │   proxy network   │  │
                    │  │                   │  │
                    │  │ Authentik (SSO)   │  │
                    │  │ Dolibarr (ERP)    │  │
                    │  │ n8n (automation)  │  │
                    │  │ Postiz (social)   │  │
                    │  │ Seafile (files)   │  │
                    │  │ SearXNG (search)  │  │
                    │  │ Meilisearch       │  │
                    │  │ Uptime Kuma       │  │
                    │  │ LiteLLM (API)     │  │
                    │  │ Open WebUI        │  │
                    │  │ mem0 (memory)     │  │
                    │  │ OpenClaw (agent)  │  │
                    │  └───────────────────┘  │
                    │                         │
                    │  ┌────────────────────┐ │
                    │  │ CoreDNS + DNSZoner │ │
                    │  │ WireGuard (wg-easy)│ │
                    │  └────────────────────┘ │
                    └────────────┬────────────┘
                                 │
                        WireGuard VPN tunnel
                       (10.13.13.0/24 subnet)
                                 │
                    ┌────────────┴────────────┐
                    │  Local PC (Archlinux)   │
                    │     RTX 4090 GPU        │
                    │                         │
                    │  Ollama (LLM inference) │
                    │  TTS / STT              │
                    │  Immich (testing)       │
                    │  PhotoPrism (testing)   │
                    └────────────┬────────────┘
                                 │
                        WireGuard VPN tunnel
                                 │
                    ┌────────────┴─────────────┐
                    │    Client Devices        │
                    │  (laptops, phones, etc.) │
                    └──────────────────────────┘
```

## Node Assignments

### VPS (Ubuntu)

The VPS is the main entry point. All user-facing services run here, proxied
through Traefik. It also serves as the WireGuard hub and DNS authority.

| Stack | Category | Purpose |
| :---- | :------- | :------ |
| traefik | core | Reverse proxy, TLS termination, routing |
| dns | core | CoreDNS + DNSZoner (dynamic DNS, DNSSEC, DoT) |
| wireguard | core | WireGuard VPN gateway (wg-easy), hub-spoke |
| authentik | core | SSO/OIDC identity provider |
| monitoring | core | Uptime Kuma status monitoring |
| dolibarr | business | ERP/CRM |
| n8n | business | Workflow automation |
| postiz | business | AI social media management |
| searxng | search | Privacy-first meta-search engine |
| meilisearch | search | Federated internal search |
| seafile | storage | File sync and share |
| litellm | ai | LLM API router/aggregator |
| open-webui | ai | LLM chat UI with RAG |
| mem0 | ai | Persistent AI memory layer |
| openclaw | ai | Personal AI coding agent |

### Local PC (Archlinux + RTX 4090)

GPU-heavy workloads run on the local machine, accessible from the VPS
(and all clients) via WireGuard VPN.

| Stack | Category | Purpose |
| :---- | :------- | :------ |
| ollama | ai | LLM inference (NVIDIA GPU) |
| tts | ai | Text-to-speech (GPU acceleration) |
| stt | ai | Speech-to-text (GPU acceleration) |
| immich | storage | Photo management with ML (testing) |
| photoprism | storage | Photo management with AI (testing) |

## Networking

### WireGuard VPN (Hub-Spoke)

```
Topology:  VPS (hub) <--> Local PC (spoke)
                     <--> Client devices (spokes)

Subnet:    10.13.13.0/24
Hub IP:    10.13.13.1 (VPS)
DNS:       10.13.13.1 (CoreDNS on VPS)
```

- **Hub-spoke model**: All peers connect to the VPS. The VPS routes traffic
  between peers when needed (e.g., client device accessing Local PC services).
- **wg-easy**: Provides a web UI for peer management at `vpn.${BASE_DOMAIN}`.
- All traffic between nodes is encrypted via WireGuard.

### Proxy Network

A shared external network named `proxy` connects Traefik to all services
that need HTTP routing. Each stack also defines its own internal network
(`<name>-internal`) for inter-service communication (e.g., app to database).

### DNS (CoreDNS + DNSZoner)

CoreDNS runs on the VPS and serves as the authoritative DNS for all services.
The DNSZoner sidecar watches container labels and dynamically generates DNS
records, so services are automatically resolvable by name.

- **DNSSEC**: Signed zones for integrity
- **DoT forwarding**: Upstream queries use DNS-over-TLS
- Clients on WireGuard use `10.13.13.1` as their DNS server

## AI Routing

```
             ┌──────────────────────┐
             │      LiteLLM         │
             │   (API Router/VPS)   │
             └───────────┬──────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
          ┌───┴───┐   ┌──┴──┐   ┌───┴────┐
          │Ollama │   │Cloud│   │OpenAI  │
          │(Local)│   │ LLM │   │Copilot │
          │GPU    │   │ API │   │etc.    │
          └───────┘   └─────┘   └────────┘
```

- **LiteLLM** runs on the VPS and acts as a unified OpenAI-compatible API
  gateway. All AI consumers (Open WebUI, OpenClaw, n8n) connect to LiteLLM.
- **Ollama** runs on the Local PC with RTX 4090. LiteLLM routes local model
  requests to Ollama over WireGuard.
- **mem0** provides persistent per-user memory, shared across Open WebUI,
  OpenClaw, and other AI tools.
- **SearXNG** provides web search results to Open WebUI RAG pipelines
  (not used for internal data search -- that's Meilisearch).

## Authentication

Authentik provides centralized SSO for all user-facing services:

- **OIDC**: Native integration for services that support OpenID Connect
  (Open WebUI, n8n, Seafile, etc.)
- **LDAP**: For services that need directory-based auth
- **Traefik forward-auth**: Catch-all for services without native SSO support

## Deployment

Deployment is SSH-based, using `deploy/deploy.sh` or the GitHub Actions CD
pipeline. Each node pulls the latest repo and runs `compose up -d` for its
assigned stacks.

```bash
# Manual deploy to VPS
./deploy/deploy.sh vps.example.com deploy /opt/selfhosted-stack \
    core/traefik core/dns core/wireguard

# Or use just recipes
just vps-up    # Start all VPS stacks
just local-up  # Start all Local PC stacks
```

See `deploy/inventory.yml` for the full node-to-stack mapping.
