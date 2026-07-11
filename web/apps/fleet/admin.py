from django.contrib import admin
from .models import Vehicle, VehicleBrand, VehicleModel, VehicleCategory, VehicleDocument, VehiclePhoto, TelematicsPing


@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    search_fields = ("name", "brand__name")
    list_display = ("name", "brand")
    list_filter = ("brand",)


@admin.register(VehicleCategory)
class VehicleCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ("plate_number", "brand", "model", "year", "status", "daily_rate", "branch")
    list_filter = ("status", "fuel", "transmission", "branch", "category")
    search_fields = ("plate_number", "vin", "brand__name", "model__name")


@admin.register(VehicleDocument)
class VehicleDocumentAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "doc_type", "expiry_date", "created_at")
    list_filter = ("doc_type",)


@admin.register(VehiclePhoto)
class VehiclePhotoAdmin(admin.ModelAdmin):
    list_display = ("vehicle", "created_at")


@admin.register(TelematicsPing)
class TelematicsPingAdmin(admin.ModelAdmin):
    list_display = (
        "vehicle",
        "provider",
        "recorded_at",
        "odometer_km",
        "speed_kmh",
        "fuel_percent",
        "battery_voltage",
        "engine_status",
    )
    list_filter = ("provider", "recorded_at")
    search_fields = ("vehicle__plate_number", "external_vehicle_id")
