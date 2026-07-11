from django.urls import path

from .views import SupportMessageListCreateAPIView

urlpatterns = [
    path(
        "messages/",
        SupportMessageListCreateAPIView.as_view(),
        name="api-support-messages",
    ),
]
