from django.contrib import admin

from .models import InsightSnapshot, AnomalyEvent, AccountingExport


@admin.register(InsightSnapshot)
class InsightSnapshotAdmin(admin.ModelAdmin):
    list_display = ("id", "branch", "period", "generated_for", "created_at")
    list_filter = ("period", "generated_for", "branch")
    search_fields = ("branch__name",)


@admin.register(AnomalyEvent)
class AnomalyEventAdmin(admin.ModelAdmin):
    list_display = ("id", "anomaly_type", "severity", "branch", "detected_on", "is_resolved")
    list_filter = ("anomaly_type", "severity", "is_resolved", "detected_on")
    search_fields = ("title", "details", "branch__name")


@admin.register(AccountingExport)
class AccountingExportAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "export_type", "status", "generated_on", "row_count")
    list_filter = ("provider", "export_type", "status", "generated_on")
    search_fields = ("file_name", "branch__name")
