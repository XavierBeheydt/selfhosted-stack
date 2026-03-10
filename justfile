# selfhosted-stack - Infrastructure management
# https://github.com/XavierBeheydt/selfhosted-stack

# Default container engine (override: CONTAINER_ENGINE=docker just ...)
container_engine := env("CONTAINER_ENGINE", "podman")
stacks_dir       := "stacks"

export BASE_DOMAIN := env("BASE_DOMAIN", "localhost")

# === Utilities ==============================================================

# List all available recipes
[private]
default:
    @just --list

# Create the shared proxy network (idempotent)
[private]
network-create:
    -@{{container_engine}} network create proxy 2>/dev/null || true

# Remove the shared proxy network
[private]
network-cleanup:
    -@{{container_engine}} network rm proxy 2>/dev/null || true

# Show status of all containers
status:
    @{{container_engine}} ps --format "table {{{{.Names}}}}\t{{{{.Status}}}}\t{{{{.Ports}}}}"

# Generate local TLS certificates using mkcert
# Usage: just mkcert
mkcert:
    #!/usr/bin/env bash
    set -euo pipefail
    mkdir -p certs
    if ! command -v mkcert >/dev/null 2>&1; then
        echo "mkcert not found; attempting to install..."
        if command -v brew >/dev/null 2>&1; then
            brew install mkcert
        elif command -v apk >/dev/null 2>&1; then
            sudo apk add --no-cache curl nss
            os=$(uname -s | tr '[:upper:]' '[:lower:]')
            arch=$(uname -m)
            case "$arch" in
                x86_64) arch=amd64 ;;
                aarch64) arch=arm64 ;;
            esac
            curl -sSL "https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-${os}-${arch}" -o /tmp/mkcert
            sudo install /tmp/mkcert /usr/local/bin/mkcert
        elif [ -f /etc/debian_version ]; then
            sudo apt-get update
            sudo apt-get install -y libnss3-tools curl
            os=$(uname -s | tr '[:upper:]' '[:lower:]')
            arch=$(uname -m)
            case "$arch" in
                x86_64) arch=amd64 ;;
                aarch64) arch=arm64 ;;
            esac
            curl -sSL "https://github.com/FiloSottile/mkcert/releases/latest/download/mkcert-${os}-${arch}" -o /tmp/mkcert
            sudo install /tmp/mkcert /usr/local/bin/mkcert
        elif command -v pacman >/dev/null 2>&1; then
            sudo pacman -S --noconfirm mkcert nss
        elif command -v dnf >/dev/null 2>&1; then
            sudo dnf install -y mkcert nss-tools
        else
            echo "Automatic mkcert install not supported on this system. Visit https://github.com/FiloSottile/mkcert for manual installation." >&2
            exit 1
        fi
    fi
    mkcert -install || true
    mkcert -cert-file certs/{{BASE_DOMAIN}}.crt -key-file certs/{{BASE_DOMAIN}}.key "{{BASE_DOMAIN}}"
    echo "Created certs/{{BASE_DOMAIN}}.crt and certs/{{BASE_DOMAIN}}.key"

# === Compose Helpers ========================================================

# Generic: start a stack by path (e.g. just stack-up core/traefik)
stack-up path: network-create
    {{container_engine}} compose -f {{stacks_dir}}/{{path}}/compose.yml up -d

# Generic: stop a stack by path
stack-down path:
    {{container_engine}} compose -f {{stacks_dir}}/{{path}}/compose.yml down

# Generic: show logs for a stack
stack-logs path *args:
    {{container_engine}} compose -f {{stacks_dir}}/{{path}}/compose.yml logs {{args}}

# Generic: pull latest images for a stack
stack-pull path:
    {{container_engine}} compose -f {{stacks_dir}}/{{path}}/compose.yml pull

# === Gateway Stacks (full deploy order) ======================================

# Start all Gateway stacks in dependency order
gateway-up: traefik-up dns-up wireguard-up authentik-up monitoring-up dolibarr-up n8n-up postiz-up searxng-up meilisearch-up seafile-up

# Stop all Gateway stacks (reverse order)
gateway-down: seafile-down meilisearch-down searxng-down postiz-down n8n-down dolibarr-down monitoring-down authentik-down wireguard-down dns-down traefik-down

# === Compute Stacks (GPU workloads) =========================================

# Start all Compute stacks
compute-up: ollama-up litellm-up open-webui-up mem0-up openclaw-up tts-up stt-up

