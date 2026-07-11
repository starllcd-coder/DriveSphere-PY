# DriveSphere Architecture Overview

## Runtime Surfaces

- Web app (Django templates + JS) for operations teams.
- API layer (`/api`, `/api/v1`) for mobile and integrations.
- Desktop shell planned as thin wrapper over web app.

## Backend Structure

- `web/apps/*` contains business domains:
  - `bookings`, `payments`, `fleet`, `customers`, `reports`, `settings_app`, `accounts`.
- `web/api/*` contains API endpoints and serializers.
- `web/config/*` contains settings, URL routing, WSGI/ASGI.

## Data Model Principles

- Branch-scoped operations for multi-branch rental businesses.
- Audit logs for critical actions.
- Sequential document numbering for invoices/receipts/agreements.
- Payment and refund records are immutable event rows.

## Operational Guarantees

- Health endpoint: `/healthz/`.
- JWT auth with refresh rotation + blacklist.
- OTP flow with server-side rate limiting.
- Login attempt throttling for web/API auth.
- Environment-driven security controls (CORS, cookies, secrets).
