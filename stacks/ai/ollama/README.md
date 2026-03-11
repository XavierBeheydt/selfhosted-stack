# Ollama - LLM Inference

Local LLM inference server. Runs on the Compute node with GPU.
Accessed by LiteLLM over WireGuard.

## Features

- GPU-accelerated inference (NVIDIA CUDA)
- REST API compatible with OpenAI format
- Model management (pull, list, delete)
- Concurrent request handling

## Quick Start

```bash
just up ollama
```

API available at `http://<compute-node-ip>:11434`.

## Models

```bash
# Pull a model
podman exec ollama ollama pull llama3.1:8b

# List models
podman exec ollama ollama list
```

## GPU Requirements

- NVIDIA GPU with CUDA support
- nvidia-container-toolkit installed
- At least 8GB VRAM for 7B models, 24GB for 70B quantized
