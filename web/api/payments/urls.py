from django.urls import path

from .views import (
    HyperPayCheckoutAPIView,
    HyperPayStatusAPIView,
    PaymentCreateAPIView,
    PaymentDetailAPIView,
    PaymentListAPIView,
    RefundCreateAPIView,
)

urlpatterns = [
    path("", PaymentListAPIView.as_view(), name="api-payment-list"),
    path("create/", PaymentCreateAPIView.as_view(), name="api-payment-create"),
    path("<int:pk>/", PaymentDetailAPIView.as_view(), name="api-payment-detail"),
    path("refunds/create/", RefundCreateAPIView.as_view(), name="api-refund-create"),
    path("hyperpay/checkout/", HyperPayCheckoutAPIView.as_view(), name="api-hyperpay-checkout"),
    path("hyperpay/status/", HyperPayStatusAPIView.as_view(), name="api-hyperpay-status"),
]