from django.urls import path
from . import views

urlpatterns = [
    # ---- PAGES ----
    path("maintenance/", views.maintenance_page, name="maintenance_page"),
    path("maintenance/new/", views.maintenance_new_task_page, name="maintenance_new_task_page"),

    # ---- API ----
    path("api/maintenance/", views.api_maintenance_list, name="api_maintenance_list"),
    path("api/maintenance/create/", views.api_maintenance_create, name="api_maintenance_create"),
    path("api/maintenance/<int:task_id>/done/", views.api_maintenance_mark_done, name="api_maintenance_mark_done"),
    path("api/maintenance/<int:task_id>/delete/", views.api_maintenance_delete, name="api_maintenance_delete"),
    path("api/maintenance/report.pdf", views.api_maintenance_report_pdf, name="api_maintenance_report_pdf"),
]