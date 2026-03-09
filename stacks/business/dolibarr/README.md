# Dolibarr - ERP/CRM

Full-featured ERP/CRM backed by MariaDB.

## Features

- Invoicing, proposals, orders
- CRM contacts and leads
- Accounting and bank reconciliation
- Inventory management
- Project management

## Quick Start

```bash
just up dolibarr
```

Access at `https://erp.<BASE_DOMAIN>`.

## Database

MariaDB 11 with automatic health checks. Backup via:

```bash
just dolibarr-backup
```
