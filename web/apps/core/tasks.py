from celery import shared_task
from django.core.management import call_command

from apps.core.services import sync_operational_notifications


@shared_task(name="apps.core.tasks.sync_operational_notifications_task")
def sync_operational_notifications_task():
    return sync_operational_notifications()


@shared_task(name="apps.core.tasks.run_automated_backup_task")
def run_automated_backup_task():
    call_command("create_system_backup")
    return {"ok": True}
