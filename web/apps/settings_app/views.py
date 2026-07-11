import io
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
from django.db.models import Q, Sum
from django.db import connection, IntegrityError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import has_perm, is_admin, ROLE_PERMISSIONS
from apps.accounts.models import User, Role
from apps.core.models import AuditLog
from apps.core.services import (
    build_operational_notifications,
    get_active_branch,
    log_audit_event,
    sync_operational_notifications,
)
from .models import BusinessProfile, Branch, DocumentNumbering
from .services import (
    get_database_profile,
    save_database_profile,
    test_target_db_connection,
    migrate_sqlite_to_target_placeholder,
    fetch_exchange_rates,
    _derive_doc_code,
)


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _active_notifications(request) -> list[dict]:
    items = _build_notifications(request)
    dismissed = set(request.session.get("notifications_dismissed", []))
    snoozed = request.session.get("notifications_snoozed", {}) or {}
    today = timezone.localdate()

    active = []
    changed = False
    for item in items:
        if item["id"] in dismissed:
            continue
        snoozed_until = snoozed.get(item["id"])
        if snoozed_until:
            try:
                until_date = date.fromisoformat(str(snoozed_until))
            except Exception:
                until_date = None
            if until_date and until_date >= today:
                continue
            snoozed.pop(item["id"], None)
            changed = True
        active.append(item)

    if changed:
        request.session["notifications_snoozed"] = snoozed
        request.session.modified = True

    return active


