# Meilisearch - Federated Internal Search

Fast, typo-tolerant search engine indexing data across all services.

## Features

- Instant search with typo tolerance
- Multi-index (Dolibarr, Seafile, photos)
- REST API
- Filterable and faceted search

## Quick Start

```bash
just up meilisearch
```

API at `https://search.${BASE_DOMAIN}`.

## Indexes

Data is fed via n8n automation workflows:
- `dolibarr` -- invoices, proposals, contacts
- `seafile` -- file metadata
- `photos` -- Immich/PhotoPrism photo metadata
- `memories` -- mem0 memory entries
