from celery import shared_task

from apps.settings_app.integration_services import run_accounting_sync, run_telematics_pull
from apps.settings_app.models import IntegrationProfile


@shared_task(name="apps.settings_app.tasks.sync_integrations_task")
def sync_integrations_task():
    results = []
    for profile in IntegrationProfile.objects.filter(is_active=True):
        if "ACCOUNTING" in profile.integration_type:
            results.append({"integration_type": profile.integration_type, **run_accounting_sync(profile=profile, period="monthly")})
        else:
            results.append({"integration_type": profile.integration_type, **run_telematics_pull(profile=profile, since_hours=6)})
    return {"count": len(results), "results": results}
