from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.accounts.permissions import has_perm
from apps.bookings.models import Booking
from apps.customers.models import Customer, CustomerDocument
from apps.fleet.models import Vehicle, VehicleDocument
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment
from apps.settings_app.models import Branch
from apps.core.models import AuditLog, Notification


def get_active_branch(request):
    branch_id = request.session.get(settings.ACTIVE_BRANCH_SESSION_KEY)
    if branch_id:
        branch = Branch.objects.filter(id=branch_id, is_active=True).first()
        if branch:
            return branch

    # Fallback: if there is only one active branch, use it.
    branches = Branch.objects.filter(is_active=True).order_by("name")
    if branches.count() == 1:
        branch = branches.first()
        request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = branch.id
        return branch
    return None


def log_audit_event(
    *,
    action: str,
    entity_type: str = "",
    entity_id=None,
    message: str = "",
    request=None,
    user=None,
    branch_name: str = "",
    metadata: dict | None = None,
):
    actor = user
    if actor is None and request is not None:
        candidate = getattr(request, "user", None)
        if getattr(candidate, "is_authenticated", False):
            actor = candidate

    if not branch_name and request is not None:
        branch = get_active_branch(request)
        branch_name = branch.name if branch else ""

    AuditLog.objects.create(
        user=actor if actor else None,
        action=(action or "").strip()[:80],
        entity_type=(entity_type or "").strip()[:80],
        entity_id=str(entity_id or "")[:80],
        branch_name=(branch_name or "")[:120],
        message=(message or "").strip()[:255],
        metadata=metadata or {},
    )


