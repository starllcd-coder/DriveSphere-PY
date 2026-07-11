# DriveSphere

DriveSphere is a multi-surface rental operations platform (web, mobile, desktop shell) focused on bookings, fleet, payments, reporting, and operational reliability.

## Quick Start (Local)

1. Copy env file:
   `cp .env.example .env`
2. Create venv and install:
   `cd web && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements/dev.txt`
3. Run migrations:
   `python manage.py migrate`
4. Start server:
   `python manage.py runserver`

## API Versions

- Legacy: `/api/...` (existing clients)
- Standardized: `/api/v1/...` (consistent success/error + pagination structure)

## Production

Use Docker Compose and deployment docs:
- `docker-compose.yml`
- `docs/deployment/production-setup.md`
- `docs/deployment/env-reference.md`

## Core Docs

- Architecture: `docs/architecture-overview.md`
- API auth flow: `docs/api/auth-flow.md`
- Endpoint reference: `docs/api/endpoints.md`
- Contribution process: `CONTRIBUTING.md`
