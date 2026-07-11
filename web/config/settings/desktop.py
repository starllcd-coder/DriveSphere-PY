from __future__ import annotations

import os
from pathlib import Path

from .base import *  # noqa


# Desktop runtime is local-only; default DEBUG to on so Django runserver
# serves static assets correctly without an extra collectstatic step.
DEBUG = os.getenv("DRIVESPHERE_DESKTOP_DEBUG", "1") == "1"

# Dedicated desktop backend data root (separate from web app runtime files).
DESKTOP_DATA_DIR = Path(
    os.getenv(
        "DRIVESPHERE_DESKTOP_DATA_DIR",
        str(Path.home() / "AppData" / "Local" / "DriveSphereDesktop" / "data"),
    )
)
DESKTOP_DATA_DIR.mkdir(parents=True, exist_ok=True)
(DESKTOP_DATA_DIR / "media").mkdir(parents=True, exist_ok=True)
(DESKTOP_DATA_DIR / "staticfiles").mkdir(parents=True, exist_ok=True)

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DESKTOP_DATA_DIR / "desktop.sqlite3"),
    }
}

MEDIA_ROOT = DESKTOP_DATA_DIR / "media"
STATIC_ROOT = DESKTOP_DATA_DIR / "staticfiles"

# Desktop backend is local-only; force cookies to non-secure for localhost.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# Keep desktop runtime self-contained (no Redis dependency).
USE_REDIS_CACHE = False
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "drivesphere-desktop-local",
        "TIMEOUT": int(os.getenv("DEFAULT_CACHE_TTL", "300")),
    }
}

# Disable external monitoring by default for local desktop runtime.
SENTRY_DSN = ""
