# WireGuard - VPN Gateway

WireGuard VPN with wg-easy web UI for peer management. Hub-spoke topology
with VPS as the hub.

## Features

- wg-easy web UI for adding/removing peers
- Hub-spoke topology (VPS routes all traffic)
- QR code generation for mobile clients
- Automatic peer configuration

## Quick Start

```bash
just up wireguard
```

Access the management UI at `https://wg.<BASE_DOMAIN>`.

## Network Topology

```
[Client] --WireGuard--> [VPS Hub] --WireGuard--> [Local PC]
                              |
                         All services
                         accessible via
                         internal DNS
```

## Peer Scripts

```bash
# Generate WireGuard keys
./scripts/genkeys.sh

# Generate peer config
./scripts/genconfig.sh <peer-name> <peer-ip>
```
