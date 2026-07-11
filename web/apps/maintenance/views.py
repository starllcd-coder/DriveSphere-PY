import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils import timezone

from apps.core.services import get_active_branch
from apps.fleet.models import Vehicle
from apps.documents.pdf_html import render_pdf_from_template
from apps.settings_app.models import BusinessProfile
from apps.settings_app.services import get_next_document_number
from apps.reports.services import get_maintenance
from apps.accounts.permissions import has_perm, is_admin
from apps.core.services import log_audit_event
from .models import MaintenanceTask


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _parse_date(value):
    """
    Accepts YYYY-MM-DD string, returns python date or None.
    """
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except Exception:
        return None


def _print_base_context():
    business = BusinessProfile.get_solo()
    return {
        "business": business,
        "now": timezone.now().strftime("%Y-%m-%d %H:%M"),
    }


# -------------------------
# PAGES
# -------------------------
@login_required
@ensure_csrf_cookie
def maintenance_page(request):
    if not has_perm(request.user, "maintenance.view"):
        return render(request, "errors/403.html", status=403)
    return render(request, "maintenance/index.html")


@login_required
def maintenance_new_task_page(request):
    if not has_perm(request.user, "maintenance.create"):
        return render(request, "errors/403.html", status=403)
    vehicles = Vehicle.objects.select_related("brand", "model").all().order_by("plate_number")

    if request.method == "POST":
        if not has_perm(request.user, "maintenance.create"):
            return render(request, "errors/403.html", status=403)
        vehicle_id = request.POST.get("vehicle_id")
        if vehicle_id:
            task = MaintenanceTask(
                vehicle_id=int(vehicle_id),
                task_type=request.POST.get("type") or "Service",
                priority=request.POST.get("priority") or "Medium",
                due_date=_parse_date(request.POST.get("due_date")),
                est_cost=request.POST.get("est_cost") or 0,
                notes=request.POST.get("notes") or "",
                assignee=request.user,
            )
            branch = get_active_branch(request)
            if hasattr(task, "branch") and branch:
                task.branch = branch
            task.save()
            if hasattr(task, "vehicle") and task.vehicle and task.vehicle.status != "MAINTENANCE":
                task.vehicle.status = "MAINTENANCE"
                task.vehicle.save(update_fields=["status"])
            return redirect("maintenance_page")

    return render(request, "maintenance/new_task.html", {"vehicles": vehicles})


