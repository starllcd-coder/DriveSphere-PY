from django.contrib import admin
from .models import Customer, CustomerDocument


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name", "phone_number", "id_type", "id_number", "is_active")
    search_fields = ("name", "phone_number", "id_number")
    list_filter = ("is_active", "id_type")


@admin.register(CustomerDocument)
class CustomerDocumentAdmin(admin.ModelAdmin):
    list_display = ("customer", "doc_type", "expiry_date", "created_at")
    list_filter = ("doc_type",)