def build_operational_notifications(*, branch=None, today=None) -> list[dict]:
    today = today or timezone.localdate()
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

    for booking in upcoming[:50]:
        vehicle_plate = getattr(booking.vehicle, "plate_number", "") if booking.vehicle_id else ""
        notifications.append({
            "id": f"booking-upcoming-{booking.id}",
            "type": "UPCOMING_BOOKING",
            "title": f"Upcoming booking #{booking.id}",
            "detail": f"Pickup {booking.pickup_date} • {vehicle_plate}",
            "due_date": booking.pickup_date.isoformat() if booking.pickup_date else "",
            "priority": 3,
        })

    overdue = booking_qs.filter(status="CHECKED_OUT", return_date__lt=today).order_by("return_date")
    for booking in overdue[:50]:
        vehicle_plate = getattr(booking.vehicle, "plate_number", "") if booking.vehicle_id else ""
        notifications.append({
            "id": f"booking-overdue-{booking.id}",
            "type": "OVERDUE_RETURN",
            "title": f"Delayed return #{booking.id}",
            "detail": f"Due {booking.return_date} • {vehicle_plate}",
            "due_date": booking.return_date.isoformat() if booking.return_date else "",
            "priority": 1,
        })

    pickup_today = booking_qs.filter(
        pickup_date=today,
        status__in=["UPCOMING", "CONFIRMED"],
    ).order_by("pickup_date")
    for booking in pickup_today[:50]:
        vehicle_plate = getattr(booking.vehicle, "plate_number", "") if booking.vehicle_id else ""
        notifications.append({
            "id": f"booking-pickup-{booking.id}",
            "type": "PICKUP_TODAY",
            "title": f"Pickup today #{booking.id}",
            "detail": f"Pickup {booking.pickup_date} • {vehicle_plate}",
            "due_date": booking.pickup_date.isoformat() if booking.pickup_date else "",
            "priority": 2,
        })

    return_today = booking_qs.filter(
        return_date=today,
        status__in=["CONFIRMED", "CHECKED_OUT"],
    ).order_by("return_date")
    for booking in return_today[:50]:
        vehicle_plate = getattr(booking.vehicle, "plate_number", "") if booking.vehicle_id else ""
        notifications.append({
            "id": f"booking-return-{booking.id}",
            "type": "RETURN_TODAY",
            "title": f"Return today #{booking.id}",
            "detail": f"Return {booking.return_date} • {vehicle_plate}",
            "due_date": booking.return_date.isoformat() if booking.return_date else "",
            "priority": 2,
        })

    balance_due = booking_qs.filter(
        status__in=["CONFIRMED", "CHECKED_OUT"],
        return_date__isnull=False,
        return_date__lte=upcoming_end,
    ).order_by("return_date")
    for booking in balance_due[:50]:
        total_paid = sum((payment.amount or 0) for payment in booking.payments.exclude(status="VOID"))
        balance = (booking.total_amount or 0) - total_paid
        if balance <= 0:
            continue
        label = "Overdue balance" if booking.return_date and booking.return_date < today else "Balance due"
        notifications.append({
            "id": f"booking-balance-{booking.id}",
            "type": "BOOKING_BALANCE_DUE",
            "title": f"{label} booking #{booking.id}",
            "detail": f"Balance {balance:.3f} • Due {booking.return_date}",
            "due_date": booking.return_date.isoformat() if booking.return_date else "",
            "priority": 1,
        })

    vehicle_qs = Vehicle.objects.all().order_by("plate_number")
    if branch:
        vehicle_qs = vehicle_qs.filter(branch=branch)

    reg_qs = vehicle_qs.filter(registration_expiry__isnull=False, registration_expiry__lte=expiry_end)
    for vehicle in reg_qs[:50]:
        is_overdue = vehicle.registration_expiry < today
        notifications.append({
            "id": f"vehicle-registration-{vehicle.id}",
            "type": "REGISTRATION_EXPIRY",
            "title": f"Registration {('overdue' if is_overdue else 'expiring')} • {vehicle.plate_number}",
            "detail": f"Expiry {vehicle.registration_expiry}",
            "due_date": vehicle.registration_expiry.isoformat() if vehicle.registration_expiry else "",
            "priority": 1 if is_overdue else 2,
        })

    ins_qs = vehicle_qs.filter(insurance_expiry__isnull=False, insurance_expiry__lte=expiry_end)
    for vehicle in ins_qs[:50]:
        is_overdue = vehicle.insurance_expiry < today
        notifications.append({
            "id": f"vehicle-insurance-{vehicle.id}",
            "type": "INSURANCE_EXPIRY",
            "title": f"Insurance {('overdue' if is_overdue else 'expiring')} • {vehicle.plate_number}",
            "detail": f"Expiry {vehicle.insurance_expiry}",
            "due_date": vehicle.insurance_expiry.isoformat() if vehicle.insurance_expiry else "",
            "priority": 1 if is_overdue else 2,
        })

    vehicle_documents = VehicleDocument.objects.select_related("vehicle").filter(
        expiry_date__isnull=False,
        expiry_date__lte=expiry_end,
    )
    if branch:
        vehicle_documents = vehicle_documents.filter(vehicle__branch=branch)
    for document in vehicle_documents[:50]:
        is_overdue = document.expiry_date < today
        plate = getattr(document.vehicle, "plate_number", "") if document.vehicle_id else ""
        notifications.append({
            "id": f"vehicle-doc-{document.id}",
            "type": "VEHICLE_DOCUMENT_EXPIRY",
            "title": f"{document.doc_type.title()} {('overdue' if is_overdue else 'expiring')} • {plate}",
            "detail": f"Expiry {document.expiry_date}",
            "due_date": document.expiry_date.isoformat() if document.expiry_date else "",
            "priority": 1 if is_overdue else 2,
        })

    customers = Customer.objects.filter(
        license_expiry_date__isnull=False,
        license_expiry_date__lte=expiry_end,
    ).order_by("license_expiry_date")
    for customer in customers[:50]:
        is_overdue = customer.license_expiry_date < today
        notifications.append({
            "id": f"customer-license-{customer.id}",
            "type": "CUSTOMER_LICENSE_EXPIRY",
            "title": f"Customer license {('overdue' if is_overdue else 'expiring')} • {customer.name}",
            "detail": f"Expiry {customer.license_expiry_date}",
            "due_date": customer.license_expiry_date.isoformat() if customer.license_expiry_date else "",
            "priority": 1 if is_overdue else 2,
        })

    customer_documents = CustomerDocument.objects.select_related("customer").filter(
        expiry_date__isnull=False,
        expiry_date__lte=expiry_end,
    ).order_by("expiry_date")
    for document in customer_documents[:50]:
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

    for task in maintenance_qs[:50]:
        if not task.due_date or task.due_date > expiry_end:
            continue
        plate = getattr(task.vehicle, "plate_number", "") if task.vehicle_id else ""
        is_overdue = task.due_date < today
        notifications.append({
            "id": f"maintenance-service-{task.id}",
            "type": "MAINTENANCE_DUE",
            "title": f"Service {('overdue' if is_overdue else 'due')} • {plate}",
            "detail": f"Due {task.due_date}",
            "due_date": task.due_date.isoformat(),
            "priority": 1 if is_overdue else 2,
        })

    failed_payments = Payment.objects.select_related("booking").filter(status="VOID").order_by("-payment_date")
    if branch:
        failed_payments = failed_payments.filter(branch=branch)
    for payment in failed_payments[:20]:
        notifications.append({
            "id": f"payment-failed-{payment.id}",
            "type": "PAYMENT_FAILED",
            "title": f"Failed payment #{payment.id}",
            "detail": f"Booking #{payment.booking_id} • {payment.amount} {payment.currency_code}",
            "due_date": payment.payment_date.isoformat() if payment.payment_date else "",
            "priority": 2,
        })

    notifications.sort(key=lambda item: (item["priority"], item["due_date"] or ""))
    return notifications


