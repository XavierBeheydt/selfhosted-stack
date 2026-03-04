# Mem0 — Persistent AI Memory Layer

> **Status**: Phase 3 — Planned

[Mem0](https://docs.mem0.ai/) is an open-source memory layer for LLM
applications. It gives your AI services long-term memory about users,
preferences, and conversation context — shared across all AI consumers in the
stack.

## Why Mem0?

Without a shared memory layer, each AI service (Open WebUI, OpenClaw, n8n)
maintains its own isolated context. Mem0 centralizes this:

```
Open WebUI ─┐                    ┌── pgvector (embeddings)
OpenClaw   ─┤──► Mem0 API ──────┤
n8n        ─┘   (:8000)         └── Neo4j (entity graph)
```

When you tell OpenClaw "I prefer dark roast coffee", Open WebUI and n8n
workflows can retrieve that preference too.

## Key Features

- **Persistent memory** — stores user preferences, traits, and facts across sessions
- **Shared across services** — all AI consumers read/write the same memory store
- **Vector search** — find relevant memories by semantic similarity (pgvector)
- **Graph memory** — entity/relationship tracking via Neo4j (optional)
- **Per-user isolation** — memories are scoped by `user_id`, `agent_id`, or `run_id`
- **Memory history** — track how memories evolve over time
- **REST API** — simple HTTP endpoints for store, search, update, delete
- **Runtime reconfiguration** — swap LLM/embedder/vector store via `/configure` endpoint
- **OpenClaw integration** — documented integration guide available

## Architecture

| Component | Image                    | Port | Purpose                   |
| :-------- | :----------------------- | :--- | :------------------------ |
| Mem0 API  | `mem0/mem0-api-server`   | 8000 | Memory management API     |
| pgvector  | `ankane/pgvector:v0.5.1` | 5432 | Vector embeddings storage |
| Neo4j     | `neo4j:5.26.4`           | 7474 | Entity/relationship graph |

Neo4j is optional — remove it from `compose.yml` if you only need vector-based
memory search without graph relationships.

## Quick Start

```bash
# Copy environment file
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and POSTGRES_PASSWORD at minimum

# Start the stack
docker compose up -d

# Verify
curl http://localhost:8888/docs
# → OpenAPI/Swagger UI

# Store a memory
curl -X POST http://localhost:8888/memories \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "I love hiking in the mountains"}],
    "user_id": "xavier"
  }'

# Search memories
curl -X POST http://localhost:8888/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What does Xavier enjoy doing?",
    "user_id": "xavier"
  }'
```

## API Reference

| Method   | Endpoint                 | Description                    |
| :------- | :----------------------- | :----------------------------- |
| `POST`   | `/memories`              | Store memories from messages   |
| `GET`    | `/memories`              | List all memories for a user   |
| `GET`    | `/memories/{id}`         | Get a specific memory          |
| `POST`   | `/search`                | Search memories by query       |
| `PUT`    | `/memories/{id}`         | Update a memory                |
| `GET`    | `/memories/{id}/history` | Get memory edit history        |
| `DELETE` | `/memories/{id}`         | Delete a specific memory       |
| `DELETE` | `/memories`              | Delete all memories for a user |
| `POST`   | `/reset`                 | Reset all memories (wipe)      |
| `POST`   | `/configure`             | Reconfigure LLM/embedder/store |

Full interactive docs at `http://<host>:8888/docs` (Swagger UI).

## Using with Local Models (Ollama)

Mem0 defaults to OpenAI for LLM and embeddings. To use Ollama instead,
reconfigure at runtime:

```bash
curl -X POST http://localhost:8888/configure \
  -H "Content-Type: application/json" \
  -d '{
    "version": "v1.1",
    "llm": {
      "provider": "ollama",
      "config": {
        "model": "llama3",
        "ollama_base_url": "http://ollama:11434"
      }
    },
    "embedder": {
      "provider": "ollama",
      "config": {
        "model": "nomic-embed-text",
        "ollama_base_url": "http://ollama:11434"
      }
    }
  }'
```

Alternatively, route through LiteLLM by configuring the OpenAI-compatible
endpoint to point to LiteLLM instead of OpenAI directly.

## Environment Variables

See [`.env.example`](.env.example) for all configurable variables.

| Variable                   | Required | Description                                  |
| :------------------------- | :------- | :------------------------------------------- |
| `OPENAI_API_KEY`           | Yes*     | LLM + embeddings key (*or use Ollama)        |
| `POSTGRES_PASSWORD`        | Yes      | pgvector database password                   |
| `NEO4J_PASSWORD`           | No       | Neo4j graph password (default: `mem0graph`)  |
| `POSTGRES_COLLECTION_NAME` | No       | Vector collection name (default: `memories`) |

## Kubernetes

K8s manifests are in `k8s/base/`. Deploy with:

```bash
kubectl apply -k k8s/base/
```

## References

- [Documentation](https://docs.mem0.ai/)
- [GitHub](https://github.com/mem0ai/mem0)
- [Docker Hub](https://hub.docker.com/r/mem0/mem0-api-server)
- [OpenClaw integration](https://docs.mem0.ai/integrations/openclaw)
- [API reference](https://docs.mem0.ai/api-reference)
