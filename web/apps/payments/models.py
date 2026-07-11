from django.db import models

from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch
from apps.bookings.models import Booking
from apps.accounts.models import User


class Payment(TimeStampedModel):
    METHOD_CHOICES = (
        ("CASH", "Cash"),
        ("CARD", "Card"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("OTHER", "Other"),
    )

    STATUS_CHOICES = (
        ("PAID", "Paid"),
        ("VOID", "Void"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="payments")

    receipt_number = models.CharField(max_length=40, unique=True)
    idempotency_key = models.CharField(max_length=80, unique=True, null=True, blank=True)

    payment_date = models.DateField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="CASH")

    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    currency_code = models.CharField(max_length=10, default="OMR")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PAID")
    notes = models.CharField(max_length=200, blank=True, default="")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments_created")

    def __str__(self):
        return f"{self.receipt_number} - {self.booking_id} - {self.amount}"


class Refund(TimeStampedModel):
    """
    Refund is separate to keep receipts clean and auditable.
    """
    METHOD_CHOICES = Payment.METHOD_CHOICES
    STATUS_CHOICES = (
        ("REFUNDED", "Refunded"),
        ("VOID", "Void"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds")
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")

    refund_number = models.CharField(max_length=40, unique=True)
    idempotency_key = models.CharField(max_length=80, unique=True, null=True, blank=True)

    refund_date = models.DateField()
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="CASH")

    amount = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    currency_code = models.CharField(max_length=10, default="OMR")

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="REFUNDED")
    notes = models.CharField(max_length=200, blank=True, default="")

    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="refunds_created")

    def __str__(self):
        return f"{self.refund_number} - {self.payment_id} - {self.amount}"
