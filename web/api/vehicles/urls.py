from django.urls import path

from .views import (
    VehicleListAPIView,
    VehicleDetailAPIView,
    VehicleTelematicsIngestAPIView,
    VehicleTelematicsMetricsAPIView,
    VehicleTelematicsLatestAPIView,
    VehicleTelematicsTripsAPIView,
    VehicleTelematicsEventsAPIView,
)
from .reviews_views import VehicleReviewListCreateAPIView
from .search_views import VehicleSearchAPIView


urlpatterns = [

    path(
        "",
        VehicleListAPIView.as_view(),
        name="api-vehicle-list"
    ),

    path(
        "search/",
        VehicleSearchAPIView.as_view(),
        name="api-vehicle-search"
    ),

    path(
        "<int:pk>/",
        VehicleDetailAPIView.as_view(),
        name="api-vehicle-detail"
    ),
    path(
        "<int:pk>/telematics/ingest/",
        VehicleTelematicsIngestAPIView.as_view(),
        name="api-vehicle-telematics-ingest",
    ),
    path(
        "<int:pk>/telematics/metrics/",
        VehicleTelematicsMetricsAPIView.as_view(),
        name="api-vehicle-telematics-metrics",
    ),
    path(
        "<int:pk>/telematics/latest/",
        VehicleTelematicsLatestAPIView.as_view(),
        name="api-vehicle-telematics-latest",
    ),
    path(
        "<int:pk>/telematics/trips/",
        VehicleTelematicsTripsAPIView.as_view(),
        name="api-vehicle-telematics-trips",
    ),
    path(
        "<int:pk>/telematics/events/",
        VehicleTelematicsEventsAPIView.as_view(),
        name="api-vehicle-telematics-events",
    ),

    path(
        "<int:pk>/reviews/",
        VehicleReviewListCreateAPIView.as_view(),
        name="api-vehicle-reviews"
    ),

]
