from django.core.management.base import BaseCommand

from apps.settings_app.integration_services import run_accounting_sync, run_telematics_pull
from apps.settings_app.models import IntegrationProfile


class Command(BaseCommand):
    help = "Run all active integration synchronizations."

    def add_arguments(self, parser):
        parser.add_argument("--period", default="monthly")
        parser.add_argument("--since-hours", type=int, default=6)

    def handle(self, *args, **options):
        period = (options.get("period") or "monthly").strip().lower()
        since_hours = int(options.get("since_hours") or 6)
        total = 0
        for profile in IntegrationProfile.objects.filter(is_active=True):
            if "ACCOUNTING" in profile.integration_type:
                result = run_accounting_sync(profile=profile, period=period)
            else:
                result = run_telematics_pull(profile=profile, since_hours=since_hours)
            total += 1
            self.stdout.write(f"{profile.integration_type}: {result.get('status')}")
        self.stdout.write(self.style.SUCCESS(f"Integration sync done ({total} profiles)."))
