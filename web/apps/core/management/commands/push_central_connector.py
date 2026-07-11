from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.utils import timezone

from apps.bookings.models import Booking
from apps.core.central_connector import post_connector


class Command(BaseCommand):
    help = "Push DriveSphere connector payloads to Central-Platform."

    def add_arguments(self, parser):
        parser.add_argument("--kind", choices=["tenant", "usage", "event"], default="usage")
        parser.add_argument("--tenant-code", default="")
        parser.add_argument("--module-code", default="")
        parser.add_argument("--status", default="active")
        parser.add_argument("--period", default="")
        parser.add_argument("--event-name", default="booking.updated")
        parser.add_argument("--event-id", default="")

    def handle(self, *args, **options):
        tenant_code = (options["tenant_code"] or getattr(settings, "CENTRAL_TENANT_CODE", "")).strip()
        module_code = (options["module_code"] or getattr(settings, "CENTRAL_MODULE_CODE", "drivesphere")).strip().lower()
        if not tenant_code:
            self.stdout.write(self.style.ERROR("Missing tenant code. Set --tenant-code or CENTRAL_TENANT_CODE"))
            return

        kind = options["kind"]
        if kind == "tenant":
            payload = {
                "tenant_code": tenant_code,
                "module_code": module_code,
                "status": str(options["status"] or "active"),
            }
            result = post_connector("tenant/sync/", payload)
            self.stdout.write(self.style.SUCCESS(f"tenant sync ok: {result}"))
            return

        if kind == "usage":
            now = timezone.now()
            period = (options["period"] or now.strftime("%Y-%m")).strip()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            qs = Booking.objects.filter(created_at__gte=month_start).exclude(status="CANCELLED")
            bookings_count = qs.count()
            gross_amount = qs.aggregate(total=Sum("total_amount")).get("total") or Decimal("0.0")
            payload = {
                "tenant_code": tenant_code,
                "module_code": module_code,
                "period": period,
                "bookings_count": bookings_count,
                "gross_amount": float(gross_amount),
            }
            result = post_connector("usage/report/", payload)
            self.stdout.write(self.style.SUCCESS(f"usage report ok: {result}"))
            return

        latest = Booking.objects.order_by("-id").values("reference", "status", "total_amount", "created_at").first() or {}
        payload = {
            "tenant_code": tenant_code,
            "module_code": module_code,
            "event_name": str(options["event_name"] or "booking.updated"),
            "event_id": str(options["event_id"] or f"drivesphere-{timezone.now().strftime('%Y%m%d%H%M%S')}"),
            "data": {"latest_booking": latest},
        }
        result = post_connector("webhooks/events/", payload)
        self.stdout.write(self.style.SUCCESS(f"webhook event ok: {result}"))
