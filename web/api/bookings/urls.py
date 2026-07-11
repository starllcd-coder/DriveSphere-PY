from django.urls import path

from .views import (
    BookingCreateAPIView,
    BookingDetailAPIView,
    BookingListAPIView,
)

urlpatterns = [
    path("create/", BookingCreateAPIView.as_view(), name="api-booking-create"),
    path("", BookingListAPIView.as_view(), name="api-booking-list"),
    path("<int:pk>/", BookingDetailAPIView.as_view(), name="api-booking-detail"),
]
