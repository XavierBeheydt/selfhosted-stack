# selfhosted-stack - Infrastructure management
# https://github.com/XavierBeheydt/selfhosted-stack

# Default container engine (override: CONTAINER_ENGINE=podman just ...)
container_engine := env("CONTAINER_ENGINE", "docker")
stacks_dir       := "stacks"

export DNS_HOST := env("DNS_HOST", "127.0.0.1")
export DNS_PORT := env("DNS_PORT", "5300")
export BASE_DOMAIN := env("BASE_DOMAIN", "localhost")

# === Utilities ==============================================================

# List all available recipes
[private]
default:
    @just --list

# Create the shared proxy-frontend network (idempotent)
[private]
network-create:
    -@{{container_engine}} network create proxy-frontend 2>/dev/null || true

# Remove the proxy-frontend network
[private]
network-cleanup:
    -@{{container_engine}} network rm proxy-frontend 2>/dev/null || true

# Show status of all containers
status:
    @{{container_engine}} ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# === Stack Lifecycle ========================================================

# Start all core stacks (traefik + dns + wireguard + dolibarr)
up: traefik-up dns-up wireguard-up dolibarr-up

# Stop all stacks (reverse order)
down: dolibarr-down wireguard-down dns-down traefik-down

# === Traefik (Reverse Proxy) ================================================

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

# === DNS (CoreDNS + DNSZoner) ===============================================

dns_cmd := container_engine + " compose -f " + stacks_dir / "core" / "dns" / "compose.yml"

# Start DNS services (CoreDNS + DNSZoner)
dns-up *services: network-create
    {{dns_cmd}} up -d {{services}}

# Stop DNS services
dns-down *services:
    {{dns_cmd}} down {{services}}

# Show DNS logs
dns-logs *args:
    {{dns_cmd}} logs {{args}}

# Run DNS integration tests
dns-test *services: (dns-up services) && (dns-down services)
    @./stacks/core/dns/dnszoner/scripts/tests.sh

# Build the dnszoner container image
[confirm("Rebuild dnszoner image from scratch?")]
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

# === WireGuard (VPN Gateway) ================================================

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

# === Dolibarr (ERP/CRM) ====================================================

dolibarr_cmd := container_engine + " compose -f " + stacks_dir / "business" / "dolibarr" / "compose.yml"

# Start Dolibarr ERP
dolibarr-up *services: network-create
    {{dolibarr_cmd}} up -d {{services}}

# Stop Dolibarr ERP
dolibarr-down *services:
    {{dolibarr_cmd}} down {{services}}

# Show Dolibarr logs
dolibarr-logs *args:
    {{dolibarr_cmd}} logs {{args}}

# Restore Dolibarr database from a SQL dump
dolibarr-restore-db dbfile: dolibarr-up
    sleep 10 && {{dolibarr_cmd}} exec -T db /usr/bin/mariadb $DOLI_DB_NAME -hdb -u$DOLI_DB_USER -p$DOLI_DB_PASSWORD < {{dbfile}}

# === K8s (Kubernetes) =======================================================

# Apply all Kubernetes manifests (Kustomize)
k8s-apply:
    kubectl apply -k {{stacks_dir}}/core/traefik/k8s/base/
    kubectl apply -k {{stacks_dir}}/core/dns/k8s/base/
    kubectl apply -k {{stacks_dir}}/core/wireguard/k8s/base/
    kubectl apply -k {{stacks_dir}}/business/dolibarr/k8s/base/

# Delete all Kubernetes resources
k8s-delete:
    kubectl delete -k {{stacks_dir}}/business/dolibarr/k8s/base/ --ignore-not-found
    kubectl delete -k {{stacks_dir}}/core/wireguard/k8s/base/ --ignore-not-found
    kubectl delete -k {{stacks_dir}}/core/dns/k8s/base/ --ignore-not-found
    kubectl delete -k {{stacks_dir}}/core/traefik/k8s/base/ --ignore-not-found

# === CI / Checks ============================================================

# Run all tests (dnszoner + dns integration)
test: dnszoner-test dns-test

# Run all linters
lint: dnszoner-lint

# Format all code
fmt: dnszoner-fmt
