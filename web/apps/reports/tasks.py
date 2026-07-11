from celery import shared_task
from django.core.management import call_command


@shared_task(name="apps.reports.tasks.generate_scheduled_reports_task")
def generate_scheduled_reports_task():
    call_command("generate_scheduled_reports")
    return {"ok": True}


@shared_task(name="apps.reports.tasks.run_anomaly_detection_task")
def run_anomaly_detection_task():
    call_command("detect_anomalies")
    return {"ok": True}
