# mem0 - AI Memory Service

Persistent per-user AI memory using pgvector for semantic search.
All AI services (Open WebUI, OpenClaw, n8n) share memory through mem0.

## Features

- Per-user memory storage and retrieval
- Semantic search via pgvector embeddings
- REST API for memory CRUD
- Integration with LiteLLM for embeddings

## Quick Start

```bash
just up mem0
```

API available at `http://mem0:8080` (internal) or `https://memory.${BASE_DOMAIN}`.
