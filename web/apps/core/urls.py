from django.urls import path
from . import views

urlpatterns = [
    path("healthz/", views.healthz, name="healthz"),
    path("healthz/deep/", views.healthz_deep, name="healthz_deep"),
]
