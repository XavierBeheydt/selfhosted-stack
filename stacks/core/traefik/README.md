# Traefik - Reverse Proxy

Reverse proxy with automatic TLS, routing, and dashboard.

## Features

- Automatic Let's Encrypt TLS certificates
- HTTP to HTTPS redirect
- Dashboard (protected via Authentik forward-auth)
- Docker/Podman provider via socket
- Dynamic configuration via file provider

## Quick Start

```bash
just up traefik
just logs traefik
```

## Configuration

- `config/traefik.yml` -- static configuration
- `config/dynamic/` -- dynamic configuration files
- `.env.example` -- environment variables

## Traefik Labels

Add to any service compose to expose via Traefik:

```yaml
labels:
  traefik.enable: "true"
  traefik.http.routers.myservice.rule: "Host(`myservice.${BASE_DOMAIN}`)"
  traefik.http.routers.myservice.entrypoints: websecure
  traefik.http.routers.myservice.tls.certresolver: letsencrypt
```
