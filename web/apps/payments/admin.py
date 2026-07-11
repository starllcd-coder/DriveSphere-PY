from django.contrib import admin
from .models import Payment, Refund


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("receipt_number", "booking", "payment_date", "method", "amount", "currency_code", "status")
    list_filter = ("status", "method", "payment_date", "branch")
    search_fields = ("receipt_number", "booking__id", "booking__customer__name", "booking__vehicle__plate_number")


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ("refund_number", "payment", "refund_date", "method", "amount", "currency_code", "status")
    list_filter = ("status", "method", "refund_date", "branch")
    search_fields = ("refund_number", "payment__receipt_number")