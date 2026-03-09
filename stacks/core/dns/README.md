# DNS - CoreDNS + DNSZoner

CoreDNS with dynamic zone management via DNSZoner sidecar.

## Features

- Dynamic DNS zone generation from container labels
- DNSSEC signing
- DNS-over-TLS (DoT) forwarding
- Conditional forwarding for split-horizon DNS
- Health monitoring

## Quick Start

```bash
just up dns
just logs dns
```

## DNSZoner Labels

Add to any service compose to auto-register DNS:

```yaml
labels:
  dnszoner.enable: "true"
  dnszoner.domain: "myservice.example.com"
```

## Configuration

- `config/Corefile` -- CoreDNS configuration
- `dnszoner/` -- Python sidecar project (generates zone files from container labels)
- `.env.example` -- environment variables

## DNSZoner Development

```bash
just dnszoner-test    # run tests
just dnszoner-lint    # run linter
just dnszoner-fmt     # format code
```