# Stop all Compute stacks (reverse order)
compute-down: stt-down tts-down openclaw-down mem0-down open-webui-down litellm-down ollama-down

# === Core: Traefik ==========================================================

traefik_cmd := container_engine + " compose -f " + stacks_dir / "core" / "traefik" / "compose.yml"

# Start Traefik reverse proxy
traefik-up: network-create
    {{traefik_cmd}} up -d

# Stop Traefik reverse proxy
traefik-down:
    {{traefik_cmd}} down

# Show Traefik logs
traefik-logs *args:
    {{traefik_cmd}} logs {{args}}

# === Core: DNS (CoreDNS + DNSZoner) =========================================

dns_cmd := container_engine + " compose -f " + stacks_dir / "core" / "dns" / "compose.yml"

# Start DNS services
dns-up *services: network-create
    {{dns_cmd}} up -d {{services}}

# Stop DNS services
dns-down *services:
    {{dns_cmd}} down {{services}}

# Show DNS logs
dns-logs *args:
    {{dns_cmd}} logs {{args}}

# Build the dnszoner container image
dns-build-dnszoner:
    {{dns_cmd}} build --no-cache dnszoner

# === DNSZoner (Python project) ==============================================

dnszoner_dir := stacks_dir / "core" / "dns" / "dnszoner"

# Install dnszoner in editable mode
[private]
dnszoner-install:
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} sync --group dev

# Run dnszoner locally (for development)
dnszoner-run: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run dnszoner --verbose

# Run dnszoner tests with coverage
dnszoner-test: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run pytest

# Run dnszoner linter
dnszoner-lint: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff check src/ tests/

# Format dnszoner code
dnszoner-fmt: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff format src/ tests/

# === Core: WireGuard ========================================================

wireguard_cmd := container_engine + " compose -f " + stacks_dir / "core" / "wireguard" / "compose.yml"

# Start WireGuard VPN gateway
wireguard-up: network-create
    {{wireguard_cmd}} up -d

# Stop WireGuard VPN gateway
wireguard-down:
    {{wireguard_cmd}} down

# Show WireGuard logs
wireguard-logs *args:
    {{wireguard_cmd}} logs {{args}}

# === Core: Authentik ========================================================

authentik_cmd := container_engine + " compose -f " + stacks_dir / "core" / "authentik" / "compose.yml"

# Start Authentik identity provider
authentik-up: network-create
    {{authentik_cmd}} up -d

# Stop Authentik
authentik-down:
    {{authentik_cmd}} down

# Show Authentik logs
authentik-logs *args:
    {{authentik_cmd}} logs {{args}}

# === Core: Monitoring =======================================================

monitoring_cmd := container_engine + " compose -f " + stacks_dir / "core" / "monitoring" / "compose.yml"

# Start Uptime Kuma monitoring
monitoring-up: network-create
    {{monitoring_cmd}} up -d

# Stop Uptime Kuma
monitoring-down:
    {{monitoring_cmd}} down

# Show Uptime Kuma logs
monitoring-logs *args:
    {{monitoring_cmd}} logs {{args}}

# === Business: Dolibarr =====================================================

dolibarr_cmd := container_engine + " compose -f " + stacks_dir / "business" / "dolibarr" / "compose.yml"

# Start Dolibarr ERP
dolibarr-up: network-create
    {{dolibarr_cmd}} up -d

# Stop Dolibarr ERP
dolibarr-down:
    {{dolibarr_cmd}} down

# Show Dolibarr logs
dolibarr-logs *args:
    {{dolibarr_cmd}} logs {{args}}

# Restore Dolibarr database from a SQL dump
dolibarr-restore-db dbfile: dolibarr-up
    sleep 10 && {{dolibarr_cmd}} exec -T db /usr/bin/mariadb $DOLI_DB_NAME -hdb -u$DOLI_DB_USER -p$DOLI_DB_PASSWORD < {{dbfile}}

# === Business: n8n ==========================================================

n8n_cmd := container_engine + " compose -f " + stacks_dir / "business" / "n8n" / "compose.yml"

# Start n8n workflow automation
n8n-up: network-create
    {{n8n_cmd}} up -d

# Stop n8n
n8n-down:
    {{n8n_cmd}} down

# Show n8n logs
n8n-logs *args:
    {{n8n_cmd}} logs {{args}}

# === Business: Postiz =======================================================

postiz_cmd := container_engine + " compose -f " + stacks_dir / "business" / "postiz" / "compose.yml"

# Start Postiz social media manager
postiz-up: network-create
    {{postiz_cmd}} up -d

