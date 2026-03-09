# Authentik - Identity Provider

Centralized SSO/OIDC/LDAP identity provider for all services.

## Features

- OIDC/OAuth2 provider for service SSO
- LDAP outpost for legacy service auth
- Traefik forward-auth for services without native OIDC
- User management and group policies
- MFA support

## Quick Start

```bash
just up authentik
```

Access at `https://auth.<BASE_DOMAIN>`.

## Integration

Services connect to Authentik via:
1. **OIDC** (preferred) -- native SSO for compatible services
2. **LDAP** outpost -- for services requiring LDAP auth
3. **Forward-auth** via Traefik -- catch-all for services without auth support

## Initial Setup

1. Start the stack
2. Navigate to `https://auth.<BASE_DOMAIN>/if/flow/initial-setup/`
3. Create the admin account
4. Configure providers and applications for each service
