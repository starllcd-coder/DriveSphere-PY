from django.db import models
from django.utils import timezone

from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch
from apps.fleet.models import Vehicle
from apps.accounts.models import User


class MaintenanceTask(TimeStampedModel):
    TYPE_CHOICES = (
        ("SERVICE", "Service"),
        ("REPAIR", "Repair"),
        ("INSPECTION", "Inspection"),
    )

    PRIORITY_CHOICES = (
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
    )

    STATUS_CHOICES = (
        ("OPEN", "Open"),
        ("IN_PROGRESS", "In Progress"),
        ("DONE", "Done"),
        ("CANCELLED", "Cancelled"),
    )

    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_tasks")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="maintenance_tasks")

    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="SERVICE")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIUM")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")

    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="maintenance_assigned")

    task_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)

    est_cost = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    notes = models.TextField(blank=True, default="")

    done_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-task_date", "-id"]

    def __str__(self):
        return f"{self.vehicle.plate_number} - {self.task_type} - {self.status}"