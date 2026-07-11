from django.db import models

from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch


class InsightSnapshot(TimeStampedModel):
    PERIOD_CHOICES = (
        ("today", "Today"),
        ("weekly", "Weekly"),
        ("monthly", "Monthly"),
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="insight_snapshots",
    )
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES, default="monthly")
    generated_for = models.DateField()
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-generated_for", "-created_at"]
        unique_together = ("branch", "period", "generated_for")

    def __str__(self):
        scope = self.branch.name if self.branch_id else "Global"
        return f"{scope} - {self.period} - {self.generated_for}"


class AnomalyEvent(TimeStampedModel):
    TYPE_CHOICES = (
        ("EXPENSE_SPIKE", "Expense Spike"),
        ("REPAIR_SPIKE", "Repair Spike"),
        ("PAYMENT_DELAY", "Payment Delay"),
    )
    SEVERITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="anomaly_events",
    )
    anomaly_type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default="MEDIUM")
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True, default="")
    detected_on = models.DateField()
    metadata = models.JSONField(default=dict, blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-detected_on", "-created_at"]

    def __str__(self):
        return f"{self.anomaly_type} - {self.detected_on} - {self.severity}"


class AccountingExport(TimeStampedModel):
    PROVIDER_CHOICES = (
        ("QUICKBOOKS", "QuickBooks"),
        ("ZOHO", "Zoho Books"),
        ("MANUAL", "Manual"),
    )
    TYPE_CHOICES = (
        ("INVOICES", "Invoices"),
        ("PAYMENTS", "Payments"),
        ("EXPENSES", "Expenses"),
    )
    STATUS_CHOICES = (
        ("READY", "Ready"),
        ("EXPORTED", "Exported"),
        ("FAILED", "Failed"),
    )

    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="accounting_exports",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default="MANUAL")
    export_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="READY")
    generated_on = models.DateField()
    row_count = models.PositiveIntegerField(default=0)
    file_name = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-generated_on", "-created_at"]

    def __str__(self):
        return f"{self.provider} {self.export_type} ({self.status})"
