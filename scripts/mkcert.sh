#!/usr/bin/env bash
# Copyright (c) 2026 Xavier Beheydt <xavier.beheydt@gmail.com>
#
# Simple helper to generate a self-signed X.509 certificate (dev use).
#
# Behaviour:
# - Generates a 2048-bit RSA key and a self-signed certificate using OpenSSL.
# - Sets SAN from the provided host (CN is set to the same value).
# - Creates parent directories and writes files directly (overwrites existing files).
# - Minimal validation is performed; this is not suitable for public/production TLS.
#
# Usage: see `--help` in the script. Environment variables (CERT_HOST, KEY_OUT,
# CERT_OUT, DAYS) can also be used instead of flags.

set -euo pipefail
SCRIPT_NAME=$(basename -- "$0")

# --- Defaults ---
CERT_HOST="${CERT_HOST:-}"
KEY_OUT="${KEY_OUT:-stacks/core/traefik/certs/local.key}"
CERT_OUT="${CERT_OUT:-stacks/core/traefik/certs/local.crt}"
DAYS="${DAYS:-365}"

# --- Helpers ---
log() { printf "[%s] %s\n" "$SCRIPT_NAME" "$*"; }
err() {
  printf "[%s] ERROR: %s\n" "$SCRIPT_NAME" "$*" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: $SCRIPT_NAME [options] [cert-host]

Generate a self-signed X.509 certificate with SAN.

Options:
  --cert-host <host>   Common name / SAN   (env: CERT_HOST)
  --key-out <path>     Private key output  (env: KEY_OUT,  default: $KEY_OUT)
  --cert-out <path>    Certificate output  (env: CERT_OUT, default: $CERT_OUT)
  --days <n>           Validity in days    (env: DAYS,     default: $DAYS)
  -h, --help           Show this help

Examples:
  $SCRIPT_NAME '*.docker.localhost'
  $SCRIPT_NAME --cert-host '*.docker.localhost' --days 730
EOF
}

# --- Arg parsing ---
while [[ $# -gt 0 ]]; do
  case "$1" in
  --cert-host)
    shift
    CERT_HOST="$1"
    ;;
  --cert-host=*) CERT_HOST="${1#*=}" ;;
  --key-out)
    shift
    KEY_OUT="$1"
    ;;
  --key-out=*) KEY_OUT="${1#*=}" ;;
  --cert-out)
    shift
    CERT_OUT="$1"
    ;;
  --cert-out=*) CERT_OUT="${1#*=}" ;;
  --days)
    shift
    DAYS="$1"
    ;;
  --days=*) DAYS="${1#*=}" ;;
  -h | --help)
    usage
    exit 0
    ;;
  --)
    shift
    break
    ;;
  -*) err "Unknown option: $1" ;;
  *) [ -z "$CERT_HOST" ] && CERT_HOST="$1" || err "Unexpected argument: $1" ;;
  esac
  shift
done

[ -z "$CERT_HOST" ] && {
  usage
  err "--cert-host is required"
}

# --- Checks ---
command -v openssl >/dev/null 2>&1 || err "openssl is not installed"

# --- Main ---
log "host=$CERT_HOST  key=$KEY_OUT  cert=$CERT_OUT  days=$DAYS"

mkdir -p "$(dirname "$KEY_OUT")" "$(dirname "$CERT_OUT")"

CFG=$(mktemp /tmp/mkcert.XXXXXX)
trap 'rm -f "$CFG"' EXIT

cat >"$CFG" <<EOF
[req]
prompt             = no
default_bits       = 2048
default_md         = sha256
distinguished_name = dn
x509_extensions    = v3_req

[dn]
CN = $CERT_HOST

[v3_req]
subjectAltName = DNS:$CERT_HOST
EOF

openssl req -x509 -nodes -days "$DAYS" -newkey rsa:2048 \
  -keyout "$KEY_OUT" -out "$CERT_OUT" -config "$CFG" 2>/dev/null ||
  err "openssl failed to generate certificate"

chmod 600 "$KEY_OUT"
chmod 644 "$CERT_OUT"

# --- Verify ---
openssl x509 -noout -subject -in "$CERT_OUT" 2>/dev/null || err "certificate is invalid"
openssl rsa -check -noout -in "$KEY_OUT" 2>/dev/null || err "private key is invalid"

log "Done — cert: $CERT_OUT  key: $KEY_OUT"
