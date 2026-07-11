from django.db import connection
from django.core.cache import cache
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.conf import settings


@require_http_methods(["GET"])
def healthz(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        db_ok = True
    except Exception:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {
            "ok": db_ok,
            "service": "drivesphere-web",
            "database": "ok" if db_ok else "error",
        },
        status=status_code,
    )


@require_http_methods(["GET"])
def healthz_deep(request):
    details = {"service": "drivesphere-web", "environment": settings.DJANGO_ENV if hasattr(settings, "DJANGO_ENV") else ""}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        details["database"] = "ok"
    except Exception as exc:
        details["database"] = f"error: {exc}"

    try:
        cache.set("healthz:ping", "ok", 10)
        details["cache"] = "ok" if cache.get("healthz:ping") == "ok" else "error"
    except Exception as exc:
        details["cache"] = f"error: {exc}"

    details["celery_configured"] = bool(getattr(settings, "CELERY_BROKER_URL", ""))

    ok = details["database"] == "ok" and details["cache"] == "ok"
    return JsonResponse({"ok": ok, **details}, status=200 if ok else 503)
