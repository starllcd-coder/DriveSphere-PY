from django.urls import path

from .views import (
    ProfileAPIView,
    ProfileUpdateAPIView
)

urlpatterns = [

    path(
        "",
        ProfileAPIView.as_view(),
        name="api-profile"
    ),

    path(
        "update/",
        ProfileUpdateAPIView.as_view(),
        name="api-profile-update"
    ),

]