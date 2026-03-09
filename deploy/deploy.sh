#!/usr/bin/env bash

# Copyright © 2026 Xavier Beheydt <xavier.beheydt@gmail.com> - All Rights Reserved

# deploy.sh - Deploy stacks to remote servers via SSH
#
# Usage:
#   ./deploy/deploy.sh <host> <user> <deploy_path> [stacks...]
#
# Example:
#   ./deploy/deploy.sh vps.example.com deploy /opt/selfhosted-stack core/traefik core/dns
#
# Environment variables:
#   SSH_KEY_PATH  - Path to SSH private key (default: uses ssh-agent)
#   SSH_PORT      - SSH port (default: 22)
#   BRANCH        - Git branch to deploy (default: main)
#   REPO_URL      - Repository URL (default: XavierBeheydt/selfhosted-stack)

set -euo pipefail
IFS=$'\n\t'

# --- Configuration ---
HOST="${1:?Usage: deploy.sh <host> <user> <deploy_path> [stacks...]}"
USER="${2:?Missing user argument}"
DEPLOY_PATH="${3:?Missing deploy_path argument}"
shift 3
STACKS=("${@:-}")

SSH_PORT="${SSH_PORT:-22}"
BRANCH="${BRANCH:-main}"
REPO_URL="${REPO_URL:-git@github.com:XavierBeheydt/selfhosted-stack.git}"

# SSH options
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o ConnectTimeout=10 -p ${SSH_PORT}"
if [[ -n "${SSH_KEY_PATH:-}" ]]; then
    SSH_OPTS="${SSH_OPTS} -i ${SSH_KEY_PATH}"
fi

ssh_cmd() {
    # shellcheck disable=SC2086
    ssh ${SSH_OPTS} "${USER}@${HOST}" "$@"
}

log() {
    printf "[deploy] %s\n" "$*"
}

err() {
    printf "[deploy] ERROR: %s\n" "$*" >&2
    exit 1
}

# --- Pre-flight checks ---
log "Deploying to ${USER}@${HOST}:${DEPLOY_PATH}"
log "Branch: ${BRANCH}"
log "Stacks: ${STACKS[*]:-default set}"

# Test SSH connection
ssh_cmd "echo 'SSH connection OK'" || err "Cannot connect to ${HOST}"

# --- Deploy ---
log "Syncing repository on remote..."

ssh_cmd "bash -s" <<REMOTE_SCRIPT
set -euo pipefail

# Ensure deploy directory exists
mkdir -p "${DEPLOY_PATH}"
cd "${DEPLOY_PATH}"

# Clone or update the repository
if [ -d .git ]; then
    echo "[remote] Pulling latest changes..."
    git fetch origin
    git checkout ${BRANCH}
    git reset --hard origin/${BRANCH}
    git clean -fd
else
    echo "[remote] Cloning repository..."
    git clone --branch ${BRANCH} ${REPO_URL} .
fi

# Detect container engine
if command -v podman &>/dev/null; then
    ENGINE="podman"
elif command -v docker &>/dev/null; then
    ENGINE="docker"
else
    echo "[remote] ERROR: No container engine found (podman or docker required)"
    exit 1
fi

echo "[remote] Using container engine: \${ENGINE}"

# Ensure shared network exists
\${ENGINE} network create proxy 2>/dev/null || true

# Determine which stacks to deploy
DEPLOY_STACKS=(${STACKS[*]:-})

if [ \${#DEPLOY_STACKS[@]} -eq 0 ]; then
    # Default: core stacks only
    DEPLOY_STACKS=(core/traefik core/dns core/wireguard core/authentik core/monitoring)
fi

echo "[remote] Deploying stacks: \${DEPLOY_STACKS[*]}"

for stack in "\${DEPLOY_STACKS[@]}"; do
    compose_file="stacks/\${stack}/compose.yml"
    if [ -f "\${compose_file}" ]; then
        echo "[remote] Starting \${stack}..."
        \${ENGINE} compose -f "\${compose_file}" pull --ignore-pull-failures 2>/dev/null || true
        \${ENGINE} compose -f "\${compose_file}" up -d --remove-orphans
        echo "[remote] \${stack} is up"
    else
        echo "[remote] WARNING: No compose.yml found for \${stack}, skipping"
    fi
done

echo "[remote] Deployment complete"
REMOTE_SCRIPT

log "Deployment to ${HOST} finished successfully"
