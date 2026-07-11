from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from apps.core.models import TimeStampedModel
from apps.settings_app.models import Branch


class Role(TimeStampedModel):
    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("AGENT", "Agent"),
        ("MECHANIC", "Mechanic"),
        ("ACCOUNTANT", "Accountant"),
        ("VIEWER", "Viewer"),
    )

    code = models.CharField(max_length=30, choices=ROLE_CHOICES, unique=True)
    name = models.CharField(max_length=60)

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        username = extra_fields.get("username")
        if username is not None:
            username = username.strip() or None
            extra_fields["username"] = username
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser, TimeStampedModel):
    """
    Email-first user model with optional username support.
    """
    LANGUAGE_CHOICES = (
        ("en", "English"),
        ("ar", "Arabic"),
    )

    username = models.CharField(max_length=150, unique=True, null=True, blank=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=30, blank=True, default="")
    nationality = models.CharField(max_length=60, blank=True, default="")

    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    default_branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    preferred_language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES, default="en")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.username is not None:
            self.username = self.username.strip() or None
        super().save(*args, **kwargs)
