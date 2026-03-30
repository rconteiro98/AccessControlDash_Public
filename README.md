# AccessControlDash

Public-safe infrastructure for an access-control workflow built around an ANPR webhook, PostgreSQL, and Nginx.

This repository intentionally contains only the shareable backend and infrastructure pieces. The private dashboard/UI service is not included here.

## Included services

- `Webhook`: Flask + Gunicorn webhook that receives ANPR events, stores detections, and can send optional notifications.
- `DB`: PostgreSQL image with the initial schema used by the project.
- `Nginx`: Static file serving for generated image assets.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Default local endpoints:

- Webhook: `http://localhost:5000/webhookcallback`
- Image files: `http://localhost/licenseimage/<filename>` and `http://localhost/detectionimage/<filename>`

## Security notes

- Real credentials, production domains, and personal contact details have been removed from this public repo.
- Secrets must be provided through environment variables.
- Directory browsing for generated images is disabled by default.
- Use a non-default database password before deploying anywhere beyond local development.

## Repository layout

```text
.
|-- DB/
|   |-- Dockerfile
|   |-- init_schema.sql
|   `-- postgres-custom.conf
|-- Nginx/
|   |-- Dockerfile
|   `-- public-assets-nginx.conf
|-- Webhook/
|   |-- Dockerfile
|   |-- anpr_webhook_app.py
|   |-- license_plate_validator.py
|   `-- requirements.txt
|-- .env.example
|-- .gitignore
`-- docker-compose.yml
```

## Notes for public sharing

- The dashboard service referenced in the original project is external to this repository.
- Review `.env.example` and set only the variables you actually need.
- If you enable email or Telegram notifications, keep those secrets only in `.env` or your deployment platform's secret store.
