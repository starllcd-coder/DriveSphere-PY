# API Endpoints

## Base Paths

- Legacy compatibility: `/api/...`
- Standardized versioned API: `/api/v1/...`

Versioned response contract (`/api/v1`):
- Success: `{"ok": true, "message"?: string, "data"?: object, ...}`
- Error: `{"ok": false, "error": string, "details"?: object, ...}`
- Paginated list: `{"ok": true, "data": [...], "pagination": {...}}`

## Authentication

- `POST /api/auth/login/` and `POST /api/v1/auth/login/`
- `POST /api/auth/register/` and `POST /api/v1/auth/register/`
- `GET /api/auth/profile/` and `GET /api/v1/auth/profile/`
- `POST /api/auth/otp/request/` and `POST /api/v1/auth/otp/request/`
- `POST /api/auth/otp/verify/` and `POST /api/v1/auth/otp/verify/`

## Bookings

- `GET /api/bookings/` and `GET /api/v1/bookings/`
- `POST /api/bookings/create/` and `POST /api/v1/bookings/create/`
- `GET /api/bookings/<id>/` and `GET /api/v1/bookings/<id>/`

Notes:
- Booking overlap conflicts return `400` with an error message.
- `/api/v1/...` endpoints use standardized error envelope.

## Payments

- `GET /api/payments/` and `GET /api/v1/payments/`
- `POST /api/payments/create/` and `POST /api/v1/payments/create/`
- `GET /api/payments/<id>/` and `GET /api/v1/payments/<id>/`
- `POST /api/payments/refunds/create/` and `POST /api/v1/payments/refunds/create/`

### Idempotency

Payment/refund creation supports idempotency using either:
- `Idempotency-Key` request header
- `idempotency_key` field in request body

Behavior:
- Same key + same payload: returns existing resource (replay-safe).
- Same key + different payload: returns `400`.

### Refund Rules

- Refund allowed only for `PAID` payments.
- Total refunded amount cannot exceed original payment amount.

## Vehicles (Web-safe aliases available)

- `GET /api/vehicles/` and `GET /api/v1/vehicles/`
- `POST /api/vehicles/<id>/telematics/ingest/` and `POST /api/v1/vehicles/<id>/telematics/ingest/`
- `GET /api/vehicles/<id>/telematics/metrics/?days=7` and `GET /api/v1/vehicles/<id>/telematics/metrics/?days=7`
- Web app aliases: `GET /web-api/vehicles/`
- Create/update/delete and document/photo endpoints are available under both `/api/...` and `/web-api/...` paths.

## Profile, Support, Devices, Notifications, Documents

- Profile:
  - `GET /api/profile/`, `PUT /api/profile/update/`
  - `GET /api/v1/profile/`, `PUT /api/v1/profile/update/`
- Support:
  - `GET|POST /api/support/messages/`
  - `GET|POST /api/v1/support/messages/`
- Devices:
  - `POST /api/devices/register/`
  - `POST /api/v1/devices/register/`
- Notifications:
  - `GET /api/notifications/`
  - `POST /api/notifications/<id>/read/`
  - `DELETE /api/notifications/<id>/delete/`
  - Same routes under `/api/v1/...`
- Documents:
  - `GET /api/documents/`, `POST /api/documents/upload/`, `GET|DELETE /api/documents/<id>/`
  - Same routes under `/api/v1/...`

## Integrations

- `GET|POST /api/integrations/profiles/` and `/api/v1/integrations/profiles/`
- `POST /api/integrations/sync/run/` and `/api/v1/integrations/sync/run/`
- `GET /api/integrations/sync/logs/` and `/api/v1/integrations/sync/logs/`

## Reports

- `GET /api/reports/overview/`
- `GET /api/reports/overview/table/`
- `GET /api/reports/revenue/`
- `GET /api/reports/financial/`
- `GET /api/reports/fleet/`
- `GET /api/reports/maintenance/`
- `GET /api/reports/customers/`
- `GET /api/reports/insights/`
- `GET /api/reports/anomalies/`
- `GET /api/reports/anomalies/?scan=1`
- `POST /api/reports/anomalies/<id>/resolve/`
- `POST /api/reports/accounting/export/?provider=QUICKBOOKS&type=PAYMENTS&period=monthly`
