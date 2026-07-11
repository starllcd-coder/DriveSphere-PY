from django.db import models
from apps.core.models import TimeStampedModel


class Customer(TimeStampedModel):
    ID_TYPE_CHOICES = (
        ("PASSPORT", "Passport"),
        ("ID", "Id"),
        ("LICENSE", "License"),
    )

    name = models.CharField(max_length=140)
    id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES, default="ID")
    id_number = models.CharField(max_length=80, blank=True, default="")
    phone_number = models.CharField(max_length=40, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    address = models.CharField(max_length=300, blank=True, default="")

    license_number = models.CharField(max_length=80, blank=True, default="")
    license_issuer = models.CharField(max_length=80, blank=True, default="")
    license_issue_date = models.DateField(null=True, blank=True)
    license_expiry_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class CustomerDocument(TimeStampedModel):
    DOC_TYPES = (
        ("ID", "Id"),
        ("LICENSE", "License"),
        ("PASSPORT", "Passport"),
        ("OTHER", "Other"),
    )

    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("VERIFIED", "Verified"),
        ("REJECTED", "Rejected"),
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES)
    file = models.FileField(upload_to="customers/documents/")
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=200, blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.customer.name} - {self.doc_type}"