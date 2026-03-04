# DNS - CoreDNS + DNSZoner

Dynamic DNS service using CoreDNS with automatic zone file generation via
DNSZoner. DNSZoner discovers running containers by inspecting Docker/Podman
labels and generates RFC 1035-compliant zone files.

## How It Works

1. **DNSZoner** watches the container engine API for containers with
   `dnszoner.enable=true` labels
2. For each labeled container, it reads `dnszoner.domain=<fqdn>` to determine
   the DNS record
3. Zone files are generated and written to a shared volume
4. **CoreDNS** auto-reloads zone files every 10 seconds

## Container Labels

Add these labels to any service to register a DNS record:

```yaml
labels:
  - dnszoner.enable=true           # Required: enable discovery
  - dnszoner.domain=app.example.com # Required: FQDN for the record
  - dnszoner.type=A                # Optional: record type (default: A)
  - dnszoner.ttl=300               # Optional: TTL in seconds
  - dnszoner.network=proxy-frontend # Optional: preferred Docker network
```

## Quick Start

```bash
just dns-up
# Verify
dig @localhost -p 53 dns.example.com
```

## DNSZoner Development

See [dnszoner/](dnszoner/) for the Python project. Develop with:

```bash
just dnszoner-install   # Install dev dependencies
just dnszoner-test      # Run tests
just dnszoner-lint      # Lint
```