# Stop Postiz
postiz-down:
    {{postiz_cmd}} down

# Show Postiz logs
postiz-logs *args:
    {{postiz_cmd}} logs {{args}}

# === Search: SearXNG ========================================================

searxng_cmd := container_engine + " compose -f " + stacks_dir / "search" / "searxng" / "compose.yml"

# Start SearXNG meta-search engine
searxng-up: network-create
    {{searxng_cmd}} up -d

# Stop SearXNG
searxng-down:
    {{searxng_cmd}} down

# Show SearXNG logs
searxng-logs *args:
    {{searxng_cmd}} logs {{args}}

# === Search: Meilisearch ====================================================

meilisearch_cmd := container_engine + " compose -f " + stacks_dir / "search" / "meilisearch" / "compose.yml"

# Start Meilisearch
meilisearch-up: network-create
    {{meilisearch_cmd}} up -d

# Stop Meilisearch
meilisearch-down:
    {{meilisearch_cmd}} down

# Show Meilisearch logs
meilisearch-logs *args:
    {{meilisearch_cmd}} logs {{args}}

# === Storage: Seafile =======================================================

seafile_cmd := container_engine + " compose -f " + stacks_dir / "storage" / "seafile" / "compose.yml"

# Start Seafile file sync & share
seafile-up: network-create
    {{seafile_cmd}} up -d

# Stop Seafile
seafile-down:
    {{seafile_cmd}} down

# Show Seafile logs
seafile-logs *args:
    {{seafile_cmd}} logs {{args}}

# === Storage: Immich ========================================================

immich_cmd := container_engine + " compose -f " + stacks_dir / "storage" / "immich" / "compose.yml"

# Start Immich photo management
immich-up: network-create
    {{immich_cmd}} up -d

# Stop Immich
immich-down:
    {{immich_cmd}} down

# Show Immich logs
immich-logs *args:
    {{immich_cmd}} logs {{args}}

# === Storage: PhotoPrism ====================================================

photoprism_cmd := container_engine + " compose -f " + stacks_dir / "storage" / "photoprism" / "compose.yml"

# Start PhotoPrism photo management
photoprism-up: network-create
    {{photoprism_cmd}} up -d

# Stop PhotoPrism
photoprism-down:
    {{photoprism_cmd}} down

# Show PhotoPrism logs
photoprism-logs *args:
    {{photoprism_cmd}} logs {{args}}

# === AI: Ollama =============================================================

ollama_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "ollama" / "compose.yml"

# Start Ollama LLM server (GPU)
ollama-up:
    {{ollama_cmd}} up -d

# Stop Ollama
ollama-down:
    {{ollama_cmd}} down

# Show Ollama logs
ollama-logs *args:
    {{ollama_cmd}} logs {{args}}

# === AI: LiteLLM ============================================================

litellm_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "litellm" / "compose.yml"

# Start LiteLLM API gateway
litellm-up: network-create
    {{litellm_cmd}} up -d

# Stop LiteLLM
litellm-down:
    {{litellm_cmd}} down

# Show LiteLLM logs
litellm-logs *args:
    {{litellm_cmd}} logs {{args}}

# === AI: Open WebUI =========================================================

openwebui_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "open-webui" / "compose.yml"

# Start Open WebUI chat interface
open-webui-up: network-create
    {{openwebui_cmd}} up -d

# Stop Open WebUI
open-webui-down:
    {{openwebui_cmd}} down

# Show Open WebUI logs
open-webui-logs *args:
    {{openwebui_cmd}} logs {{args}}

# === AI: mem0 ===============================================================

mem0_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "mem0" / "compose.yml"

# Start mem0 memory layer
mem0-up: network-create
    {{mem0_cmd}} up -d

# Stop mem0
mem0-down:
    {{mem0_cmd}} down

# Show mem0 logs
mem0-logs *args:
    {{mem0_cmd}} logs {{args}}

# === AI: OpenClaw ===========================================================

openclaw_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "openclaw" / "compose.yml"

# Start OpenClaw AI agent
openclaw-up: network-create
    {{openclaw_cmd}} up -d

# Stop OpenClaw
openclaw-down:
    {{openclaw_cmd}} down

# Show OpenClaw logs
openclaw-logs *args:
    {{openclaw_cmd}} logs {{args}}

# === AI: TTS ================================================================

tts_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "tts" / "compose.yml"

# Start text-to-speech service
tts-up:
    {{tts_cmd}} up -d

# Stop TTS
tts-down:
    {{tts_cmd}} down

