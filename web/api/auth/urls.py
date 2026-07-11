from django.urls import path

from .views import LoginAPIView, RegisterAPIView, ProfileAPIView, OTPRequestAPIView, OTPVerifyAPIView

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-auth-login"),
    path("register/", RegisterAPIView.as_view(), name="api-auth-register"),
    path("profile/", ProfileAPIView.as_view(), name="api-auth-profile"),
    path("otp/request/", OTPRequestAPIView.as_view(), name="api-auth-otp-request"),
    path("otp/verify/", OTPVerifyAPIView.as_view(), name="api-auth-otp-verify"),
]