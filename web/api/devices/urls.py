from django.urls import path

from .views import DeviceTokenRegisterAPIView

urlpatterns = [
    path(
        "register/",
        DeviceTokenRegisterAPIView.as_view(),
        name="api-device-register",
    ),
]
