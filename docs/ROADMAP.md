# Roadmap

Progress tracker for the selfhosted-stack rework (Compose-based architecture).

## Completed

### Phase 1 -- Foundation

- [x] `AGENTS.md` + `CLAUDE.md` symlink
- [x] `README.md` with project overview and quickstart
- [x] `.gitignore`, `.env.example`, `LICENSE` (MIT)
- [x] `stack-network.yml` (external `proxy` network)

### Phase 2 -- Core Stacks

- [x] **Traefik** -- reverse proxy with auto-TLS and dashboard
- [x] **CoreDNS + DNSZoner** -- dynamic container-based DNS with zone generation
- [x] **WireGuard** -- hub-spoke VPN via wg-easy
- [x] **Authentik** -- SSO provider (OIDC/LDAP)
- [x] **Uptime Kuma** -- monitoring and status page

### Phase 3 -- Business Stacks

- [x] **Dolibarr** -- ERP/CRM (official v22 image + MariaDB)
- [x] **n8n** -- workflow automation (+ PostgreSQL)
- [x] **Postiz** -- social media scheduling (+ PostgreSQL + Redis)

### Phase 4 -- AI Stacks

- [x] **Ollama** -- LLM inference with GPU passthrough (local node)
- [x] **LiteLLM** -- unified LLM proxy (+ PostgreSQL)
- [x] **Open WebUI** -- team chat interface with RAG (+ SearXNG)
- [x] **mem0** -- persistent AI memory (+ Qdrant)
- [x] **OpenClaw** -- AI coding agent
- [x] **TTS** -- text-to-speech (openedai-speech)
- [x] **STT** -- speech-to-text (faster-whisper-server)

### Phase 5 -- Search and Storage

- [x] **Meilisearch** -- federated internal search
- [x] **SearXNG** -- privacy-first web meta-search (+ settings.yml)
- [x] **Seafile** -- file sync and share (+ MariaDB + memcached)
- [x] **Immich** -- photo management (+ ML + pgvecto-rs + Redis)
- [x] **PhotoPrism** -- photo library (+ MariaDB)

### Phase 6 -- Tooling

- [x] `justfile` -- task runner with per-service recipes, node groups, validation
- [x] `scripts/deploy.sh` -- SSH-based deployment script
- [x] `stack-inventory.yml` -- node inventory (Gateway + Compute)


### Phase 7 -- CI/CD

- [x] `.github/workflows/ci.yml` -- DNSZoner tests, compose validation, ShellCheck
- [x] `.github/workflows/deploy.yml` -- Gateway + Compute node deployment via SSH

### Phase 8 -- Documentation

- [x] Architecture section in `AGENTS.md` -- network topology, node mapping, AI routing, auth

### Phase 9 -- DNSZoner Refactor

- [x] `DiscoveryClient` class with persistent session reuse and context manager
- [x] Atomic zone file writes (tempfile + rename)
- [x] Sequential SOA serials (`YYYYMMDDnn`)
- [x] CLI flags (`--version`, `--label-prefix`, `--default-ttl`)
- [x] CNAME record support
- [x] Domain/hostname validation, config validation
- [x] Stale zone file cleanup
- [x] Bug fixes (TTL parsing crash, Content-Length bytes, 404 status text)
- [x] Full test suite (98 tests, 73% coverage)
- [x] `README.md` documentation

## Upcoming

### Stack Hardening

- [ ] Add healthcheck to all compose services where missing
- [ ] Audit volume mount permissions
- [ ] Review resource limits (memory, CPU) per service
- [ ] Add log rotation configuration

### Operational

- [ ] Backup strategy (volumes, databases)
- [ ] Secret management (consider SOPS, Vault, or `podman secret`)
- [ ] Alerting integration with Uptime Kuma
- [ ] Runbook for common operations (upgrades, restores, node failover)

### Enhancements

- [ ] Authentik integration for all user-facing services
- [ ] Meilisearch indexing pipelines (Dolibarr, Seafile, photos)
- [ ] mem0 integration with Open WebUI
- [ ] DNSSEC signing in CoreDNS
- [ ] DoT/DoH forwarding in CoreDNS
