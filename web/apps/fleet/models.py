from django.db import models
from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch


class VehicleBrand(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class VehicleModel(TimeStampedModel):
    brand = models.ForeignKey(VehicleBrand, on_delete=models.CASCADE, related_name="models")
    name = models.CharField(max_length=80)

    class Meta:
        unique_together = ("brand", "name")
        ordering = ["brand__name", "name"]

    def __str__(self):
        return f"{self.brand.name} {self.name}"


class VehicleCategory(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Vehicle(TimeStampedModel):
    TRANSMISSION_CHOICES = (
        ("AUTOMATIC", "Automatic"),
        ("MANUAL", "Manual"),
    )

    FUEL_CHOICES = (
        ("PETROL", "Petrol"),
        ("DIESEL", "Diesel"),
        ("HYBRID", "Hybrid"),
        ("ELECTRIC", "Electric"),
    )

    STATUS_CHOICES = (
        ("AVAILABLE", "Available"),
        ("RESERVED", "Reserved"),
        ("RENTED", "Rented"),
        ("MAINTENANCE", "Maintenance"),
        ("INACTIVE", "Inactive"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles")

    plate_number = models.CharField(max_length=30, unique=True)
    vin = models.CharField(max_length=40, blank=True, default="")

    brand = models.ForeignKey(VehicleBrand, on_delete=models.PROTECT, related_name="vehicles")
    model = models.ForeignKey(VehicleModel, on_delete=models.PROTECT, related_name="vehicles")

    year = models.PositiveIntegerField()
    category = models.ForeignKey(VehicleCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="vehicles")

    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, default="AUTOMATIC")
    fuel = models.CharField(max_length=20, choices=FUEL_CHOICES, default="PETROL")
    color = models.CharField(max_length=40, blank=True, default="")

    seats = models.PositiveIntegerField(default=5)
    odometer_km = models.PositiveIntegerField(default=0)

    last_service_odometer = models.PositiveIntegerField(default=0)
    service_interval_km = models.PositiveIntegerField(default=10000)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="AVAILABLE")

    daily_rate = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    deposit = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    tags = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")

    registration_expiry = models.DateField(null=True, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["plate_number"]

    def __str__(self):
        return f"{self.plate_number} - {self.brand.name} {self.model.name}"


class VehicleDocument(TimeStampedModel):
    DOC_TYPES = (
        ("REGISTRATION", "Registration"),
        ("INSURANCE", "Insurance"),
        ("OTHER", "Other"),
    )

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to="vehicles/docs/")
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.doc_type}"


class VehiclePhoto(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="vehicles/photos/")
    caption = models.CharField(max_length=120, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle.plate_number} Photo"


class VehicleReview(TimeStampedModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.vehicle_id} - {self.rating}"


class TelematicsPing(TimeStampedModel):
    PROVIDER_CHOICES = (
        ("GENERIC", "Generic"),
        ("GPS_PROVIDER_A", "GPS Provider A"),
        ("GPS_PROVIDER_B", "GPS Provider B"),
    )

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="telematics_pings")
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default="GENERIC")
    external_vehicle_id = models.CharField(max_length=120, blank=True, default="")
    recorded_at = models.DateTimeField()

    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    speed_kmh = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    odometer_km = models.PositiveIntegerField(default=0)
    fuel_percent = models.PositiveSmallIntegerField(default=0)
    fuel_used_liters = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    idle_seconds = models.PositiveIntegerField(default=0)
    engine_on = models.BooleanField(null=True, blank=True)
    engine_status = models.CharField(max_length=40, blank=True, default="")
    battery_voltage = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    fault_codes = models.JSONField(default=list, blank=True)

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-recorded_at", "-id"]
        indexes = [
            models.Index(fields=["vehicle", "recorded_at"]),
            models.Index(fields=["provider", "recorded_at"]),
        ]

    def __str__(self):
        return f"{self.vehicle.plate_number} {self.recorded_at}"
