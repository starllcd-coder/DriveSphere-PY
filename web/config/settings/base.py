import logging
import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(
    os.getenv("DRIVESPHERE_BASE_DIR", str(Path(__file__).resolve().parents[2]))
)  # /web by default

DJANGO_ENV = os.getenv("DJANGO_ENV", "development").strip().lower()
IS_PRODUCTION = DJANGO_ENV in {"production", "prod"}

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"

if IS_PRODUCTION and SECRET_KEY == "dev-secret-key-change-me":
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",

    # Local
    "apps.core",
    "apps.accounts",
    "apps.settings_app",
    "apps.dashboard",

    # Chunk 2
    "apps.fleet",
    "apps.customers",

    # Chunk 3
    "apps.bookings",

    # Chunk 4
    "apps.payments",
    "apps.maintenance",
    "apps.reports",
    "apps.documents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    "apps.core.middleware.ActiveBranchMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.drivesphere_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DB_NAME", str(BASE_DIR / "db.sqlite3")),
        "USER": os.getenv("DB_USER", ""),
        "PASSWORD": os.getenv("DB_PASSWORD", ""),
        "HOST": os.getenv("DB_HOST", ""),
        "PORT": os.getenv("DB_PORT", ""),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Muscat"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "apps.accounts.auth_backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/dashboard/"
LOGOUT_REDIRECT_URL = "/login/"

ACTIVE_BRANCH_SESSION_KEY = "active_branch_id"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "api.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": int(os.getenv("API_PAGE_SIZE", "25")),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "EXCEPTION_HANDLER": "api.exceptions.standard_exception_handler",
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("API_THROTTLE_ANON", "60/minute"),
        "user": os.getenv("API_THROTTLE_USER", "300/minute"),
        "auth_login": os.getenv("API_THROTTLE_AUTH_LOGIN", "10/minute"),
        "otp_verify": os.getenv("API_THROTTLE_OTP_VERIFY", "20/minute"),
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=12),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "0") == "1"
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^http://localhost:\d+$",
    r"^http://127\.0\.0\.1:\d+$",
    r"^http://0\.0\.0\.0:\d+$",
]
if DEBUG and not CORS_ALLOWED_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

# HyperPay (KSA/MENA)
HYPERPAY_BASE_URL = os.getenv("HYPERPAY_BASE_URL", "")
HYPERPAY_ENTITY_ID = os.getenv("HYPERPAY_ENTITY_ID", "")
HYPERPAY_ACCESS_TOKEN = os.getenv("HYPERPAY_ACCESS_TOKEN", "")

# OTP via Twilio (WhatsApp first, SMS fallback)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")
TWILIO_SMS_FROM = os.getenv("TWILIO_SMS_FROM", "")
OTP_TTL_SECONDS = int(os.getenv("OTP_TTL_SECONDS", "90"))
OTP_RATE_LIMIT_MAX = int(os.getenv("OTP_RATE_LIMIT_MAX", "3"))
OTP_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("OTP_RATE_LIMIT_WINDOW_SECONDS", "600"))
OTP_BLOCK_VOIP = os.getenv("OTP_BLOCK_VOIP", "1") == "1"
OTP_DEBUG_RETURN_CODE = DEBUG and (os.getenv("OTP_DEBUG_RETURN_CODE", "1") == "1")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "noreply@drivesphere.local")

# Web login brute-force controls
LOGIN_ATTEMPT_LIMIT = int(os.getenv("LOGIN_ATTEMPT_LIMIT", "8"))
LOGIN_ATTEMPT_WINDOW_SECONDS = int(os.getenv("LOGIN_ATTEMPT_WINDOW_SECONDS", "900"))
LOGIN_BLOCK_SECONDS = int(os.getenv("LOGIN_BLOCK_SECONDS", "900"))

# At-rest encryption for sensitive settings data
DATA_ENCRYPTION_KEY = os.getenv("DATA_ENCRYPTION_KEY", "")

