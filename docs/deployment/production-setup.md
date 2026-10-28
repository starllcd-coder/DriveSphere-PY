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

## 7. Deploy to Render with the Existing SQLite Data

The app supports Render PostgreSQL through `DATABASE_URL`. SQLite on a Render web
service is not a suitable production database because its filesystem is ephemeral.
Create a Render PostgreSQL database and migrate the existing SQLite data into it.

### Configure the Render service

1. In Render, create a PostgreSQL database in the same region as the web service.
2. Create a **Web Service** for this GitHub repository. Select the Docker runtime
   and leave the Dockerfile path as `./Dockerfile`.
3. Set these environment variables on the web service:
   - `DJANGO_SETTINGS_MODULE=config.settings.prod`
   - `DJANGO_ENV=production`
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY`: keep the current value if the existing
     `DATA_ENCRYPTION_KEY` is not set; otherwise use a private random value
   - `DJANGO_ALLOWED_HOSTS`: the Render hostname, without `https://`
   - `DATA_ENCRYPTION_KEY`: keep the current value if one is set; otherwise
     leave it unset
   - `CENTRAL_CONNECTOR_SECRET`: a private, strong value (keep the current
     value if an existing platform integration uses it)
   - `DATABASE_URL`: Render PostgreSQL's **Internal Database URL** (use Render's
     database-to-service connection option if available)
   - `OTP_DEBUG_RETURN_CODE=0`
   - `USE_REDIS_CACHE=0` for a web-only deployment without Redis. To use Redis
     caching/background workers, provision Render Key Value and configure its
     private URL and a separate worker service.
4. Deploy the service. The Docker startup applies migrations and collects static
   files before starting Gunicorn.
5. In the web service's Shell, create your own administrator account:
   `python manage.py createsuperuser --settings=config.settings.prod`

Do not set `DATABASE_URL` to the SQLite file or commit database URLs and secret
values to the repository. The production container no longer creates the
hard-coded demo administrator account.

### Copy the current SQLite data

Take a backup of `web/db.sqlite3` first. From the project root, prepare a
working Python environment (this also repairs a virtual environment copied from
another computer):

```powershell
py -3.12 -m venv --clear web\.venv
.\web\.venv\Scripts\python.exe -m pip install -r web\requirements\dev.txt
```

Export application data before pointing the app at PostgreSQL:

```powershell
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
$env:DB_ENGINE = "django.db.backends.sqlite3"
$env:DB_NAME = (Resolve-Path .\web\db.sqlite3).Path
$fixture = Join-Path $env:TEMP "drivesphere-data.json"
.\web\.venv\Scripts\python.exe web\manage.py dumpdata `
  --natural-foreign --natural-primary `
  --exclude contenttypes --exclude auth.permission `
  --exclude admin.logentry --exclude sessions.session `
  --exclude token_blacklist `
  --output $fixture
```

If `DATA_ENCRYPTION_KEY` is set in the current installation, use that exact
value on Render. If it is unset, keep the same `DJANGO_SECRET_KEY`; otherwise
previously encrypted integration credentials may no longer decrypt.

Set `DATABASE_URL` in the current PowerShell process to the Render database's
**External Database URL** (keep the URL private). Then run migrations and import
the fixture:

```powershell
$secureUrl = Read-Host "Render External Database URL" -AsSecureString
$env:DATABASE_URL = (New-Object System.Net.NetworkCredential("", $secureUrl)).Password
.\web\.venv\Scripts\python.exe web\manage.py migrate --settings=config.settings.prod
.\web\.venv\Scripts\python.exe web\manage.py loaddata $fixture --settings=config.settings.prod
Remove-Item Env:DATABASE_URL
Remove-Item Env:DB_ENGINE, Env:DB_NAME -ErrorAction SilentlyContinue
Remove-Item $fixture
```

Import only into a new or empty Render database; loading the same fixture twice
can create duplicate records. Verify the imported users and application data
before directing users to the new service. Treat the fixture as sensitive: it
may contain personal information and credential hashes, and the commands above
remove it after a successful import. For a failed import, inspect the error
before retrying rather than loading into a partially populated database.
