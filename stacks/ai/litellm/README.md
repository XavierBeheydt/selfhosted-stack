# LiteLLM — Unified LLM API Gateway

> **Status**: Phase 3 — Planned

[LiteLLM](https://docs.litellm.ai/) is an open-source proxy that provides a
single OpenAI-compatible API endpoint for 100+ LLM providers. All AI consumers
in the stack (Open WebUI, OpenClaw, n8n) connect through LiteLLM instead of
directly to individual providers.

## Why LiteLLM?

Without a gateway, every consumer must independently configure connections to
Ollama, OpenAI, Anthropic, etc. LiteLLM centralizes this:

```
Open WebUI ─┐
OpenClaw   ─┤──► LiteLLM (:4000) ──┬──► Ollama (local GPU)
n8n        ─┘    (unified API)     ├──► OpenAI
                                    └──► Anthropic
```

## Key Features

- **Unified OpenAI-compatible API** — one endpoint for all providers
- **Caching** — in-memory, Redis, or semantic caching to reduce inference load
- **Cost tracking** — per-user/per-key budget limits and spend monitoring
- **Load balancing** — distribute requests across model replicas
- **Fallbacks** — if Ollama is down, automatically route to a cloud provider
- **Rate limiting** — protect your GPU from overload
- **Admin dashboard** — web UI at `/ui` for model management and monitoring
- **Virtual keys** — issue API keys with per-key quotas and permissions

## Architecture

| Component  | Image                                          | Port |
| :--------- | :--------------------------------------------- | :--- |
| LiteLLM    | `ghcr.io/berriai/litellm-database:main-stable` | 4000 |
| PostgreSQL | `postgres:16-alpine`                           | 5432 |

The `-database` image variant includes Prisma DB migrations for faster startup.

## Quick Start

```bash
# Copy environment file
cp .env.example .env
# Edit .env — set LITELLM_MASTER_KEY and POSTGRES_PASSWORD at minimum

# Start the stack
docker compose up -d

# Verify
curl http://localhost:4000/health/liveliness
# → "I'm alive!"

# Access dashboard
open http://localhost:4000/ui
```

## Configuration

### Models

Edit `config/litellm_config.yaml` to add or remove models. The format is:

```yaml
model_list:
  - model_name: <display-name>
    litellm_params:
      model: <provider>/<model-id>
      api_base: <url>          # for self-hosted (Ollama, vLLM)
      api_key: os.environ/KEY  # for cloud providers
```

Models can also be added at runtime via the dashboard UI when
`STORE_MODEL_IN_DB=True`.

### Connecting Consumers

Point any OpenAI-compatible client to LiteLLM:

```bash
# Example: curl
curl http://litellm:4000/v1/chat/completions \
  -H "Authorization: Bearer sk-your-master-key" \
  -H "Content-Type: application/json" \
  -d '{"model": "llama3", "messages": [{"role": "user", "content": "Hello"}]}'
```

- **Open WebUI**: Set `OPENAI_API_BASE=http://litellm:4000/v1`
- **OpenClaw**: Configure LiteLLM endpoint in provider settings
- **n8n**: Use the OpenAI node with custom base URL `http://litellm:4000/v1`

### Health Endpoints

| Endpoint             | Auth | Purpose                  |
| :------------------- | :--- | :----------------------- |
| `/health/liveliness` | No   | Container liveness probe |
| `/health/readiness`  | No   | DB connection status     |
| `/health`            | Yes  | Full model health check  |

## Environment Variables

See [`.env.example`](.env.example) for all configurable variables.

| Variable             | Required | Description                                 |
| :------------------- | :------- | :------------------------------------------ |
| `LITELLM_MASTER_KEY` | Yes      | Admin API key (must start with `sk-`)       |
| `POSTGRES_PASSWORD`  | Yes      | Database password                           |
| `OLLAMA_API_BASE`    | No       | Ollama URL (default: `http://ollama:11434`) |
| `OPENAI_API_KEY`     | No       | OpenAI API key (if using cloud)             |
| `ANTHROPIC_API_KEY`  | No       | Anthropic API key (if using cloud)          |

## Kubernetes

K8s manifests are in `k8s/base/`. Deploy with:

```bash
kubectl apply -k k8s/base/
```

## References

- [Documentation](https://docs.litellm.ai/)
- [GitHub](https://github.com/BerriAI/litellm)
- [Docker Hub](https://hub.docker.com/r/berriai/litellm)
- [Config reference](https://docs.litellm.ai/docs/proxy/configs)
