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

## Deploy User Setup

The deployment scripts connect via SSH as a dedicated `deploy` user (see
`stack-inventory.yml`). Follow these steps on **each node** (Gateway and
Compute) before running any deployment.

### 1. Create the user

```bash
# Create a system-level deploy user with no login shell and no password
sudo useradd --system --no-create-home --shell /usr/sbin/nologin deploy
# OR, if you prefer a home directory for SSH keys:
sudo useradd --create-home --shell /bin/bash deploy
sudo passwd -l deploy          # lock password-based login
```

### 2. Configure SSH access (key-only)

```bash
# On your local machine – generate a dedicated deploy key (Ed25519, no passphrase)
ssh-keygen -t ed25519 -C "deploy@selfhosted-stack" -f ~/.ssh/deploy_ed25519

# Copy the public key to each node
ssh-copy-id -i ~/.ssh/deploy_ed25519.pub <admin-user>@<node-host>
# Then move it to the deploy user's authorized_keys:
sudo mkdir -p /home/deploy/.ssh
sudo tee -a /home/deploy/.ssh/authorized_keys < ~/.ssh/deploy_ed25519.pub
sudo chmod 700 /home/deploy/.ssh
sudo chmod 600 /home/deploy/.ssh/authorized_keys
sudo chown -R deploy:deploy /home/deploy/.ssh
```

Restrict the key in `authorized_keys` to limit what the deploy user can do:

```
no-agent-forwarding,no-X11-forwarding,no-pty ssh-ed25519 AAAA... deploy@selfhosted-stack
```

### 3. Harden SSH daemon

In `/etc/ssh/sshd_config` (or a drop-in under `/etc/ssh/sshd_config.d/`):

```sshd_config
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
AllowUsers deploy <your-admin-user>
```

```bash
sudo sshd -t          # validate config
sudo systemctl reload sshd
```

### 4. Grant access to the container engine

#### Podman (rootless — default)

Run containers as the `deploy` user without root. Enable the user's systemd
session so it survives after SSH logout:

```bash
sudo loginctl enable-linger deploy
```

No additional group membership is required for rootless Podman.

#### Docker

Add the deploy user to the `docker` group:

```bash
sudo usermod -aG docker deploy
# Re-login or run: newgrp docker
```

> **Security note**: Membership in the `docker` group is equivalent to
> passwordless `sudo`. Keep this in mind and prefer Podman rootless when
> possible.

### 5. Grant write access to the deploy path

```bash
sudo mkdir -p /opt/selfhosted-stack
sudo chown deploy:deploy /opt/selfhosted-stack
sudo chmod 750 /opt/selfhosted-stack
```

### 6. Verify the setup

```bash
# From your local machine — confirm SSH works with the deploy key
SSH_KEY_PATH=~/.ssh/deploy_ed25519 \
  ssh -i ~/.ssh/deploy_ed25519 deploy@<node-host> "echo 'SSH OK'"

# Run a test deployment
SSH_KEY_PATH=~/.ssh/deploy_ed25519 \
  ./scripts/deploy.sh <node-host> deploy /opt/selfhosted-stack
```

### 7. Store the key securely (CI/CD)

For automated deployments via GitHub Actions, add the private key as a
repository secret and reference it in the workflow:

```
Secret name : DEPLOY_SSH_KEY
Secret value: <contents of ~/.ssh/deploy_ed25519>
```

The CD workflow (`deploy.yml`) reads this secret and writes it to a temporary
file before passing it to `deploy.sh` via `SSH_KEY_PATH`.

## Requirements

- [Podman](https://podman.io/) (or Docker) with compose plugin
- [just](https://github.com/casey/just) task runner
- WireGuard for inter-node connectivity

## License

[MIT](LICENSE) -- Xavier Beheydt
