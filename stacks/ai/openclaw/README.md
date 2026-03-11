# OpenClaw - AI Coding Agent

Personal AI coding agent. Single instance, accessible via WireGuard.
Connects to both nodes for development tasks.

## Features

- AI-powered coding assistance
- Access to all nodes via WireGuard
- Integration with LiteLLM for model routing
- Single instance, personal use

## Quick Start

```bash
just up openclaw
```

Access at `https://claw.${BASE_DOMAIN}`.

## Architecture

One instance connects to all machines over WireGuard.
No need for per-device instances -- the agent reaches any host
via the VPN mesh.