def _build_notifications(request) -> list[dict]:
    return build_operational_notifications(
        branch=get_active_branch(request),
        today=timezone.localdate(),
    )

    branch = get_active_branch(request)
    today = timezone.localdate()
    upcoming_end = today + timedelta(days=7)
    expiry_end = today + timedelta(days=30)

    notifications = []

    booking_qs = Booking.objects.select_related("customer", "vehicle").exclude(status="CANCELLED")
    if branch:
        booking_qs = booking_qs.filter(branch=branch)

    upcoming = booking_qs.filter(
        status__in=["UPCOMING", "CONFIRMED"],
        pickup_date__gte=today,
        pickup_date__lte=upcoming_end,
    ).order_by("pickup_date")

    for b in upcoming[:50]:
        vehicle_plate = getattr(b.vehicle, "plate_number", "") if b.vehicle_id else ""
        notifications.append({
            "id": f"booking-upcoming-{b.id}",
            "type": "UPCOMING_BOOKING",
            "title": f"Upcoming booking #{b.id}",
            "detail": f"Pickup {b.pickup_date} • {vehicle_plate}",
            "due_date": b.pickup_date.isoformat() if b.pickup_date else "",
            "priority": 3,
        })

    overdue = booking_qs.filter(status="CHECKED_OUT", return_date__lt=today).order_by("return_date")
    for b in overdue[:50]:
        vehicle_plate = getattr(b.vehicle, "plate_number", "") if b.vehicle_id else ""
        notifications.append({
            "id": f"booking-overdue-{b.id}",
            "type": "OVERDUE_RETURN",
            "title": f"Delayed return #{b.id}",
            "detail": f"Due {b.return_date} • {vehicle_plate}",
            "due_date": b.return_date.isoformat() if b.return_date else "",
            "priority": 1,
        })

    pickup_today = booking_qs.filter(
        pickup_date=today,
        status__in=["UPCOMING", "CONFIRMED"],
    ).order_by("pickup_date")
    for b in pickup_today[:50]:
        vehicle_plate = getattr(b.vehicle, "plate_number", "") if b.vehicle_id else ""
        notifications.append({
            "id": f"booking-pickup-{b.id}",
            "type": "PICKUP_TODAY",
            "title": f"Pickup today #{b.id}",
            "detail": f"Pickup {b.pickup_date} • {vehicle_plate}",
            "due_date": b.pickup_date.isoformat() if b.pickup_date else "",
            "priority": 2,
        })

    returns_today = booking_qs.filter(
        return_date=today,
    ).exclude(status__in=["RETURNED", "CLOSED"]).order_by("return_date")
    for b in returns_today[:50]:
        vehicle_plate = getattr(b.vehicle, "plate_number", "") if b.vehicle_id else ""
        notifications.append({
            "id": f"booking-return-{b.id}",
            "type": "RETURN_TODAY",
            "title": f"Return today #{b.id}",
            "detail": f"Return {b.return_date} • {vehicle_plate}",
            "due_date": b.return_date.isoformat() if b.return_date else "",
            "priority": 2,
        })

    past_due = booking_qs.filter(return_date__lt=today).exclude(status__in=["RETURNED", "CLOSED"]).order_by("return_date")
    for b in past_due[:50]:
        paid_sum = Payment.objects.filter(booking=b, status="PAID").aggregate(s=Sum("amount"))["s"] or 0
        total = float(b.total_amount or 0)
        paid = float(paid_sum or 0)
        if total <= 0 or paid >= total:
            continue
        balance = max(total - paid, 0)
        label = "Unpaid" if paid == 0 else "Partially paid"
        notifications.append({
            "id": f"booking-balance-{b.id}",
            "type": "BOOKING_BALANCE_DUE",
            "title": f"{label} booking #{b.id}",
            "detail": f"Balance {balance:.3f} • Due {b.return_date}",
            "due_date": b.return_date.isoformat() if b.return_date else "",
            "priority": 1,
        })

    vehicle_qs = Vehicle.objects.all()
    if branch:
        vehicle_qs = vehicle_qs.filter(branch=branch)

    reg_qs = vehicle_qs.filter(registration_expiry__isnull=False, registration_expiry__lte=expiry_end)
    for v in reg_qs[:50]:
        is_overdue = v.registration_expiry < today
        notifications.append({
            "id": f"vehicle-registration-{v.id}",
            "type": "REGISTRATION_EXPIRY",
            "title": f"Registration {('overdue' if is_overdue else 'expiring')} • {v.plate_number}",
            "detail": f"Expiry {v.registration_expiry}",
            "due_date": v.registration_expiry.isoformat() if v.registration_expiry else "",
            "priority": 1 if is_overdue else 2,
        })

    ins_qs = vehicle_qs.filter(insurance_expiry__isnull=False, insurance_expiry__lte=expiry_end)
    for v in ins_qs[:50]:
        is_overdue = v.insurance_expiry < today
        notifications.append({
            "id": f"vehicle-insurance-{v.id}",
            "type": "INSURANCE_EXPIRY",
            "title": f"Insurance {('overdue' if is_overdue else 'expiring')} • {v.plate_number}",
            "detail": f"Expiry {v.insurance_expiry}",
            "due_date": v.insurance_expiry.isoformat() if v.insurance_expiry else "",
            "priority": 1 if is_overdue else 2,
        })

    doc_qs = VehicleDocument.objects.select_related("vehicle").filter(
        expiry_date__isnull=False,
        expiry_date__lte=expiry_end,
    )
    if branch:
        doc_qs = doc_qs.filter(vehicle__branch=branch)
    for d in doc_qs[:50]:
        is_overdue = d.expiry_date < today
        plate = getattr(d.vehicle, "plate_number", "") if d.vehicle_id else ""
        notifications.append({
            "id": f"vehicle-doc-{d.id}",
            "type": "VEHICLE_DOCUMENT_EXPIRY",
            "title": f"{d.doc_type.title()} {('overdue' if is_overdue else 'expiring')} • {plate}",
            "detail": f"Expiry {d.expiry_date}",
            "due_date": d.expiry_date.isoformat() if d.expiry_date else "",
            "priority": 1 if is_overdue else 2,
        })

    customer_qs = Customer.objects.filter(
        license_expiry_date__isnull=False,
        license_expiry_date__lte=expiry_end,
    ).order_by("license_expiry_date")
    for customer in customer_qs[:50]:
        is_overdue = customer.license_expiry_date < today
        notifications.append({
            "id": f"customer-license-{customer.id}",
            "type": "CUSTOMER_LICENSE_EXPIRY",
            "title": f"Customer license {('overdue' if is_overdue else 'expiring')} • {customer.name}",
            "detail": f"Expiry {customer.license_expiry_date}",
            "due_date": customer.license_expiry_date.isoformat() if customer.license_expiry_date else "",
            "priority": 1 if is_overdue else 2,
        })

    customer_docs = CustomerDocument.objects.select_related("customer").filter(
        expiry_date__isnull=False,
        expiry_date__lte=expiry_end,
    ).order_by("expiry_date")
    for document in customer_docs[:50]:
        is_overdue = document.expiry_date < today
        notifications.append({
            "id": f"customer-doc-{document.id}",
            "type": "CUSTOMER_DOCUMENT_EXPIRY",
            "title": f"{document.doc_type.title()} {('overdue' if is_overdue else 'expiring')} • {document.customer.name}",
            "detail": f"Expiry {document.expiry_date}",
            "due_date": document.expiry_date.isoformat() if document.expiry_date else "",
            "priority": 1 if is_overdue else 2,
        })

    maintenance_qs = MaintenanceTask.objects.select_related("vehicle").filter(
        task_type="SERVICE",
        status__in=["OPEN", "IN_PROGRESS"],
        due_date__isnull=False,
    ).order_by("due_date")
    if branch:
        maintenance_qs = maintenance_qs.filter(branch=branch)

    for t in maintenance_qs[:50]:
        if not t.due_date:
            continue
        if t.due_date > expiry_end:
            continue
        plate = getattr(t.vehicle, "plate_number", "") if t.vehicle_id else ""
        is_overdue = t.due_date < today
        notifications.append({
            "id": f"maintenance-service-{t.id}",
            "type": "MAINTENANCE_DUE",
            "title": f"Service {('overdue' if is_overdue else 'due')} • {plate}",
            "detail": f"Due {t.due_date}",
            "due_date": t.due_date.isoformat(),
            "priority": 1 if is_overdue else 2,
        })

    failed_payments = Payment.objects.select_related("booking").filter(status="VOID").order_by("-payment_date")
    if branch:
        failed_payments = failed_payments.filter(branch=branch)
    for p in failed_payments[:50]:
        notifications.append({
            "id": f"payment-failed-{p.id}",
            "type": "PAYMENT_FAILED",
            "title": f"Failed payment #{p.id}",
            "detail": f"Booking #{p.booking_id} • {p.amount} {p.currency_code}",
            "due_date": p.payment_date.isoformat() if p.payment_date else "",
            "priority": 2,
        })

    notifications.sort(key=lambda n: (n["priority"], n["due_date"] or ""))
    return notifications


