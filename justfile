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

# Run the formatter in check mode (matches CI ruff format --check)
dnszoner-fmt-check: dnszoner-install
    uv --project {{dnszoner_dir}} --directory {{dnszoner_dir}} run ruff format --check src/ tests/

# Run all tests (including hostsfilter)
test-all: dnszoner-test hostsfilter-test

# Run all linters (including hostsfilter)
lint-all: dnszoner-lint hostsfilter-lint

# Format all code (including hostsfilter)
fmt-all: dnszoner-fmt hostsfilter-fmt

# === Hosts Filter (Python project) ============================================

hostsfilter_dir := stacks_dir / "core" / "dns" / "hosts-filter"

# Install hostsfilter in editable mode
[private]
hostsfilter-install:
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} sync --group dev

# Run hostsfilter locally (for development)
hostsfilter-run: hostsfilter-install
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} run hostsfilter --verbose

# Run hostsfilter tests with coverage
hostsfilter-test: hostsfilter-install
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} run pytest

# Run hostsfilter linter
hostsfilter-lint: hostsfilter-install
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} run ruff check src/ tests/

# Format hostsfilter code
hostsfilter-fmt: hostsfilter-install
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} run ruff format src/ tests/

# Run the formatter in check mode (matches CI ruff format --check)
hostsfilter-fmt-check: hostsfilter-install
    uv --project {{hostsfilter_dir}} --directory {{hostsfilter_dir}} run ruff format --check src/ tests/

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
