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

## Key Files

| File | Purpose |
| :--- | :------ |
| [README.md](README.md) | Project overview and quickstart |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phased plan with progress |
| [justfile](justfile) | Task runner recipes |
| [.env.example](.env.example) | Global environment template |
| [stack-inventory.yml](stack-inventory.yml) | Node inventory |
| [scripts/deploy.sh](scripts/deploy.sh) | SSH-based deployment script |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | CI pipeline |
| [.github/workflows/deploy.yml](.github/workflows/deploy.yml) | CD pipeline |

## Architecture

### Network Topology

Two nodes connected via WireGuard hub-spoke VPN. The **Gateway** is the entry
point and WireGuard hub. The **Compute** node provides GPU for LLM inference
and heavy ML workloads. All services are container-based (Podman/Docker
Compose) with Traefik as the shared reverse proxy.

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

Both Compute and Client devices are **spokes** connecting directly to the
Gateway hub. Clients never route through Compute.

### Node Assignments

#### Gateway Node

The entry point. All user-facing services run here, proxied through Traefik.
Also serves as the WireGuard hub and DNS authority.

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

#### Compute Node (GPU)

GPU-heavy workloads, accessible from the Gateway (and all clients) via
WireGuard VPN.

| Stack | Category | Purpose |
| :---- | :------- | :------ |
| ollama | ai | LLM inference (NVIDIA GPU) |
| tts | ai | Text-to-speech (GPU acceleration) |
| stt | ai | Speech-to-text (GPU acceleration) |
| immich | storage | Photo management with ML (testing) |
| photoprism | storage | Photo management with AI (testing) |

### Networking

#### WireGuard VPN (Hub-Spoke)

```
Topology:  Gateway (hub) <--> Compute (spoke)
                         <--> Client devices (spokes)

Subnet:    10.13.13.0/24
Hub IP:    10.13.13.1 (Gateway)
DNS:       10.13.13.1 (CoreDNS on Gateway)
```

- **Hub-spoke model**: All peers connect to the Gateway. The Gateway routes
  traffic between peers when needed.
- **wg-easy**: Provides a web UI for peer management at `vpn.${BASE_DOMAIN}`.
- All traffic between nodes is encrypted via WireGuard.

#### Proxy Network

A shared external network named `proxy` connects Traefik to all services
that need HTTP routing. Each stack also defines its own internal network
(`<name>-internal`) for inter-service communication (e.g., app to database).

#### DNS (CoreDNS + DNSZoner)

CoreDNS runs on the Gateway and serves as the authoritative DNS for all
services. The DNSZoner sidecar watches container labels and dynamically
generates DNS records, so services are automatically resolvable by name.

- **DNSSEC**: Signed zones for integrity
- **DoT forwarding**: Upstream queries use DNS-over-TLS
- Clients on WireGuard use `10.13.13.1` as their DNS server

### AI Routing

```
         +---------------------+
         |      LiteLLM        |
         |  (API Router)       |
         +---+------+------+---+
             |      |      |
         +---+--+ +-+---+ ++------+
         |Ollama| |Cloud| |OpenAI |
         |(GPU) | | LLM | |etc.   |
         +------+ +-----+ +-------+
```

- **LiteLLM** acts as a unified OpenAI-compatible API gateway. All AI
  consumers (Open WebUI, OpenClaw, n8n) connect to LiteLLM.
- **Ollama** runs on the Compute node with GPU. LiteLLM routes local model
  requests to Ollama over WireGuard.
- **mem0** provides persistent per-user memory, shared across Open WebUI,
  OpenClaw, and other AI tools.
- **SearXNG** provides web search results to Open WebUI RAG pipelines
  (not used for internal data search -- that's Meilisearch).

### Authentication

Authentik provides centralized SSO for all user-facing services:

- **OIDC**: Native integration for services that support OpenID Connect
  (Open WebUI, n8n, Seafile, etc.)
- **LDAP**: For services that need directory-based auth
- **Traefik forward-auth**: Catch-all for services without native SSO support

### Deployment

Deployment is SSH-based, using `scripts/deploy.sh` or the GitHub Actions CD
pipeline. Each node pulls the latest repo and runs `compose up -d` for its
assigned stacks.

```bash
# Use just recipes
just gateway-up    # Start all Gateway stacks
just compute-up    # Start all Compute stacks
```

See `stack-inventory.yml` for the full node-to-stack mapping.

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
- WireGuard uses hub-spoke topology (Gateway as hub, all devices connect to Gateway)
- System is entirely private -- accessible only via WireGuard