# -------------------------
# PAGES
# -------------------------
@login_required
def settings_page(request):
    if not (has_perm(request.user, "settings.manage") or has_perm(request.user, "employees.manage")):
        return render(request, "errors/403.html", status=403)
    return render(request, "settings/index.html", {"role_permissions": ROLE_PERMISSIONS})


# -------------------------
# APIs
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_db_profile_get(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    prof = get_database_profile()
    return JsonResponse({
        "ok": True,
        "data": {
            "provider": prof.provider,
            "host": prof.host,
            "port": prof.port,
            "database_name": prof.database_name,
            "username": prof.username,
            "password": "",
            "has_password": bool(prof.get_password()),
            "sslmode": prof.sslmode,
            "is_active": prof.is_active,
        }
    })


@login_required
@require_http_methods(["GET"])
def api_business_profile_get(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    prof = BusinessProfile.get_solo()
    return JsonResponse({
        "ok": True,
        "data": {
            "business_name": prof.business_name,
            "short_code": prof.short_code,
            "business_name_ar": prof.business_name_ar,
            "commercial_registration_number": prof.commercial_registration_number,
            "vat_no": prof.vat_no,
            "address": prof.address,
            "address_ar": prof.address_ar,
            "phone_number": prof.phone_number,
            "phone_number_ar": prof.phone_number_ar,
            "email": prof.email,
            "email_ar": prof.email_ar,
            "website": prof.website,
            "website_ar": prof.website_ar,
            "currency_code": prof.currency_code,
            "currency_symbol": prof.currency_symbol,
            "logo_url": prof.logo.url if prof.logo else "",
        }
    })


@login_required
@require_http_methods(["POST"])
def api_business_profile_save(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    data = _json(request)
    prof = BusinessProfile.get_solo()
    prof.business_name = data.get("business_name", prof.business_name)
    prof.short_code = (data.get("short_code", prof.short_code) or "").strip().upper()
    prof.business_name_ar = data.get("business_name_ar", prof.business_name_ar)
    prof.commercial_registration_number = data.get("commercial_registration_number", prof.commercial_registration_number)
    prof.vat_no = data.get("vat_no", prof.vat_no)
    prof.address = data.get("address", prof.address)
    prof.address_ar = data.get("address_ar", prof.address_ar)
    prof.phone_number = data.get("phone_number", prof.phone_number)
    prof.phone_number_ar = data.get("phone_number_ar", prof.phone_number_ar)
    prof.email = data.get("email", prof.email)
    prof.email_ar = data.get("email_ar", prof.email_ar)
    prof.website = data.get("website", prof.website)
    prof.website_ar = data.get("website_ar", prof.website_ar)
    prof.currency_code = data.get("currency_code", prof.currency_code)
    prof.currency_symbol = data.get("currency_symbol", prof.currency_symbol)
    prof.save()
    log_audit_event(
        action="BUSINESS_PROFILE_UPDATED",
        entity_type="BusinessProfile",
        entity_id=prof.id,
        message="Business profile updated",
        request=request,
    )
    return JsonResponse({"ok": True, "message": "Saved"})


@login_required
@require_http_methods(["GET"])
def api_notifications_list(request):
    unread = _active_notifications(request)
    return JsonResponse({
        "ok": True,
        "results": unread,
        "count": len(unread),
        "total": len(_build_notifications(request)),
    })


@login_required
@require_http_methods(["POST"])
def api_notifications_clear(request):
    items = _build_notifications(request)
    request.session["notifications_dismissed"] = [n["id"] for n in items]
    request.session.modified = True
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_notifications_dismiss(request):
    data = _json(request)
    notification_id = (data.get("id") or "").strip()
    if not notification_id:
        return JsonResponse({"ok": False, "error": "Notification id required"}, status=400)

    dismissed = set(request.session.get("notifications_dismissed", []))
    dismissed.add(notification_id)
    request.session["notifications_dismissed"] = list(dismissed)
    request.session.modified = True
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_notifications_snooze(request):
    data = _json(request)
    notification_id = (data.get("id") or "").strip()
    days = int(data.get("days") or 1)
    if not notification_id:
        return JsonResponse({"ok": False, "error": "Notification id required"}, status=400)
    if days < 1:
        return JsonResponse({"ok": False, "error": "Invalid snooze period"}, status=400)

    snoozed = request.session.get("notifications_snoozed", {}) or {}
    snoozed[notification_id] = (timezone.localdate() + timedelta(days=days)).isoformat()
    request.session["notifications_snoozed"] = snoozed
    request.session.modified = True
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_notifications_sync(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Permission denied"}, status=403)

    result = sync_operational_notifications(today=timezone.localdate())
    log_audit_event(
        action="NOTIFICATION_SYNC_RUN",
        entity_type="Notification",
        message=f"Operational reminder sync completed for {result['users']} users",
        request=request,
        metadata=result,
    )
    return JsonResponse({"ok": True, "result": result})


@require_http_methods(["POST"])
def api_language_set(request):
    data = _json(request)
    language = (data.get("language") or "").strip().lower()
    if language not in ["en", "ar"]:
        return JsonResponse({"ok": False, "error": "Invalid language"}, status=400)

    if hasattr(request, "user") and request.user.is_authenticated:
        request.user.preferred_language = language
        request.user.save(update_fields=["preferred_language"])

    request.session["ui_lang"] = language
    request.session.modified = True
    return JsonResponse({"ok": True, "language": language})


@login_required
@require_http_methods(["POST"])
def api_business_logo_upload(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    logo = request.FILES.get("logo")
    if not logo:
        return JsonResponse({"ok": False, "error": "Logo file required"}, status=400)

    prof = BusinessProfile.get_solo()
    prof.logo = logo
    prof.save(update_fields=["logo"])
    log_audit_event(
        action="BUSINESS_LOGO_UPDATED",
        entity_type="BusinessProfile",
        entity_id=prof.id,
        message="Business logo updated",
        request=request,
    )
    return JsonResponse({"ok": True, "logo_url": prof.logo.url if prof.logo else ""})


@login_required
@require_http_methods(["GET"])
def api_branches_list(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branches = Branch.objects.all().order_by("name")
    return JsonResponse({"ok": True, "results": [{
        "id": b.id,
        "name": b.name,
        "code": b.code,
        "is_active": b.is_active,
    } for b in branches]})


@login_required
@require_http_methods(["POST"])
def api_branch_create(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "Branch name required"}, status=400)
    code = (data.get("code") or "").strip().upper()
    b, _ = Branch.objects.get_or_create(name=name)
    if code and b.code != code:
        b.code = code
        b.save(update_fields=["code"])
    log_audit_event(
        action="BRANCH_CREATED",
        entity_type="Branch",
        entity_id=b.id,
        message=f"Branch {b.name} created",
        request=request,
    )
    return JsonResponse({"ok": True, "branch_id": b.id})


@login_required
@require_http_methods(["POST"])
def api_branch_update(request, branch_id: int):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    branch = Branch.objects.filter(id=branch_id).first()
    if not branch:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)
    if "code" in data:
        branch.code = (data.get("code") or "").strip().upper()
    branch.save(update_fields=["code"])
    log_audit_event(
        action="BRANCH_UPDATED",
        entity_type="Branch",
        entity_id=branch.id,
        message=f"Branch {branch.name} updated",
        request=request,
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_branch_delete(request, branch_id: int):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = Branch.objects.filter(id=branch_id).first()
    Branch.objects.filter(id=branch_id).delete()
    if branch:
        log_audit_event(
            action="BRANCH_DELETED",
            entity_type="Branch",
            entity_id=branch.id,
            message=f"Branch {branch.name} deleted",
            request=request,
        )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_doc_numbering_list(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    default_types = [
        "INVOICE",
        "RECEIPT",
        "AGREEMENT",
        "CONFIRMATION",
        "QUOTATION",
        "HANDOVER",
        "RETURN_REPORT",
        "REPORT",
    ]
    for doc_type in default_types:
        DocumentNumbering.objects.get_or_create(doc_type=doc_type)

    docs = DocumentNumbering.objects.all().order_by("doc_type")
    for d in docs:
        if not d.doc_code:
            d.doc_code = _derive_doc_code(d.doc_type)
            d.save(update_fields=["doc_code"])
    return JsonResponse({"ok": True, "results": [{
        "id": d.id,
        "doc_type": d.doc_type,
        "doc_code": d.doc_code,
        "prefix": d.prefix,
        "separator": d.separator,
        "padding": d.padding,
        "next_number": d.next_number,
    } for d in docs]})


@login_required
@require_http_methods(["POST"])
def api_doc_numbering_save(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    doc_type = (data.get("doc_type") or "").strip()
    if not doc_type:
        return JsonResponse({"ok": False, "error": "doc_type required"}, status=400)
    d, _ = DocumentNumbering.objects.get_or_create(doc_type=doc_type)
    d.doc_code = (data.get("doc_code", d.doc_code) or "").strip().upper()
    d.prefix = data.get("prefix", d.prefix)
    d.separator = data.get("separator", d.separator)
    d.padding = int(data.get("padding", d.padding))
    d.next_number = int(data.get("next_number", d.next_number))
    d.save()
    log_audit_event(
        action="DOC_NUMBERING_UPDATED",
        entity_type="DocumentNumbering",
        entity_id=d.id,
        message=f"Document numbering updated for {d.doc_type}",
        request=request,
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_exchange_rates_get(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    prof = BusinessProfile.get_solo()
    updated_at = prof.exchange_rates_updated_at.isoformat() if prof.exchange_rates_updated_at else ""
    return JsonResponse({
        "ok": True,
        "data": {
            "base": prof.currency_code or "USD",
            "rates": prof.exchange_rates or {},
            "updated_at": updated_at,
        }
    })


@login_required
@require_http_methods(["POST"])
def api_exchange_rates_update(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    prof = BusinessProfile.get_solo()
    result = fetch_exchange_rates(prof.currency_code)
    if not result.ok:
        return JsonResponse({"ok": False, "error": result.message}, status=400)

    prof.exchange_rates = result.rates or {}
    prof.exchange_rates_updated_at = timezone.now()
    prof.save(update_fields=["exchange_rates", "exchange_rates_updated_at"])

    return JsonResponse({"ok": True, "message": result.message})


def _ensure_admin(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    return None


def _sqlite_db_path() -> str:
    engine = settings.DATABASES.get("default", {}).get("ENGINE", "")
    if "sqlite" not in engine:
        return ""
    return str(settings.DATABASES.get("default", {}).get("NAME", ""))


def _pg_config() -> dict:
    db = settings.DATABASES.get("default", {})
    engine = (db.get("ENGINE") or "").lower()
    if "postgres" not in engine:
        return {}
    return {
        "name": db.get("NAME") or "",
        "user": db.get("USER") or "",
        "password": db.get("PASSWORD") or "",
        "host": db.get("HOST") or "",
        "port": str(db.get("PORT") or ""),
    }


def _run_pg_command(cmd: list[str], env: dict) -> tuple[bool, str]:
    try:
        res = subprocess.run(cmd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True, res.stdout
    except FileNotFoundError:
        return False, "pg_dump/pg_restore not found in PATH"
    except subprocess.CalledProcessError as exc:
        return False, exc.stderr or str(exc)


def _safe_zip_members(zf: zipfile.ZipFile) -> list[str]:
    safe_names = []
    for name in zf.namelist():
        p = Path(name)
        if p.is_absolute() or ".." in p.parts:
            raise ValueError("Unsafe path in backup archive")
        safe_names.append(name)
    return safe_names


@login_required
@require_http_methods(["GET"])
def api_backup_export(request):
    guard = _ensure_admin(request)
    if guard:
        return guard

    db_path = _sqlite_db_path()
    pg = _pg_config()
    if not db_path and not pg:
        return JsonResponse({"ok": False, "error": "Unsupported database engine"}, status=400)
    if db_path and not os.path.exists(db_path):
        return JsonResponse({"ok": False, "error": "SQLite database not found"}, status=400)

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        if db_path:
            zf.write(db_path, arcname="db.sqlite3")
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                dump_path = os.path.join(tmpdir, "db.pgdump")
                env = os.environ.copy()
                if pg.get("password"):
                    env["PGPASSWORD"] = pg["password"]
                cmd = [
                    "pg_dump",
                    "-Fc",
                    "-f",
                    dump_path,
                ]
                if pg.get("host"):
                    cmd += ["-h", pg["host"]]
                if pg.get("port"):
                    cmd += ["-p", pg["port"]]
                if pg.get("user"):
                    cmd += ["-U", pg["user"]]
                cmd.append(pg["name"])
                ok, msg = _run_pg_command(cmd, env)
                if not ok:
                    return JsonResponse({"ok": False, "error": f"pg_dump failed: {msg}"}, status=400)
                zf.write(dump_path, arcname="db.pgdump")

        media_root = getattr(settings, "MEDIA_ROOT", "") or ""
        if media_root and os.path.exists(media_root):
            for root, _, files in os.walk(media_root):
                for f in files:
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, media_root)
                    zf.write(full_path, arcname=os.path.join("media", rel_path))

        meta = {
            "created_at": timezone.now().isoformat(),
            "db_engine": settings.DATABASES.get("default", {}).get("ENGINE", ""),
        }
        zf.writestr("meta.json", json.dumps(meta, indent=2))

    buf.seek(0)
    filename = f"drivesphere-backup-{timezone.now().strftime('%Y%m%d-%H%M%S')}.zip"
    response = HttpResponse(buf.read(), content_type="application/zip")
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


@login_required
@require_http_methods(["POST"])
def api_backup_restore(request):
    guard = _ensure_admin(request)
    if guard:
        return guard

    if (request.POST.get("confirm") or "").strip() != "RESTORE":
        return JsonResponse({"ok": False, "error": "Confirmation required"}, status=400)

    db_path = _sqlite_db_path()
    pg = _pg_config()
    if not db_path and not pg:
        return JsonResponse({"ok": False, "error": "Unsupported database engine"}, status=400)
    if db_path and not os.path.exists(db_path):
        return JsonResponse({"ok": False, "error": "SQLite database not found"}, status=400)

    backup = request.FILES.get("backup")
    if not backup:
        return JsonResponse({"ok": False, "error": "Backup file required"}, status=400)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            with zipfile.ZipFile(backup) as zf:
                _safe_zip_members(zf)
                zf.extractall(tmpdir)
        except Exception as exc:
            return JsonResponse({"ok": False, "error": f"Invalid backup: {exc}"}, status=400)

        if db_path:
            db_src = os.path.join(tmpdir, "db.sqlite3")
            if not os.path.exists(db_src):
                return JsonResponse({"ok": False, "error": "Backup missing db.sqlite3"}, status=400)
            connection.close()
            shutil.copy2(db_src, db_path)
        else:
            dump_src = os.path.join(tmpdir, "db.pgdump")
            if not os.path.exists(dump_src):
                return JsonResponse({"ok": False, "error": "Backup missing db.pgdump"}, status=400)
            env = os.environ.copy()
            if pg.get("password"):
                env["PGPASSWORD"] = pg["password"]
            cmd = [
                "pg_restore",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges",
                "-d",
                pg["name"],
                dump_src,
            ]
            if pg.get("host"):
                cmd += ["-h", pg["host"]]
            if pg.get("port"):
                cmd += ["-p", pg["port"]]
            if pg.get("user"):
                cmd += ["-U", pg["user"]]
            ok, msg = _run_pg_command(cmd, env)
            if not ok:
                return JsonResponse({"ok": False, "error": f"pg_restore failed: {msg}"}, status=400)

        media_root = getattr(settings, "MEDIA_ROOT", "") or ""
        media_src = os.path.join(tmpdir, "media")
        if media_root:
            if os.path.exists(media_root):
                shutil.rmtree(media_root)
            if os.path.exists(media_src):
                shutil.copytree(media_src, media_root)

    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_backup_reset(request):
    guard = _ensure_admin(request)
    if guard:
        return guard

    if (request.POST.get("confirm") or request.body.decode("utf-8", "ignore")).find("RESET") == -1:
        data = _json(request)
        if (data.get("confirm") or "").strip() != "RESET":
            return JsonResponse({"ok": False, "error": "Confirmation required"}, status=400)

    data = _json(request)
    admin_username = (data.get("admin_username") or os.environ.get("ADMIN_USERNAME") or "").strip()
    admin_password = data.get("admin_password") or os.environ.get("ADMIN_PASSWORD") or ""
    admin_email = (os.environ.get("ADMIN_EMAIL") or "").strip() or f"{admin_username}@local"
    if not admin_username or not admin_password:
        return JsonResponse({
            "ok": False,
            "error": "ADMIN_USERNAME and ADMIN_PASSWORD must be set before reset",
        }, status=400)

    call_command("flush", verbosity=0, interactive=False)

    role, _ = Role.objects.get_or_create(code="ADMIN", defaults={"name": "Admin"})
    user = User.objects.filter(Q(username__iexact=admin_username) | Q(email__iexact=admin_email)).first()
    if user:
        user.username = admin_username
        user.email = admin_email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.role = role
        user.set_password(admin_password)
        user.save()
    else:
        User.objects.create_superuser(
            email=admin_email,
            password=admin_password,
            username=admin_username,
            role=role,
        )

    media_root = getattr(settings, "MEDIA_ROOT", "") or ""
    if media_root and os.path.exists(media_root):
        shutil.rmtree(media_root)
        os.makedirs(media_root, exist_ok=True)

    request.session.flush()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_employees_list(request):
    if not has_perm(request.user, "employees.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    users = User.objects.select_related("role").order_by("email")
    return JsonResponse({"ok": True, "results": [{
        "id": u.id,
        "email": u.email,
        "username": u.username,
        "role": u.role.code if u.role else "",
        "is_active": u.is_active,
    } for u in users]})


@login_required
@require_http_methods(["POST"])
def api_employee_create(request):
    if not has_perm(request.user, "employees.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    if not email or not password:
        return JsonResponse({"ok": False, "error": "Email and password required"}, status=400)
    role_code = (data.get("role") or "").strip()
    role = None
    if role_code:
        role, _ = Role.objects.get_or_create(code=role_code, defaults={"name": role_code.title()})
    username = (data.get("username") or "").strip() or None
    try:
        user = User.objects.create(email=email, username=username, role=role, is_active=True)
        user.set_password(password)
        user.save()
    except IntegrityError:
        return JsonResponse(
            {"ok": False, "error": "Email or username already exists"},
            status=400,
        )
    log_audit_event(
        action="EMPLOYEE_CREATED",
        entity_type="User",
        entity_id=user.id,
        message=f"Employee {user.email} created",
        request=request,
        metadata={"role": role.code if role else ""},
    )
    return JsonResponse({"ok": True, "user_id": user.id, "message": "User saved"})


@login_required
@require_http_methods(["POST"])
def api_employee_update(request, user_id: int):
    if not has_perm(request.user, "employees.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    user = User.objects.filter(id=user_id).first()
    if not user:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)
    if "email" in data:
        incoming_email = (data.get("email") or "").strip()
        if not incoming_email:
            return JsonResponse({"ok": False, "error": "Email required"}, status=400)
        user.email = incoming_email
    if "username" in data:
        user.username = (data.get("username") or "").strip() or None
    if "role" in data:
        role_code = (data.get("role") or "").strip()
        if role_code:
            role_obj, _ = Role.objects.get_or_create(code=role_code, defaults={"name": role_code.title()})
            user.role = role_obj
        else:
            user.role = None
    if "is_active" in data:
        user.is_active = bool(data.get("is_active"))
    if data.get("password"):
        user.set_password(data.get("password"))
    try:
        user.save()
    except IntegrityError:
        return JsonResponse(
            {"ok": False, "error": "Email or username already exists"},
            status=400,
        )
    log_audit_event(
        action="EMPLOYEE_UPDATED",
        entity_type="User",
        entity_id=user.id,
        message=f"Employee {user.email} updated",
        request=request,
        metadata={"role": user.role.code if user.role else ""},
    )
    return JsonResponse({"ok": True, "message": "User saved"})


@login_required
@require_http_methods(["POST"])
def api_employee_delete(request, user_id: int):
    if not has_perm(request.user, "employees.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    user = User.objects.filter(id=user_id).first()
    User.objects.filter(id=user_id).delete()
    if user:
        log_audit_event(
            action="EMPLOYEE_DELETED",
            entity_type="User",
            entity_id=user.id,
            message=f"Employee {user.email} deleted",
            request=request,
        )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_audit_logs_list(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    qs = AuditLog.objects.select_related("user").all()
    query = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()
    if query:
        qs = qs.filter(
            Q(action__icontains=query)
            | Q(entity_type__icontains=query)
            | Q(entity_id__icontains=query)
            | Q(message__icontains=query)
            | Q(branch_name__icontains=query)
            | Q(user__email__icontains=query)
        )
    if action:
        qs = qs.filter(action=action)

    results = []
    for log in qs[:200]:
        results.append({
            "id": log.id,
            "created_at": log.created_at.isoformat() if log.created_at else "",
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "branch_name": log.branch_name,
            "message": log.message,
            "user_email": log.user.email if log.user_id else "",
        })
    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_db_profile_save(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    data = _json(request)
    prof = save_database_profile(data)
    return JsonResponse({"ok": True, "message": "Saved", "data": {"provider": prof.provider, "is_active": prof.is_active}})


@login_required
@require_http_methods(["POST"])
def api_db_test_connection(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    prof = get_database_profile()
    result = test_target_db_connection(prof)
    return JsonResponse({"ok": result.ok, "message": result.message})


@login_required
@require_http_methods(["POST"])
def api_db_migrate_placeholder(request):
    if not has_perm(request.user, "settings.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    prof = get_database_profile()
    result = migrate_sqlite_to_target_placeholder(prof)
    return JsonResponse({"ok": result.ok, "message": result.message})
