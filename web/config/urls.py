from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Mobile / desktop API
    path("api/", include("api.urls")),
    path("api/v1/", include("api.urls")),
    path("", include("apps.core.urls")),

    # Admin
    path("admin/", admin.site.urls),

    # Web app
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("settings/", include("apps.settings_app.urls")),

    # Chunk 2
    path("", include("apps.fleet.urls")),
    path("", include("apps.customers.urls")),

    # Chunk 3
    path("", include("apps.bookings.urls")),

    # Chunk 4
    path("", include("apps.payments.urls")),
    path("", include("apps.maintenance.urls")),
    path("", include("apps.reports.urls")),
    path("", include("apps.documents.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
