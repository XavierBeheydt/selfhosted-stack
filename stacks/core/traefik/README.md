# Traefik - Reverse Proxy

Dynamic reverse proxy with automatic TLS certificate management and container
service discovery.

## Features

- Automatic HTTPS via Let's Encrypt
- Docker/Podman label-based service discovery
- Security headers and rate limiting middleware
- Dashboard (optional, protected by basic auth)
- DNSZoner integration for dynamic DNS records

## Quick Start

```bash
# From repository root
cp stacks/core/traefik/.env.example stacks/core/traefik/.env
# Edit .env with your domain and ACME email

just traefik-up
```

## Environment Variables

See [.env.example](.env.example) for all available settings.

## Labels

Add these labels to any service to expose it through Traefik:

```yaml
labels:
  - traefik.enable=true
  - traefik.http.routers.myservice.rule=Host(`myservice.${BASE_DOMAIN}`)
  - traefik.http.routers.myservice.entrypoints=websecure
  - traefik.http.routers.myservice.tls.certresolver=letsencrypt
  - dnszoner.enable=true
  - dnszoner.domain=myservice.${BASE_DOMAIN}
```
