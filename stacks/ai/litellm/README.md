# LiteLLM - API Router/Aggregator

Unified API gateway that routes AI requests to multiple providers.
Routes to local Ollama over WireGuard for GPU inference, and to cloud
providers (OpenRouter, GitHub Copilot, etc.) for external models.

## Features

- OpenAI-compatible API proxy
- Multi-provider routing (Ollama, OpenRouter, Azure, GitHub Copilot)
- API key management and rate limiting
- Cost tracking per model/provider
- Fallback chains (if provider A fails, try B)
- Per-user memory integration via mem0

## Quick Start

```bash
just up litellm
```

API available at `https://ai.${BASE_DOMAIN}`.

## Provider Configuration

Edit `config/litellm_config.yaml` to add providers:

```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openrouter/openai/gpt-4
      api_key: os.environ/OPENROUTER_API_KEY
  - model_name: llama3
    litellm_params:
      model: ollama/llama3.1:8b
      api_base: http://<compute-node-wg-ip>:11434
```
