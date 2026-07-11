from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch
from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.accounts.models import User


class Booking(TimeStampedModel):
    STATUS_CHOICES = (
        ("DRAFT", "Draft"),
        ("CONFIRMED", "Confirmed"),
        ("UPCOMING", "Upcoming"),
        ("CHECKED_OUT", "Checked Out"),
        ("RETURNED", "Returned"),
        ("CLOSED", "Closed"),
        ("CANCELLED", "Cancelled"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bookings")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="bookings")

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings_created"
    )

    # Reference / numbering (for invoices/agreements)
    reference = models.CharField(max_length=40, blank=True, default="", db_index=True)

    pickup_date = models.DateField()
    return_date = models.DateField()

    # Optional time components (enterprise usage)
    pickup_time = models.TimeField(null=True, blank=True)
    return_time = models.TimeField(null=True, blank=True)

    # Optional locations (delivery / different pickup/drop)
    pickup_location = models.CharField(max_length=200, blank=True, default="")
    return_location = models.CharField(max_length=200, blank=True, default="")

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")

    # Pricing snapshot (frozen at booking time)
    currency_code = models.CharField(max_length=10, default="OMR")
    currency_symbol = models.CharField(max_length=10, default="﷼")

    daily_rate = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    extras_total = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    vat_rate = models.DecimalField(max_digits=6, decimal_places=3, default=0)  # e.g. 0.050
    vat_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    subtotal_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)  # subtotal + vat (excl deposit)

    notes = models.TextField(blank=True, default="")

    # Policies (frozen)
    included_km_per_day = models.PositiveIntegerField(default=200)
    rate_per_extra_km = models.DecimalField(max_digits=10, decimal_places=3, default=0.250)

    # Document workflow flags (optional but useful)
    invoice_generated = models.BooleanField(default=False)
    agreement_generated = models.BooleanField(default=False)

    def days(self) -> int:
        # Common rental practice: at least 1 day
        delta = (self.return_date - self.pickup_date).days
        return max(delta, 1)

    def __str__(self):
        ref = f"{self.reference} " if self.reference else ""
        plate = getattr(self.vehicle, "plate_number", "") if self.vehicle_id else ""
        return f"{ref}Booking #{self.id} - {self.customer.name} - {plate}"


class BookingStatusHistory(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    note = models.CharField(max_length=200, blank=True, default="")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.booking_id}: {self.from_status} -> {self.to_status}"


class BookingExtra(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="extras")
    name = models.CharField(max_length=80)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    def line_total(self):
        return self.qty * self.unit_price

    def __str__(self):
        return f"{self.booking_id} Extra: {self.name}"


class BookingDriver(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="additional_drivers")
    name = models.CharField(max_length=140)
    id_number = models.CharField(max_length=80, blank=True, default="")
    phone_number = models.CharField(max_length=40, blank=True, default="")
    license_number = models.CharField(max_length=80, blank=True, default="")
    license_expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.booking_id} Driver: {self.name}"


class BookingHandover(TimeStampedModel):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="handover")
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    odometer_out_km = models.PositiveIntegerField(default=0)
    fuel_out_percent = models.PositiveIntegerField(default=100)

    accessory_spare = models.BooleanField(default=False)
    accessory_jack = models.BooleanField(default=False)
    accessory_triangle = models.BooleanField(default=False)
    accessory_docs = models.BooleanField(default=False)
    accessory_child_seat = models.BooleanField(default=False)
    accessory_gps = models.BooleanField(default=False)

    customer_signature_data = models.TextField(blank=True, default="")  # store base64 or vector later

    def __str__(self):
        return f"Handover {self.booking_id}"


class BookingReturn(TimeStampedModel):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="return_report")
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    inspector_name = models.CharField(max_length=120, blank=True, default="")
    actual_return_date = models.DateField(default=timezone.localdate)

    odometer_in_km = models.PositiveIntegerField(default=0)
    fuel_return_percent = models.PositiveIntegerField(default=100)

    damage_details = models.TextField(blank=True, default="")
    inspector_signature_data = models.TextField(blank=True, default="")

    # Calculated return amounts (snapshot)
    extra_km = models.PositiveIntegerField(default=0)
    extra_km_charge = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    fuel_charge = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    late_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    damage_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    other_fee = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    additions_subtotal = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    final_due = models.DecimalField(max_digits=10, decimal_places=3, default=0)  # booking total + additions - deposit

    def __str__(self):
        return f"Return {self.booking_id}"


class BookingAttachment(TimeStampedModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="bookings/attachments/")
    kind = models.CharField(max_length=40, default="GENERAL")  # DAMAGE_PHOTO, SIGNATURE, OTHER
    notes = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"{self.booking_id} Attachment {self.kind}"


class BookingCharge(TimeStampedModel):
    """
    Optional granular charges beyond BookingReturn fields.
    """
    CHARGE_TYPES = (
        ("EXTRA_KM", "Extra Km"),
        ("FUEL", "Fuel"),
        ("LATE", "Late"),
        ("DAMAGE", "Damage"),
        ("OTHER", "Other"),
    )

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="charges")
    charge_type = models.CharField(max_length=20, choices=CHARGE_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    notes = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return f"{self.booking_id} {self.charge_type} {self.amount}"