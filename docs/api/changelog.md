# API Changelog

## 2026-03-26

### Added

- Introduced versioned API base path support at `/api/v1/...`.
- Added standardized `/api/v1` response envelope:
  - Success: `{"ok": true, "message"?: "...", "data"?: {...}}`
  - Error: `{"ok": false, "error": "...", "details"?: {...}}`
- Added standardized paginated list shape for `/api/v1` list endpoints.
- Added payment/refund idempotency support:
  - `Idempotency-Key` header
  - `idempotency_key` body field
- Added web-safe aliases for web UI endpoints under `/web-api/...` for route-collision protection.

### Changed

- Standardized `/api/v1` behavior for:
  - Auth
  - Bookings
  - Payments
  - Vehicles (list/detail/search/reviews)
  - Profile
  - Support
  - Devices
  - Documents
  - Notifications
- Preserved legacy `/api` response shapes for backward compatibility.
- Improved booking conflict handling to return clean `400` API error instead of unhandled server exception.
- Improved reports overview KPI rendering and collection-rate calculation logic.

### Security

- Enabled login attempt throttling for web and API auth flows.
- Added OTP verify throttling controls.
- Enabled JWT refresh rotation + blacklist.
- Hardened environment-based security settings (CORS/cookies/secret enforcement).
- Added encrypted-at-rest storage for sensitive database profile passwords.

### Payment Integrity

- Enforced refund rules:
  - Refund only allowed on `PAID` payments.
  - Total refunded amount cannot exceed original payment amount.
- Added idempotent replay-safe create behavior for payments/refunds.

### Infra and Ops

- Added health check endpoint: `/healthz/`.
- Replaced infrastructure placeholders with working Docker/Nginx/Gunicorn/backup-restore files.

### Tests

- Added and expanded regression tests for:
  - Auth login and OTP verification
  - Booking overlap conflict behavior
  - Payment idempotency success and payload conflict
  - Over-refund rejection
  - `/api/v1` standardized response shapes
