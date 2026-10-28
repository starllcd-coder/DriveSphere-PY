# Environment Variable Reference

## Core Django

- `DJANGO_ENV`: `development|production`
- `DJANGO_DEBUG`: `0|1`
- `DJANGO_SECRET_KEY`: required in production
- `DJANGO_ALLOWED_HOSTS`: comma-separated hosts

## Database

- `DATABASE_URL`: optional PostgreSQL URL; when set, it takes precedence over the `DB_*` settings below
- `DB_ENGINE`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`

## API Reliability and Security

- `API_PAGE_SIZE`
- `API_THROTTLE_ANON`
- `API_THROTTLE_USER`
- `API_THROTTLE_AUTH_LOGIN`
- `API_THROTTLE_OTP_VERIFY`

## Web Login Protection

- `LOGIN_ATTEMPT_LIMIT`
- `LOGIN_ATTEMPT_WINDOW_SECONDS`
- `LOGIN_BLOCK_SECONDS`

## CORS and Cookies

- `CORS_ALLOW_ALL_ORIGINS`
- `CORS_ALLOWED_ORIGINS`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `SESSION_COOKIE_SAMESITE`
- `CSRF_COOKIE_SAMESITE`

## Sensitive Data Encryption

- `DATA_ENCRYPTION_KEY`: used to encrypt sensitive stored configuration fields
- `CENTRAL_CONNECTOR_SECRET`: shared secret for the Central Platform connector; required in production

## OTP and Messaging

- `OTP_DEBUG_RETURN_CODE`
- `OTP_TTL_SECONDS`
- `OTP_RATE_LIMIT_MAX`
- `OTP_RATE_LIMIT_WINDOW_SECONDS`
- `OTP_BLOCK_VOIP`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_FROM`
- `TWILIO_SMS_FROM`
