from django.contrib import admin
from .models import (
    Booking,
    BookingExtra,
    BookingDriver,
    BookingStatusHistory,
    BookingHandover,
    BookingReturn,
    BookingAttachment,
    BookingCharge,
)


class BookingExtraInline(admin.TabularInline):
    model = BookingExtra
    extra = 0


class BookingDriverInline(admin.TabularInline):
    model = BookingDriver
    extra = 0


class BookingStatusInline(admin.TabularInline):
    model = BookingStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "note", "created_at")


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "vehicle", "pickup_date", "return_date", "status", "total_amount", "deposit_amount")
    list_filter = ("status", "pickup_date", "return_date", "branch")
    search_fields = ("id", "customer__name", "vehicle__plate_number", "vehicle__vin")
    inlines = [BookingExtraInline, BookingDriverInline, BookingStatusInline]


@admin.register(BookingHandover)
class BookingHandoverAdmin(admin.ModelAdmin):
    list_display = ("booking", "inspector", "timestamp", "odometer_out_km", "fuel_out_percent")


@admin.register(BookingReturn)
class BookingReturnAdmin(admin.ModelAdmin):
    list_display = ("booking", "inspector", "actual_return_date", "extra_km", "final_due")


@admin.register(BookingAttachment)
class BookingAttachmentAdmin(admin.ModelAdmin):
    list_display = ("booking", "kind", "created_at")


@admin.register(BookingCharge)
class BookingChargeAdmin(admin.ModelAdmin):
    list_display = ("booking", "charge_type", "amount", "created_at")