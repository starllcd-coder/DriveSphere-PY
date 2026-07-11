from django.urls import path

from .views import (
    NotificationListAPIView,
    NotificationMarkReadAPIView,
    NotificationDeleteAPIView,
)

urlpatterns = [

    path(
        "",
        NotificationListAPIView.as_view(),
        name="api-notification-list"
    ),

    path(
        "<int:pk>/read/",
        NotificationMarkReadAPIView.as_view(),
        name="api-notification-read"
    ),

    path(
        "<int:pk>/delete/",
        NotificationDeleteAPIView.as_view(),
        name="api-notification-delete"
    ),

]