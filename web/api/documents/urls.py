from django.urls import path

from .views import (
    CustomerDocumentDetailAPIView,
    CustomerDocumentListAPIView,
    CustomerDocumentUploadAPIView,
)

urlpatterns = [
    path("upload/", CustomerDocumentUploadAPIView.as_view(), name="api-document-upload"),
    path("", CustomerDocumentListAPIView.as_view(), name="api-document-list"),
    path("<int:pk>/", CustomerDocumentDetailAPIView.as_view(), name="api-document-detail"),
]