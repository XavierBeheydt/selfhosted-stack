# Open WebUI - LLM Chat Interface

Web-based LLM chat interface with RAG, MCP tools, and per-user memory.
Connects to LiteLLM for model access.

## Features

- Chat interface with multiple model support
- RAG (Retrieval-Augmented Generation) with document upload
- MCP (Model Context Protocol) tool integration
- Per-user chat history and settings
- Web search integration

## Quick Start

```bash
just up open-webui
```

Access at `https://chat.${BASE_DOMAIN}`.

## Integration

- Connects to LiteLLM API for all model access
- Authentik SSO for user authentication
- mem0 for persistent per-user memory
