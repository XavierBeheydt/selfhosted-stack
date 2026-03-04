# WireGuard - VPN Gateway

WireGuard VPN gateway using [wg-easy](https://github.com/wg-easy/wg-easy)
for personal device access to the private service network.

## Purpose

This stack provides VPN access for devices (iPhone, laptop, etc.) to services
running on the private cluster network. It is **separate** from the K3s
inter-node WireGuard mesh which is handled natively by K3s Flannel.

### Network Architecture

```
Internet Devices (iPhone, Laptop)
        │
        │ WireGuard UDP :51820
        ▼
┌──────────────┐
│   wg-easy    │ VPN Gateway (10.13.13.0/24)
│   (VPS)      │
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────┐
│  K3s Cluster Network             │
│  Pods: 10.42.0.0/16             │
│  Services: 10.43.0.0/16         │
│  ┌─────┐  ┌─────┐  ┌─────┐     │
│  │ VPS │──│ PC  │──│ ... │     │
│  └─────┘  └─────┘  └─────┘     │
│  (K3s native WireGuard mesh)    │
└──────────────────────────────────┘
```

## Quick Start

```bash
# Generate password hash
docker run --rm ghcr.io/wg-easy/wg-easy wgpw 'your-password'

# Configure
cp .env.example .env
# Set WG_HOST and WG_PASSWORD_HASH in .env

# Start
just wireguard-up

# Access web UI at https://vpn.example.com
# Download client configs for your devices
```

## K3s WireGuard Native

For inter-node communication, K3s uses WireGuard natively. Install K3s with:

```bash
# Server node (VPS)
curl -sfL https://get.k3s.io | sh -s - server \
  --flannel-backend=wireguard-native \
  --node-external-ip=<VPS_PUBLIC_IP>

# Agent node (local PC)
curl -sfL https://get.k3s.io | sh -s - agent \
  --server https://<VPS_IP>:6443 \
  --token <K3S_TOKEN> \
  --node-external-ip=<PC_PUBLIC_IP>
```
