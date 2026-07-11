import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.reports.services import (
    get_overview,
    get_financial,
    get_fleet,
    get_customers,
    get_maintenance,
    get_predictive_insights,
    detect_anomalies,
)
from apps.settings_app.models import Branch


class Command(BaseCommand):
    help = "Generate JSON snapshots of key reports for all active branches."

    def handle(self, *args, **options):
        now = timezone.now()
        snapshot_dir = Path(settings.MEDIA_ROOT) / "reports" / "snapshots" / now.strftime("%Y%m%d")
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        branches = list(Branch.objects.filter(is_active=True).order_by("id"))
        targets = [None, *branches]
        generated = 0

        for branch in targets:
            branch_label = "global" if branch is None else f"branch-{branch.id}"
            payload = {
                "generated_at": now.isoformat(),
                "branch": {
                    "id": getattr(branch, "id", None),
                    "name": getattr(branch, "name", "Global"),
                    "code": getattr(branch, "code", ""),
                },
                "overview": {
                    "daily": get_overview("today", branch=branch),
                    "weekly": get_overview("weekly", branch=branch),
                    "monthly": get_overview("monthly", branch=branch),
                },
                "financial": get_financial("monthly", branch=branch),
                "fleet": get_fleet("monthly", branch=branch),
                "customers": get_customers("monthly", branch=branch),
                "maintenance": get_maintenance("monthly", branch=branch),
                "insights": get_predictive_insights("monthly", branch=branch),
                "new_anomalies": detect_anomalies("monthly", branch=branch, notify=False),
            }

            target = snapshot_dir / f"{branch_label}.json"
            target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            generated += 1

        self.stdout.write(self.style.SUCCESS(f"Report snapshots generated: {generated}"))
