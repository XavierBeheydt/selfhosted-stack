# OpenClaw - Personal AI Agent Gateway

> **Status**: Phase 3 - Testing / Not yet integrated

[OpenClaw](https://openclaw.ai/) is an MIT-licensed, self-hosted AI agent gateway created by Peter Steinberger. It connects your messaging apps to AI models and turns them into an always-on personal assistant that can autonomously execute tasks.

## Philosophy: The Lobster Way

OpenClaw follows the "Lobster Philosophy":

- **Hard on the outside** — local-first, self-hosted, you own your data, aggressive security defaults (DM pairing, allowlists, sandboxed sessions)
- **Soft on the inside** — seamless UX across 20+ messaging channels, voice wake, companion apps, skills ecosystem

The core idea: your AI assistant should live where *you* already are (WhatsApp, Telegram, Slack, Signal...), not behind yet another web UI.

## OpenClaw vs Open WebUI

These two tools are **complementary, not redundant**:

| | Open WebUI | OpenClaw |
|---|---|---|
| **Interface** | Web browser (ChatGPT-like) | Messaging apps (WhatsApp, Telegram, Slack, Discord, Signal, iMessage, Teams, Matrix, IRC, ...) |
| **User type** | Teams, casual users, demos | Power user / personal assistant |
| **Interaction** | Pull — you go to it | Push — always-on, comes to you |
| **Core strength** | RAG, document upload, model switching, multi-user accounts | Autonomous agent loops, tool use, multi-channel inbox, voice wake, device control |
| **Multi-user** | Yes (built-in user management) | Single-user (personal assistant) |
| **GPU needs** | No (connects to Ollama) | No (connects to Ollama or cloud APIs) |

**Use Open WebUI** for team access, RAG document exploration, and model comparison.
**Use OpenClaw** as your personal always-on agent — reachable from your phone, can execute commands, browse the web, manage files, send emails, control devices.

Both connect to the same Ollama instance for local inference.

## Key Features

- **20+ messaging channels** — WhatsApp, Telegram, Slack, Discord, Signal, iMessage (BlueBubbles), Microsoft Teams, Matrix, Google Chat, IRC, LINE, Mattermost, Nostr, and more
- **Autonomous agent loop** — chains tool calls together until a task is complete, without manual intervention
- **Multi-agent routing** — route different channels/accounts to isolated agents with separate sessions
- **Voice Wake + Talk Mode** — wake words on macOS/iOS, continuous voice on Android
- **Live Canvas** — agent-driven visual workspace (A2UI)
- **Skills system** — bundled, managed, and workspace skills with ClawHub registry
- **Companion apps** — macOS menu bar, iOS/Android nodes (camera, screen recording, location)
- **Security defaults** — DM pairing codes, per-channel allowlists, Docker sandboxing for non-main sessions
- **Model agnostic** — any LLM provider (OpenAI, Anthropic, etc.) or local Ollama

## Architecture

```
WhatsApp / Telegram / Slack / Discord / Signal / iMessage / Teams / ...
                 │
                 ▼
┌───────────────────────────────┐
│         OpenClaw Gateway      │
│        (control plane)        │
│      ws://127.0.0.1:18789     │
└──────────────┬────────────────┘
               │
               ├── Pi agent (RPC) ──► Ollama / Cloud LLMs
               ├── CLI (openclaw …)
               ├── WebChat UI
               ├── macOS app
               └── iOS / Android nodes
```

## Planned Configuration

- Gateway running on VPS (always-on, reachable from messaging apps)
- Connected to local Ollama via WireGuard for GPU inference
- Fallback to cloud APIs (Anthropic, OpenAI) when local is unavailable
- Traefik reverse proxy for WebChat/Control UI
- WhatsApp + Telegram channels configured
- Workspace skills for business-specific automation

## References

- [GitHub](https://github.com/openclaw/openclaw)
- [Documentation](https://docs.openclaw.ai/)
- [Docker Compose](https://github.com/openclaw/openclaw/blob/main/docker-compose.yml)
- [Wikipedia](https://en.wikipedia.org/wiki/OpenClaw)
