from django.urls import path

from .views import (
    IntegrationProfileListCreateAPIView,
    IntegrationSyncRunAPIView,
    IntegrationSyncLogListAPIView,
)

urlpatterns = [
    path("profiles/", IntegrationProfileListCreateAPIView.as_view(), name="api-integration-profiles"),
    path("sync/run/", IntegrationSyncRunAPIView.as_view(), name="api-integration-sync-run"),
    path("sync/logs/", IntegrationSyncLogListAPIView.as_view(), name="api-integration-sync-logs"),
]
