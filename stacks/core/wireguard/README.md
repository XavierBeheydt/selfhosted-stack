# WireGuard - VPN Gateway

WireGuard VPN with wg-easy web UI for peer management. Hub-spoke topology
with Gateway as the hub.

## Features

- wg-easy web UI for adding/removing peers
- Hub-spoke topology (Gateway routes all traffic)
- QR code generation for mobile clients
- Automatic peer configuration

## Quick Start

```bash
just up wireguard
```

Access the management UI at `https://wg.<BASE_DOMAIN>`.

## Network Topology

```
[Client] --WireGuard--> [Gateway Hub] --WireGuard--> [Compute]
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
