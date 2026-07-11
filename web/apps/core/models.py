from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Notification(TimeStampedModel):
    TYPE_CHOICES = [
        ("BOOKING", "Booking"),
        ("PAYMENT", "Payment"),
        ("REMINDER", "Reminder"),
        ("GENERAL", "General"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="GENERAL",
    )
    metadata = models.JSONField(blank=True, default=dict)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user}"


class DeviceToken(TimeStampedModel):
    PLATFORM_CHOICES = [
        ("ios", "iOS"),
        ("android", "Android"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="device_tokens",
    )
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.platform}"


class SupportMessage(TimeStampedModel):
    SENDER_CHOICES = [
        ("customer", "Customer"),
        ("support", "Support"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_messages",
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, default="customer")
    message = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user_id} - {self.sender}"


class AuditLog(TimeStampedModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=80, blank=True, default="")
    entity_id = models.CharField(max_length=80, blank=True, default="")
    branch_name = models.CharField(max_length=120, blank=True, default="")
    message = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(blank=True, default=dict)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.action} - {self.entity_type} - {self.entity_id}"
