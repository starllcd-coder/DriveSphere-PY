from django.contrib import admin
from .models import MaintenanceTask


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "task_type", "priority", "status", "assignee", "task_date", "due_date", "est_cost")
    list_filter = ("status", "task_type", "priority", "branch")
    search_fields = ("vehicle__plate_number", "vehicle__vin", "notes")