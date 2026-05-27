# Data Flow

This public repository documents the backend and infrastructure layer of an access-control platform. The private dashboard/UI is intentionally excluded.

## ANPR Event Ingestion

1. An ANPR camera sends a multipart webhook request to `POST /webhookcallback`.
2. The Flask application receives XML metadata plus license-plate and detection images.
3. XML fields such as event type, timestamp, plate, vehicle type, confidence, direction, and channel are parsed.
4. Images are validated, converted to WebP, and stored in persistent Docker volumes.
5. Detection metadata is inserted into PostgreSQL.

## Media Serving

1. Nginx mounts the image volumes as read-only.
2. Generated image assets are exposed through static routes.
3. Directory browsing is disabled and missing files return `404`.

## Optional Notifications

The webhook can send email or Telegram notifications when environment variables are configured. Public credentials and chat IDs are not included in this repository.

## Operational Output

The backend turns raw camera webhooks into structured records and image assets that can be consumed by a separate dashboard or operational review workflow.
