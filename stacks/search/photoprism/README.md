# PhotoPrism stack

This stack provides a self-hosted PhotoPrism deployment suitable for testing and small personal libraries.

Files
- `compose.yml` — Docker Compose for quick testing
- `.env.example` — environment template

Quick start

1. Copy `.env.example` to `.env` and adjust values (hostname, passwords).
2. Start with `docker compose up -d` from this directory.
3. Upload or mount your photo library into the `photoprism-originals` volume (or bind mount to `/photoprism/originals`).

Notes
- This is a minimal test stack — for production follow PhotoPrism docs about scaling, using external storage and optimizing ML models (TensorFlow, Ollama, etc.).
- The stack joins the `proxy-frontend` external network so Traefik in the repo can expose it — ensure the network exists.
