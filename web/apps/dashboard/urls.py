from django.urls import path
from .views import dashboard_view, api_global_search

urlpatterns = [
    path("", dashboard_view, name="home"),
    path("dashboard/", dashboard_view, name="dashboard"),
    path("api/search/", api_global_search, name="api_global_search"),
]
