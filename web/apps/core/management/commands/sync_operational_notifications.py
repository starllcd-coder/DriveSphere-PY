from django.core.management.base import BaseCommand

from apps.core.services import sync_operational_notifications


class Command(BaseCommand):
    help = "Generate and sync operational reminder notifications for internal users."

    def handle(self, *args, **options):
        result = sync_operational_notifications()
        self.stdout.write(
            self.style.SUCCESS(
                "Operational reminders synced: "
                f"users={result['users']} "
                f"created={result['created']} "
                f"updated={result['updated']} "
                f"deleted={result['deleted']} "
                f"total={result['total']}"
            )
        )