def sync_operational_notifications(*, today=None) -> dict:
    today = today or timezone.localdate()
    User = get_user_model()
    recipient_qs = User.objects.filter(is_active=True).select_related("role", "default_branch")

    eligible_users = []
    for user in recipient_qs:
        if getattr(user, "is_superuser", False) or getattr(user, "role_id", None):
            eligible_users.append(user)

    created = 0
    updated = 0
    deleted = 0
    total = 0

    for user in eligible_users:
        branch = getattr(user, "default_branch", None)
        if branch and not has_perm(user, "settings.manage"):
            branch_notifications = build_operational_notifications(branch=branch, today=today)
        else:
            branch_notifications = build_operational_notifications(today=today)

        existing = {
            note.metadata.get("source_id"): note
            for note in Notification.objects.filter(
                user=user,
                notification_type="REMINDER",
                metadata__source="operations_reminder",
            )
        }
        active_ids = set()

        with transaction.atomic():
            for item in branch_notifications:
                active_ids.add(item["id"])
                defaults = {
                    "title": item["title"][:255],
                    "message": item["detail"],
                    "metadata": {
                        "source": "operations_reminder",
                        "source_id": item["id"],
                        "due_date": item["due_date"],
                        "priority": item["priority"],
                        "alert_type": item["type"],
                        "generated_on": today.isoformat(),
                        "branch_id": branch.id if branch else "",
                    },
                }
                note = existing.get(item["id"])
                if note:
                    note.title = defaults["title"]
                    note.message = defaults["message"]
                    note.metadata = defaults["metadata"]
                    note.save(update_fields=["title", "message", "metadata", "updated_at"])
                    updated += 1
                else:
                    Notification.objects.create(
                        user=user,
                        title=defaults["title"],
                        message=defaults["message"],
                        notification_type="REMINDER",
                        metadata=defaults["metadata"],
                    )
                    created += 1

            stale_qs = Notification.objects.filter(
                user=user,
                notification_type="REMINDER",
                metadata__source="operations_reminder",
            )
            if active_ids:
                stale_qs = stale_qs.exclude(metadata__source_id__in=active_ids)
            stale_deleted, _ = stale_qs.delete()
            deleted += stale_deleted

        total += len(branch_notifications)

    return {
        "users": len(eligible_users),
        "created": created,
        "updated": updated,
        "deleted": deleted,
        "total": total,
    }
