from django.db import transaction
from django.utils import timezone

from apps.core.services import get_active_branch
from .models import MaintenanceTask


@transaction.atomic
def create_task(*, request, vehicle, task_type, priority, due_date=None, est_cost=0, notes="") -> MaintenanceTask:
    branch = get_active_branch(request)

    # enforce branch if active
    if branch and vehicle.branch_id and vehicle.branch_id != branch.id:
        raise ValueError("Vehicle Does Not Belong To Active Branch")

    t = MaintenanceTask.objects.create(
        branch=branch,
        vehicle=vehicle,
        task_type=task_type,
        priority=priority,
        status="OPEN",
        assignee=request.user,
        due_date=due_date,
        est_cost=est_cost,
        notes=notes or "",
    )
    return t


@transaction.atomic
def mark_done(task: MaintenanceTask, user=None) -> MaintenanceTask:
    task.status = "DONE"
    task.done_at = timezone.now()
    task.save(update_fields=["status", "done_at", "updated_at"])
    return task