# Show TTS logs
tts-logs *args:
    {{tts_cmd}} logs {{args}}

# === AI: STT ================================================================

stt_cmd := container_engine + " compose -f " + stacks_dir / "ai" / "stt" / "compose.yml"

# Start speech-to-text service
stt-up:
    {{stt_cmd}} up -d

# Stop STT
stt-down:
    {{stt_cmd}} down

# Show STT logs
stt-logs *args:
    {{stt_cmd}} logs {{args}}

# === CI / Checks ============================================================

# Run all tests (dnszoner)
test: dnszoner-test

# Run all linters
lint: dnszoner-lint

# Format all code
fmt: dnszoner-fmt

# Validate all compose files
validate:
    #!/usr/bin/env bash
    set -euo pipefail
    errors=0
    for f in $(find stacks -name compose.yml -type f | sort); do
        printf "Validating %s... " "$f"
        if {{container_engine}} compose -f "$f" config --quiet 2>/dev/null; then
            echo "OK"
        else
            echo "FAIL"
            errors=$((errors + 1))
        fi
    done
    if [ "$errors" -gt 0 ]; then
        echo "ERROR: $errors compose file(s) failed validation"
        exit 1
    fi
    echo "All compose files valid"

# Run the formatter in check mode (matches CI ruff format --check)
dnszoner-fmt-check: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff format --check src/ tests/

# Validate all compose files with the same environment used in CI (safe defaults)
validate-ci:
    #!/usr/bin/env bash
    set -euo pipefail
    # Provide the env vars the compose files may expect during CI validation
    export CONTAINER_ENGINE_SOCKET=/var/run/docker.sock
    export BASE_DOMAIN=localhost
    export TZ=UTC
    export TRAEFIK_DASHBOARD_AUTH="admin:test"
    export WG_HOST=vpn.localhost
    export WG_PASSWORD_HASH="test"
    export AUTHENTIK_SECRET_KEY=test-secret-key
    export AUTHENTIK_DB_PASSWORD=test
    export DOLI_DB_ROOT_PASSWORD=test
    export DOLI_DB_PASSWORD=test
    export DOLI_ADMIN_PASSWORD=test
    export POSTIZ_DB_PASSWORD=test
    export POSTIZ_JWT_SECRET=test-jwt-secret
    export SEARXNG_SECRET=test-secret
    export MEILI_MASTER_KEY=test-master-key
    export SEAFILE_DB_ROOT_PASSWORD=test
    export SEAFILE_ADMIN_EMAIL=admin@test.com
    export SEAFILE_ADMIN_PASSWORD=test
    export IMMICH_DB_PASSWORD=test
    export PHOTOPRISM_ADMIN_PASSWORD=test
    export PHOTOPRISM_DB_PASSWORD=test
    export PHOTOPRISM_DB_ROOT_PASSWORD=test
    export LITELLM_MASTER_KEY=test-master-key
    export LITELLM_API_KEY=test-api-key
    export LITELLM_DB_PASSWORD=test
    export WEBUI_SECRET_KEY=test-secret-key

    errors=0
    for f in $(find stacks -name compose.yml -type f | sort); do
        printf "Validating %s... " "$f"
        if {{container_engine}} compose -f "$f" config --quiet 2>/dev/null; then
            echo "OK"
        else
            echo "FAIL"
            errors=$((errors + 1))
        fi
    done
    if [ "$errors" -gt 0 ]; then
        echo "ERROR: $errors compose file(s) failed validation"
        exit 1
    fi
    echo "All compose files valid"

# Run ShellCheck locally (if installed)
shellcheck:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v shellcheck >/dev/null 2>&1; then
        # collect shell script files tracked by git, fall back to scanning repository
        files=$(git ls-files '*.sh' || true)
        if [ -z "$files" ]; then
            echo "No shell scripts tracked by git found, skipping shellcheck"
        else
            shellcheck -x $files
        fi
    else
        echo "shellcheck not installed, skipping shell checks. Install it to enable shell linting."
    fi

# Run the same sequence of checks that CI runs (lint, format-check, tests, compose validate, shellcheck)
ci: dnszoner-install
    #!/usr/bin/env bash
    set -euo pipefail
    echo "== DNSZoner: ruff check =="
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff check src/ tests/

    echo "== DNSZoner: ruff format --check =="
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff format --check src/ tests/

    echo "== DNSZoner: pytest =="
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run pytest

    echo "== Compose: validate (CI defaults) =="
    just validate-ci

    echo "== Shell: shellcheck =="
    just shellcheck || true
