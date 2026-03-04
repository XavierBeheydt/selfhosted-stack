# Roadmap

Current progress and next steps for selfhosted-stack.

## Completed

### Phase 1 — Core Infrastructure

- [x] Repository setup (MIT license, .gitignore, .env.example)
- [x] Traefik reverse proxy (compose, config, k8s)
- [x] CoreDNS + DNSZoner (compose, config, k8s, full Python project)
- [x] WireGuard VPN gateway — wg-easy (compose, k8s)
- [x] Dolibarr ERP/CRM + MariaDB (compose, k8s)
- [x] CI/CD workflows (ci.yml, deploy.yml)
- [x] justfile with 30+ recipes
- [x] Deploy scripts (deploy.sh, inventory.yml)
- [x] Architecture documentation
- [x] Shared network definitions

### AI Middleware Research & Scaffolding

- [x] OpenClaw stack — detailed README, k8s placeholder
- [x] LiteLLM stack — compose, config, k8s base manifests, README
- [x] Mem0 stack — compose (API + pgvector + Neo4j), README
- [x] Markdown table formatter script with --exclude flag
- [x] All markdown tables aligned across the repo

## Next Steps

### Phase 2 — Business Automation

- [ ] **n8n** — compose.yml, .env.example, k8s/base/, README
  - Postgres backend, Traefik labels, DNSZoner labels
  - Webhook ingress configuration
  - Worker mode support for k8s (separate queue/worker deployments)
- [ ] **Postiz** — compose.yml, .env.example, k8s/base/, README
  - Redis + Postgres dependencies
  - Traefik labels for web UI
  - OAuth configuration for social media channels
- [ ] Update README.md stack tables (mark n8n/Postiz as complete)
- [ ] Update ARCHITECTURE.md with n8n/Postiz details
- [ ] Add n8n/Postiz recipes to justfile

### Phase 3 — AI Stack

- [ ] **Ollama** — compose.yml, k8s/base/ with GPU nodeSelector
  - NVIDIA runtime configuration
  - Model volume persistence
  - Health check on /api/tags
- [ ] **Open WebUI** — compose.yml, k8s/base/, README
  - Connect to LiteLLM (not directly to Ollama)
  - RAG/document upload volume
  - Multi-user auth configuration
- [ ] **OpenClaw** — compose.yml, k8s/base/ (expand from current README-only)
  - Gateway on VPS, connected to Ollama via WireGuard
  - Mem0 integration for persistent memory
  - WhatsApp + Telegram channel configuration
- [ ] **SearXNG** — compose.yml, config/settings.yml, k8s/base/
  - Redis backend
  - Restrict to internal network (no public exposure)
  - Configure as tool for Open WebUI and OpenClaw
- [ ] **TTS** — compose.yml, k8s/base/
  - Piper (fast, CPU-friendly) + XTTS-v2 (GPU, voice cloning)
  - GPU nodeSelector for XTTS-v2
  - Shared voice model volume
- [ ] **STT** — compose.yml, k8s/base/
  - Faster-Whisper with GPU support
  - Model download and caching
- [ ] **LiteLLM** — add Mem0 k8s base manifests (currently missing)
- [ ] **Mem0** — add k8s base manifests (namespace, deployments, services, pvc)
- [ ] Wire AI data flow: all consumers → LiteLLM → Ollama/cloud; all memory → Mem0
- [ ] Update README.md and ARCHITECTURE.md with full AI topology

### Phase 4 — Storage

- [ ] **Seafile** — compose.yml, k8s/base/, README
  - MariaDB + Memcached dependencies
  - File storage volume (large PVC)
  - Traefik labels for WebDAV + web UI
- [ ] **Immich** — compose.yml, k8s/base/, README
  - Postgres + Redis + ML worker
  - Photo/video upload volume
  - GPU nodeSelector for ML classification
  - Mobile app configuration notes
- [ ] Update README.md and ARCHITECTURE.md
 - [ ] **PhotoPrism** — compose.yml, .env.example, README (stacks/search/photoprism)
   - Docker Compose test stack added at `stacks/search/photoprism/`
   - Supports TensorFlow / CLIP / Ollama integrations for advanced AI features
   - Mobile backup via WebDAV (PhotoSync) or PWA (no native background uploader)
   - Testing session: evaluation notes at `docs/tests/immich-vs-photoprism.md`

### Phase 5 — Polish & Documentation

- [ ] Full `docs/` site — per-stack deployment guides
- [ ] `docs/K3S-SETUP.md` — step-by-step K3s cluster setup
- [ ] `docs/GPU-ROUTING.md` — split DNS, nodeSelector, NodePort strategy
- [ ] `docs/WIREGUARD.md` — VPN setup, allowed IPs, K3s pod/service CIDRs
- [ ] `docs/BACKUP.md` — backup strategy for volumes and databases
- [ ] Repo badges (CI status, license, stack count)
- [ ] Screenshots / architecture diagrams (Mermaid or exported PNG)
- [ ] Kustomize overlays for each stack (vps/, local/)
- [ ] Helm chart consideration (or document why Kustomize is preferred)
- [ ] Security hardening checklist per stack
- [ ] `.env.example` audit — ensure every stack has one and they're consistent

## Architecture Decisions Still Open

- [ ] Shared Postgres instance vs per-service Postgres (LiteLLM, Mem0, n8n, Postiz all need PG)
- [ ] Redis: shared instance or per-service? (LiteLLM caching, Postiz, SearXNG, Immich all use Redis)
- [ ] Monitoring stack? (Prometheus + Grafana, or keep it out of scope)
- [ ] Log aggregation? (Loki, or rely on `docker logs` / `kubectl logs`)
- [ ] Secret management for K8s — sealed-secrets vs external-secrets vs SOPS