# -------------------------
# APIs
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_maintenance_list(request):
    if not has_perm(request.user, "maintenance.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    qs = MaintenanceTask.objects.select_related("vehicle", "assignee", "branch").order_by("-id")

    branch = get_active_branch(request)
    if branch:
        qs = qs.filter(branch=branch)

    task_type = (request.GET.get("type") or request.GET.get("task_type") or "").strip()
    if task_type:
        qs = qs.filter(task_type__iexact=task_type)

    priority = (request.GET.get("priority") or "").strip()
    if priority:
        qs = qs.filter(priority__iexact=priority)

    show_done = (request.GET.get("show_done") or "").lower() in ["1", "true", "yes"]
    if not show_done:
        qs = qs.exclude(status__in=["DONE", "CANCELLED"])

    results = []
    for t in qs[:500]:
        v = getattr(t, "vehicle", None)
        plate = getattr(v, "plate_number", "") or getattr(v, "plate", "")

        vehicle_name = ""
        if v:
            bname = getattr(getattr(v, "brand", None), "name", "")
            mname = getattr(getattr(v, "model", None), "name", "")
            vehicle_name = (bname + " " + mname).strip() or getattr(v, "name", "")

        results.append({
            "id": t.id,
            "date": str(getattr(t, "task_date", getattr(t, "date", "")) or ""),
            "vehicle": vehicle_name,
            "plate": plate,
            "type": getattr(t, "task_type", getattr(t, "type", "")),
            "priority": getattr(t, "priority", ""),
            "assignee": getattr(getattr(t, "assignee", None), "email", "") or getattr(getattr(t, "assignee", None), "name", ""),
            "due": str(getattr(t, "due_date", getattr(t, "due", "")) or ""),
            "est_cost": str(getattr(t, "est_cost", "0.000")),
            "notes": getattr(t, "notes", ""),
        })

    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_maintenance_create(request):
    if not has_perm(request.user, "maintenance.create"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """
    POST /api/maintenance/create/

    Expected JSON body (recommended):
    {
      "vehicle_id": 1,
      "type": "Service" | "Repair" | "Inspection",
      "priority": "Low" | "Medium" | "High",
      "due_date": "YYYY-MM-DD",
      "est_cost": 25.000,
      "notes": "..."
    }
    """
    data = _json(request)

    vehicle_id = data.get("vehicle_id")
    if not vehicle_id:
        return JsonResponse({"ok": False, "error": "vehicle_id required"}, status=400)

    task_type = data.get("type") or data.get("task_type") or "Service"
    priority = data.get("priority") or "Medium"
    due_date = _parse_date(data.get("due_date") or data.get("due"))
    est_cost = data.get("est_cost", 0) or 0
    notes = data.get("notes", "") or ""

    branch = get_active_branch(request)

    task = MaintenanceTask(
        vehicle_id=int(vehicle_id),
        task_type=task_type,
        priority=priority,
        due_date=due_date,
        est_cost=est_cost,
        notes=notes,
        assignee=request.user,
    )

    # Set branch if your model has it
    if hasattr(task, "branch") and branch:
        task.branch = branch

    task.save()

    vehicle = getattr(task, "vehicle", None)
    if vehicle and getattr(vehicle, "status", "") != "MAINTENANCE":
        vehicle.status = "MAINTENANCE"
        vehicle.save(update_fields=["status"])

    log_audit_event(
        action="MAINTENANCE_CREATED",
        entity_type="MaintenanceTask",
        entity_id=task.id,
        message=f"Maintenance task #{task.id} created",
        request=request,
        metadata={"vehicle_id": task.vehicle_id, "task_type": task.task_type, "status": task.status},
    )
    return JsonResponse({"ok": True, "task_id": task.id})


@login_required
@require_http_methods(["POST"])
def api_maintenance_mark_done(request, task_id: int):
    task = get_object_or_404(MaintenanceTask, id=task_id)

    # Respect branch (if branch field exists)
    branch = get_active_branch(request)
    if branch and hasattr(task, "branch_id") and task.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)

    if not has_perm(request.user, "maintenance.update"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    if hasattr(task, "status"):
        task.status = "DONE"
        task.done_at = timezone.now()
        task.save(update_fields=["status", "done_at"])

    vehicle = getattr(task, "vehicle", None)
    if vehicle and str(getattr(task, "task_type", "")).upper() == "SERVICE":
        vehicle.last_service_odometer = getattr(vehicle, "odometer_km", 0) or 0
        vehicle.save(update_fields=["last_service_odometer"])
    if vehicle and getattr(vehicle, "status", "") == "MAINTENANCE":
        vehicle.status = "AVAILABLE"
        vehicle.save(update_fields=["status"])

    log_audit_event(
        action="MAINTENANCE_COMPLETED",
        entity_type="MaintenanceTask",
        entity_id=task.id,
        message=f"Maintenance task #{task.id} marked done",
        request=request,
        metadata={"vehicle_id": task.vehicle_id},
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_maintenance_delete(request, task_id: int):
    if not has_perm(request.user, "maintenance.delete"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    task = get_object_or_404(MaintenanceTask, id=task_id)
    branch = get_active_branch(request)
    if branch and hasattr(task, "branch_id") and task.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)

    task_id_value = task.id
    task.delete()
    log_audit_event(
        action="MAINTENANCE_DELETED",
        entity_type="MaintenanceTask",
        entity_id=task_id_value,
        message=f"Maintenance task #{task_id_value} deleted",
        request=request,
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_maintenance_report_pdf(request):
    if not (has_perm(request.user, "reports.view") or has_perm(request.user, "reports.view_maintenance")):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period = (request.GET.get("period") or "monthly").strip().lower()
    branch = get_active_branch(request)

    data = get_maintenance(period, branch=branch)
    start = timezone.datetime.fromisoformat(data["date_from"]).date()
    end = timezone.datetime.fromisoformat(data["date_to"]).date()

    qs = MaintenanceTask.objects.select_related("vehicle", "assignee", "branch").order_by("-id")
    qs = qs.filter(task_date__gte=start, task_date__lte=end)
    if branch:
        qs = qs.filter(branch=branch)

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Maintenance Report",
        "data": data,
        "tasks": qs,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_maintenance.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="maintenance",
    )
