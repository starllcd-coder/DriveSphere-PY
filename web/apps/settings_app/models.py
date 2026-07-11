from django.db import models
from apps.core.models import TimeStampedModel
from .crypto import decrypt_value, encrypt_value


class Branch(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    code = models.CharField(max_length=10, blank=True, default="")
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BusinessProfile(TimeStampedModel):
    """
    Singleton-ish row. We keep it as first row.
    """
    business_name = models.CharField(max_length=200, blank=True, default="")
    short_code = models.CharField(max_length=10, blank=True, default="")
    business_name_ar = models.CharField(max_length=200, blank=True, default="")
    commercial_registration_number = models.CharField(max_length=100, blank=True, default="")
    vat_no = models.CharField(max_length=100, blank=True, default="")
    address = models.CharField(max_length=300, blank=True, default="")
    address_ar = models.CharField(max_length=300, blank=True, default="")
    phone_number = models.CharField(max_length=60, blank=True, default="")
    phone_number_ar = models.CharField(max_length=60, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    email_ar = models.EmailField(blank=True, default="")
    website = models.CharField(max_length=200, blank=True, default="")
    website_ar = models.CharField(max_length=200, blank=True, default="")

    # Default currency
    currency_code = models.CharField(max_length=10, blank=True, default="OMR")
    currency_symbol = models.CharField(max_length=10, blank=True, default="﷼")

    # Exchange rates cache (base currency -> rates map)
    exchange_rates = models.JSONField(blank=True, default=dict)
    exchange_rates_updated_at = models.DateTimeField(null=True, blank=True)

    # Logo later (keep placeholder field)
    logo = models.ImageField(upload_to="business/logo/", null=True, blank=True)

    class Meta:
        verbose_name = "Business Profile"
        verbose_name_plural = "Business Profile"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        return self.business_name or "Business Profile"


class DocumentNumbering(TimeStampedModel):
    """
    Stores prefixes/padding per document type. Increment is atomic in services.
    """
    doc_type = models.CharField(max_length=40, unique=True)  # INVOICE, RECEIPT, AGREEMENT, REPORT, etc.
    doc_code = models.CharField(max_length=10, blank=True, default="")
    prefix = models.CharField(max_length=20, blank=True, default="DS")
    separator = models.CharField(max_length=5, blank=True, default="-")
    padding = models.PositiveIntegerField(default=6)
    next_number = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["doc_type"]

    def __str__(self):
        return f"{self.doc_type} ({self.prefix}{self.separator}{str(self.next_number).zfill(self.padding)})"


class DatabaseProfile(TimeStampedModel):
    """
    Stores DB credentials for future use: PostgreSQL or Neon.
    We do NOT auto-switch Django DB at runtime; we provide "test" and "migrate placeholder".
    """
    PROVIDER_CHOICES = (
        ("POSTGRES", "PostgreSQL"),
        ("NEON", "Neon"),
    )

    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="POSTGRES")
    host = models.CharField(max_length=200, blank=True, default="")
    port = models.PositiveIntegerField(default=5432)
    database_name = models.CharField(max_length=200, blank=True, default="")
    username = models.CharField(max_length=200, blank=True, default="")
    password = models.CharField(max_length=200, blank=True, default="")  # later encrypt at rest

    # Optional SSL mode for Neon
    sslmode = models.CharField(max_length=30, blank=True, default="require")

    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Database Profile"
        verbose_name_plural = "Database Profile"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if not obj:
            obj = cls.objects.create()
        return obj

    def __str__(self):
        return f"{self.get_provider_display()} ({'Active' if self.is_active else 'Inactive'})"

    def set_password(self, raw_password: str) -> None:
        self.password = encrypt_value(raw_password)

    def get_password(self) -> str:
        return decrypt_value(self.password)


class IntegrationProfile(TimeStampedModel):
    INTEGRATION_CHOICES = (
        ("ACCOUNTING_QUICKBOOKS", "Accounting - QuickBooks"),
        ("ACCOUNTING_ZOHO", "Accounting - Zoho Books"),
        ("TELEMATICS_PROVIDER_A", "Telematics - Provider A"),
        ("TELEMATICS_PROVIDER_B", "Telematics - Provider B"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="integration_profiles")
    integration_type = models.CharField(max_length=40, choices=INTEGRATION_CHOICES, unique=True)
    base_url = models.CharField(max_length=255, blank=True, default="")
    client_id = models.CharField(max_length=255, blank=True, default="")
    client_secret = models.TextField(blank=True, default="")
    access_token = models.TextField(blank=True, default="")
    refresh_token = models.TextField(blank=True, default="")
    org_id = models.CharField(max_length=120, blank=True, default="")
    metadata = models.JSONField(blank=True, default=dict)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["integration_type"]

    def __str__(self):
        return f"{self.integration_type} ({'Active' if self.is_active else 'Inactive'})"

    def set_client_secret(self, raw_value: str) -> None:
        self.client_secret = encrypt_value(raw_value)

    def get_client_secret(self) -> str:
        return decrypt_value(self.client_secret)

    def set_access_token(self, raw_value: str) -> None:
        self.access_token = encrypt_value(raw_value)

    def get_access_token(self) -> str:
        return decrypt_value(self.access_token)

    def set_refresh_token(self, raw_value: str) -> None:
        self.refresh_token = encrypt_value(raw_value)

    def get_refresh_token(self) -> str:
        return decrypt_value(self.refresh_token)


class IntegrationSyncLog(TimeStampedModel):
    DIRECTION_CHOICES = (
        ("EXPORT", "Export"),
        ("IMPORT", "Import"),
        ("BIDIRECTIONAL", "Bidirectional"),
    )
    STATUS_CHOICES = (
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("PARTIAL", "Partial"),
    )

    profile = models.ForeignKey(IntegrationProfile, on_delete=models.CASCADE, related_name="sync_logs")
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default="BIDIRECTIONAL")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SUCCESS")
    summary = models.CharField(max_length=255, blank=True, default="")
    details = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.profile.integration_type} {self.direction} {self.status}"
