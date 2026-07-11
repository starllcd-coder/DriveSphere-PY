# Auth Flow

## Endpoints

- `POST /api/auth/login/` (legacy shape)
- `POST /api/v1/auth/login/` (standardized shape)
- `POST /api/auth/register/`
- `POST /api/v1/auth/register/`
- `GET /api/auth/profile/`
- `GET /api/v1/auth/profile/`
- `POST /api/auth/otp/request/`
- `POST /api/v1/auth/otp/request/`
- `POST /api/auth/otp/verify/`
- `POST /api/v1/auth/otp/verify/`

## Login Request

```json
{
  "identifier": "manager@example.com",
  "password": "pass1234"
}
```

## Login Response (Legacy `/api/auth/login/`)

```json
{
  "message": "Login successful.",
  "tokens": {
    "access": "<jwt-access>",
    "refresh": "<jwt-refresh>"
  },
  "user": {
    "id": 1,
    "email": "manager@example.com"
  }
}
```

## Login Response (Versioned `/api/v1/auth/login/`)

```json
{
  "ok": true,
  "message": "Login successful.",
  "data": {
    "tokens": {
      "access": "<jwt-access>",
      "refresh": "<jwt-refresh>"
    },
    "user": {
      "id": 1,
      "email": "manager@example.com"
    }
  }
}
```

## OTP Verify

Request:

```json
{
  "phone": "+971500000000",
  "otp": "123456"
}
```

Success response (v1):

```json
{
  "ok": true,
  "data": {
    "verified": true
  }
}
```

Failure response (v1):

```json
{
  "ok": false,
  "error": "Invalid OTP.",
  "verified": false
}
```

## Notes

- `/api/v1` is the preferred integration path.
- `/api` is kept for backward compatibility with older clients.
- JWT refresh rotation + blacklist is enabled.
