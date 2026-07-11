# Production Setup Guide

## 1. Prerequisites

- Docker + Docker Compose
- Domain and DNS pointed to the server
- TLS certificate strategy (e.g., reverse proxy + certbot)

## 2. Environment

1. Copy `.env.example` to `.env`.
2. Set production values:
   - `DJANGO_ENV=production`
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY=<strong-random-secret>`
   - `DJANGO_ALLOWED_HOSTS=<your-domain>`
   - Postgres credentials
   - `DATA_ENCRYPTION_KEY=<strong-random-secret>`

## 3. Run Stack

```bash
docker compose up -d --build
```

This starts:
- Django app (`web`)
- Celery worker (`worker`)
- Celery beat scheduler (`beat`)
- Nginx reverse proxy (`nginx`)
- Postgres (`db`)
- Redis (`redis`)

## 4. Validate

- Health check:
  `curl http://<server>/healthz/`
- API:
  `curl http://<server>/api/v1/auth/profile/` (with token)

## 5. Backup and Restore

- Backup:
  `bash infra/scripts/backup.sh`
- Restore:
  `bash infra/scripts/restore.sh <backup-file>`

App-level scheduled jobs (Celery):
- `apps.core.tasks.sync_operational_notifications_task`
- `apps.reports.tasks.generate_scheduled_reports_task`
- `apps.core.tasks.run_automated_backup_task`
- `apps.reports.tasks.run_anomaly_detection_task`

Manual command equivalents:
- `python manage.py sync_operational_notifications`
- `python manage.py generate_scheduled_reports`
- `python manage.py create_system_backup`
- `python manage.py detect_anomalies`
- `python manage.py sync_integrations`

## 6. Hardening Checklist

- Enforce HTTPS at the proxy/load balancer.
- Restrict CORS origins to trusted domains only.
- Disable debug OTP output in production.
- Rotate secrets periodically.
