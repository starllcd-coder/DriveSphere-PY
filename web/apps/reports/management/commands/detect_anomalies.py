from django.core.management.base import BaseCommand

from apps.reports.services import detect_anomalies
from apps.settings_app.models import Branch


class Command(BaseCommand):
    help = "Run anomaly detection for global scope and active branches."

    def add_arguments(self, parser):
        parser.add_argument("--period", default="monthly")
        parser.add_argument("--no-notify", action="store_true")

    def handle(self, *args, **options):
        period = (options.get("period") or "monthly").strip().lower()
        notify = not options.get("no_notify")

        total = 0
        total += len(detect_anomalies(period=period, branch=None, notify=notify))
        for branch in Branch.objects.filter(is_active=True):
            total += len(detect_anomalies(period=period, branch=branch, notify=notify))

        self.stdout.write(self.style.SUCCESS(f"Anomaly detection completed. New anomalies: {total}"))
