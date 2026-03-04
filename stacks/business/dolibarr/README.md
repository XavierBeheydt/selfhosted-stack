# Dolibarr - ERP/CRM

[Dolibarr](https://www.dolibarr.org/) ERP/CRM with MariaDB backend.

## Quick Start

```bash
cp .env.example .env
# Edit .env with your credentials and domain

just dolibarr-up
# Access at https://erp.example.com
```

## Database Backup & Restore

```bash
# Backup
just dolibarr-backup

# Restore from SQL dump
just dolibarr-restore-db path/to/dump.sql
```

## Environment Variables

See [.env.example](.env.example) for all available settings.