# Cookie/session hardening
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "1" if IS_PRODUCTION else "0") == "1"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "1" if IS_PRODUCTION else "0") == "1"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SAMESITE = os.getenv("CSRF_COOKIE_SAMESITE", "Lax")
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Cache layer (Redis in production-ready mode, local-memory fallback)
USE_REDIS_CACHE = os.getenv("USE_REDIS_CACHE", "1" if IS_PRODUCTION else "0") == "1"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1")

if USE_REDIS_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
            "KEY_PREFIX": "drivesphere",
            "TIMEOUT": int(os.getenv("DEFAULT_CACHE_TTL", "300")),
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "drivesphere-default",
            "TIMEOUT": int(os.getenv("DEFAULT_CACHE_TTL", "300")),
        }
    }

# Celery / background jobs
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
CELERY_BEAT_SCHEDULE = {
    "sync-operational-notifications-hourly": {
        "task": "apps.core.tasks.sync_operational_notifications_task",
        "schedule": int(os.getenv("CELERY_SYNC_NOTIFICATIONS_MINUTES", "60")) * 60,
    },
    "generate-scheduled-reports-daily": {
        "task": "apps.reports.tasks.generate_scheduled_reports_task",
        "schedule": int(os.getenv("CELERY_DAILY_REPORTS_HOURS", "24")) * 3600,
    },
    "automated-backup-daily": {
        "task": "apps.core.tasks.run_automated_backup_task",
        "schedule": int(os.getenv("CELERY_BACKUP_HOURS", "24")) * 3600,
    },
    "detect-anomalies-every-6-hours": {
        "task": "apps.reports.tasks.run_anomaly_detection_task",
        "schedule": int(os.getenv("CELERY_ANOMALY_HOURS", "6")) * 3600,
    },
    "sync-external-integrations-every-6-hours": {
        "task": "apps.settings_app.tasks.sync_integrations_task",
        "schedule": int(os.getenv("CELERY_INTEGRATIONS_HOURS", "6")) * 3600,
    },
}

# Error monitoring (optional)
SENTRY_DSN = os.getenv("SENTRY_DSN", "").strip()
SENTRY_TRACES_SAMPLE_RATE = float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.0"))
SENTRY_PROFILES_SAMPLE_RATE = float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.0"))
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            environment=DJANGO_ENV,
            send_default_pii=False,
            traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE,
            profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE,
        )
    except Exception as exc:  # pragma: no cover - optional integration path
        logging.getLogger(__name__).warning("Sentry init skipped: %s", exc)

# Central Platform connector integration
CENTRAL_PLATFORM_URL = os.getenv("CENTRAL_PLATFORM_URL", "http://127.0.0.1:8000")
CENTRAL_CONNECTOR_SECRET = os.getenv("CENTRAL_CONNECTOR_SECRET", "")
CENTRAL_CONNECTOR_SIGNED = os.getenv("CENTRAL_CONNECTOR_SIGNED", "0") == "1"
CENTRAL_TENANT_CODE = os.getenv("CENTRAL_TENANT_CODE", "")
CENTRAL_MODULE_CODE = os.getenv("CENTRAL_MODULE_CODE", "drivesphere")

if IS_PRODUCTION:
    if not any(h and h not in {"127.0.0.1", "localhost"} for h in ALLOWED_HOSTS):
        raise RuntimeError("DJANGO_ALLOWED_HOSTS must include production hostnames.")
    if CENTRAL_CONNECTOR_SECRET in {"", "dev-connector-secret"}:
        raise RuntimeError("CENTRAL_CONNECTOR_SECRET must be set to a strong value in production.")
if CENTRAL_CONNECTOR_SIGNED and not CENTRAL_CONNECTOR_SECRET:
    raise RuntimeError("CENTRAL_CONNECTOR_SIGNED=1 requires CENTRAL_CONNECTOR_SECRET.")
