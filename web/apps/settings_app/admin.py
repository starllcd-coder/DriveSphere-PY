from django.contrib import admin
from .models import BusinessProfile, Branch, DatabaseProfile, IntegrationProfile, IntegrationSyncLog


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "business_name")
    search_fields = ("business_name",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(DatabaseProfile)
class DatabaseProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "provider", "database_name", "is_active")
    list_filter = ("provider", "is_active")


@admin.register(IntegrationProfile)
class IntegrationProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "integration_type", "branch", "is_active", "updated_at")
    list_filter = ("integration_type", "is_active")
    search_fields = ("integration_type", "branch__name", "org_id")


@admin.register(IntegrationSyncLog)
class IntegrationSyncLogAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "direction", "status", "summary", "created_at")
    list_filter = ("direction", "status", "profile__integration_type")
    search_fields = ("summary", "profile__integration_type")
