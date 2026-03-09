# TTS - Text-to-Speech

Text-to-speech service. Node assignment TBD based on model requirements
(GPU on Compute node vs CPU-only on Gateway).

## Features

- REST API for text-to-speech conversion
- Multiple voice models
- Streaming audio output

## Quick Start

```bash
just up tts
```

## Candidates

- [Piper](https://github.com/rhasspy/piper) -- fast, CPU-friendly
- [Coqui TTS](https://github.com/coqui-ai/TTS) -- more models, GPU optional
- [OpenedAI Speech](https://github.com/matatonic/openedai-speech) -- OpenAI API compatible
