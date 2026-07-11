import json
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models.deletion import ProtectedError
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from apps.core.services import get_active_branch
from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.payments.models import Payment
from apps.payments.services import create_payment, get_booking_net_paid
from apps.accounts.permissions import has_perm
from apps.core.services import log_audit_event

from .models import Booking, BookingDriver, BookingAttachment
from .services import (
    BookingError,
    activate_upcoming_booking,
    checkout_booking,
    create_booking,
    extend_booking,
    finalize_return,
)


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _d(val):
    return parse_date(val) if val else None


def _perm_guard(request, perm_code: str):
    if not has_perm(request.user, perm_code):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    return None


def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception:
        amount = Decimal("0")
    return amount.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


# ================================
# LIST
# ================================
@login_required
@require_http_methods(["GET"])
def api_bookings_list(request):
    guard = _perm_guard(request, "bookings.view")
    if guard:
        return guard
    branch = get_active_branch(request)

    qs = Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").order_by("-id")
    if branch:
        qs = qs.filter(branch=branch)

    q = (request.GET.get("q") or "").strip()
    status = (request.GET.get("status") or "").strip()

    if status:
        qs = qs.filter(status=status)

    if q:
        qs = qs.filter(
            customer__name__icontains=q
        ) | qs.filter(
            customer__phone_number__icontains=q
        ) | qs.filter(
            vehicle__plate_number__icontains=q
        )

    data = []
    for b in qs[:500]:
        data.append(
            {
                "id": b.id,
                "status": b.status,
                "pickup_date": str(b.pickup_date),
                "return_date": str(b.return_date),
                "customer": b.customer.name,
                "vehicle": f"{getattr(b.vehicle.brand,'name','')} {getattr(b.vehicle.model,'name','')} {b.vehicle.plate_number}",
                "total": str(b.total_amount),
            }
        )

    return JsonResponse({"ok": True, "results": data})


# ================================
# CREATE
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_create(request):
    guard = _perm_guard(request, "bookings.create")
    if guard:
        return guard
    data = _json(request)

    vehicle = Vehicle.objects.filter(id=data.get("vehicle_id")).first()
    if not vehicle:
        return JsonResponse({"ok": False, "error": "Vehicle Not Found"}, status=404)

    branch = get_active_branch(request)

    pickup = _d(data.get("pickup_date") or data.get("pickup"))
    ret = _d(data.get("return_date") or data.get("return"))

    if not pickup or not ret:
        return JsonResponse({"ok": False, "error": "Dates Required"}, status=400)

    customer = None
    if data.get("customer_id"):
        customer = Customer.objects.filter(id=data.get("customer_id")).first()

    if not customer:
        name = (data.get("customer_name") or "").strip()
        if not name:
            return JsonResponse({"ok": False, "error": "Customer Required"}, status=400)

        customer = Customer.objects.create(
            name=name,
            phone_number=data.get("phone") or "",
            id_number=data.get("id_number") or "",
        )

    extras = data.get("extras") or []

    try:
        booking = create_booking(
            branch=branch,
            created_by=request.user,
            customer=customer,
            vehicle=vehicle,
            pickup_date=pickup,
            return_date=ret,
            daily_rate=data.get("daily_rate"),
            deposit_amount=data.get("deposit"),
            vat_rate=data.get("vat_rate"),
            extras=extras,
            status="CONFIRMED",
            notes=data.get("notes"),
        )

        drivers = data.get("drivers") or []
        for d in drivers:
            BookingDriver.objects.create(
                booking=booking,
                name=d.get("name"),
                phone_number=d.get("phone"),
                id_number=d.get("id_number"),
                license_number=d.get("license"),
            )

        log_audit_event(
            action="BOOKING_CREATED",
            entity_type="Booking",
            entity_id=booking.id,
            message=f"Booking {booking.reference or booking.id} created",
            request=request,
            metadata={"customer_id": customer.id, "vehicle_id": vehicle.id, "status": booking.status},
        )
        return JsonResponse({"ok": True, "booking_id": booking.id})

    except BookingError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ================================
# UPDATE
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_update(request, booking_id: int):
    guard = _perm_guard(request, "bookings.update")
    if guard:
        return guard

    branch = get_active_branch(request)
    booking = Booking.objects.filter(id=booking_id).first()
    if not booking:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)
    if branch and booking.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    data = _json(request)

    pickup = _d(data.get("pickup_date")) if data.get("pickup_date") is not None else booking.pickup_date
    ret = _d(data.get("return_date")) if data.get("return_date") is not None else booking.return_date
    if pickup and ret and ret < pickup:
        return JsonResponse({"ok": False, "error": "Return date cannot be before pickup date"}, status=400)

    allowed_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}
    status = data.get("status")
    if status and status not in allowed_statuses:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)

    if pickup:
        booking.pickup_date = pickup
    if ret:
        booking.return_date = ret
    if status:
        booking.status = status
    if data.get("notes") is not None:
        booking.notes = (data.get("notes") or "").strip()

    booking.save(update_fields=["pickup_date", "return_date", "status", "notes"])
    log_audit_event(
        action="BOOKING_UPDATED",
        entity_type="Booking",
        entity_id=booking.id,
        message=f"Booking {booking.reference or booking.id} updated",
        request=request,
        metadata={"status": booking.status},
    )
    return JsonResponse({"ok": True})


# ================================
# DELETE
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_delete(request, booking_id: int):
    guard = _perm_guard(request, "bookings.delete")
    if guard:
        return guard

    branch = get_active_branch(request)
    booking = Booking.objects.filter(id=booking_id).first()
    if not booking:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)
    if branch and booking.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    try:
        booking_ref = booking.reference or booking.id
        booking.delete()
    except ProtectedError:
        return JsonResponse({"ok": False, "error": "This booking has related records and cannot be deleted"}, status=400)
    log_audit_event(
        action="BOOKING_DELETED",
        entity_type="Booking",
        entity_id=booking_id,
        message=f"Booking {booking_ref} deleted",
        request=request,
    )
    return JsonResponse({"ok": True})


# ================================
# AVAILABILITY
# ================================
@login_required
@require_http_methods(["GET"])
def api_vehicle_availability(request):
    guard = _perm_guard(request, "bookings.create")
    if guard:
        return guard
    pickup = _d(request.GET.get("pickup"))
    ret = _d(request.GET.get("return"))

    if not pickup or not ret:
        return JsonResponse({"ok": False, "error": "Dates Required"}, status=400)

    branch = get_active_branch(request)

    booked = Booking.objects.filter(
        pickup_date__lt=ret,
        return_date__gt=pickup,
    ).exclude(status__in=["CANCELLED", "RETURNED", "CLOSED"])

    if branch:
        booked = booked.filter(branch=branch)

    vehicles = Vehicle.objects.exclude(id__in=booked.values_list("vehicle_id", flat=True))

    out = []
    for v in vehicles:
        out.append(
            {
                "id": v.id,
                "name": f"{getattr(v.brand,'name','')} {getattr(v.model,'name','')}",
                "plate": v.plate_number,
                "rate": float(v.daily_rate),
                "deposit": float(v.deposit),
            }
        )

    return JsonResponse({"ok": True, "vehicles": out})


# ================================
# ACTIVATE
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_activate(request, booking_id: int):
    guard = _perm_guard(request, "bookings.update")
    if guard:
        return guard
    branch = get_active_branch(request)
    b = Booking.objects.filter(id=booking_id).first()

    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    try:
        activate_upcoming_booking(b, user=request.user)
        log_audit_event(
            action="BOOKING_ACTIVATED",
            entity_type="Booking",
            entity_id=b.id,
            message=f"Booking {b.reference or b.id} activated",
            request=request,
        )
        return JsonResponse({"ok": True})
    except BookingError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ================================
# EXTEND
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_extend(request, booking_id: int):
    guard = _perm_guard(request, "bookings.extend")
    if guard:
        return guard
    data = _json(request)
    b = Booking.objects.filter(id=booking_id).first()

    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    new_return = _d(data.get("new_return_date"))

    if not new_return:
        return JsonResponse({"ok": False, "error": "Date Required"}, status=400)

    try:
        extend_booking(b, new_return_date=new_return, user=request.user)
        log_audit_event(
            action="BOOKING_EXTENDED",
            entity_type="Booking",
            entity_id=b.id,
            message=f"Booking {b.reference or b.id} extended",
            request=request,
            metadata={"new_return_date": new_return.isoformat()},
        )
        return JsonResponse({"ok": True})
    except BookingError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ================================
# CHECKOUT
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_checkout(request, booking_id: int):
    guard = _perm_guard(request, "bookings.checkout")
    if guard:
        return guard
    data = _json(request)
    b = Booking.objects.filter(id=booking_id).first()

    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    try:
        checkout_booking(
            b,
            inspector=request.user,
            odometer_out_km=data.get("odo"),
            fuel_out_percent=data.get("fuel"),
            checklist=data.get("checklist"),
            customer_signature_data=data.get("signature"),
        )
        log_audit_event(
            action="BOOKING_CHECKED_OUT",
            entity_type="Booking",
            entity_id=b.id,
            message=f"Booking {b.reference or b.id} checked out",
            request=request,
        )
        return JsonResponse({"ok": True})
    except BookingError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ================================
# RETURN
# ================================
@login_required
@require_http_methods(["POST"])
def api_booking_return(request, booking_id: int):
    guard = _perm_guard(request, "bookings.return")
    if guard:
        return guard
    data = _json(request)
    b = Booking.objects.filter(id=booking_id).first()

    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    branch = get_active_branch(request)
    if branch and b.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    try:
        if b.status != "CHECKED_OUT":
            checkout_booking(
                b,
                inspector=request.user,
                odometer_out_km=data.get("odo") or 0,
                fuel_out_percent=data.get("fuel") or 100,
                checklist={},
                customer_signature_data="",
            )

        ret = finalize_return(
            b,
            inspector=request.user,
            inspector_name=data.get("inspector_name"),
            actual_return_date=_d(data.get("date")) or date.today(),
            odometer_in_km=data.get("odo"),
            fuel_return_percent=data.get("fuel"),
            fuel_charge=data.get("fuel_charge"),
            late_fee=data.get("late_fee"),
            damage_fee=data.get("damage_fee"),
            other_fee=data.get("other_fee"),
            damage_details=data.get("damage"),
            inspector_signature_data=data.get("signature"),
            extra_km_override=data.get("extra_km"),
        )

        payable_total = _money(ret.final_due)
        already_paid = _money(get_booking_net_paid(b))
        balance_before_payment = _money(payable_total - already_paid)

        payment_amount_raw = (data.get("payment_amount") or "").strip()
        if not payment_amount_raw:
            payment_amount_raw = str(max(balance_before_payment, Decimal("0")))

        try:
            payment_amount = _money(payment_amount_raw)
        except Exception:
            payment_amount = Decimal("0")

        if payment_amount > 0:
            duplicate_today = Payment.objects.filter(
                booking=b,
                status="PAID",
                payment_date=timezone.localdate(),
                amount=payment_amount,
            ).exists()
            if not duplicate_today:
                create_payment(
                    request=request,
                    booking=b,
                    amount=str(payment_amount),
                    method=(data.get("payment_method") or "CASH"),
                    notes=(data.get("payment_notes") or "Return settlement"),
                )
        balance_due = _money(balance_before_payment - payment_amount)

        log_audit_event(
            action="BOOKING_RETURNED",
            entity_type="Booking",
            entity_id=b.id,
            message=f"Booking {b.reference or b.id} returned",
            request=request,
            metadata={
                "final_due": str(ret.final_due),
                "early_return_credit": str(getattr(ret, "early_return_credit", Decimal("0"))),
                "already_paid": str(already_paid),
                "balance_due": str(balance_due),
            },
        )
        return JsonResponse(
            {
                "ok": True,
                "due": str(ret.final_due),
                "early_return_credit": str(getattr(ret, "early_return_credit", Decimal("0"))),
                "payable_total": str(payable_total),
                "already_paid": str(already_paid),
                "collected_amount": str(payment_amount),
                "balance_before_payment": str(balance_before_payment),
                "balance_due": str(balance_due),
            }
        )
    except BookingError as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)


# ================================
# RETURN DAMAGE PHOTOS
# ================================
@login_required
@require_http_methods(["GET"])
def api_booking_return_damage_photos_list(request, booking_id: int):
    guard = _perm_guard(request, "bookings.damage_photos")
    if guard:
        return guard
    b = Booking.objects.filter(id=booking_id).first()
    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    branch = get_active_branch(request)
    if branch and b.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    items = BookingAttachment.objects.filter(booking=b, kind="DAMAGE_PHOTO").order_by("-id")
    data = [
        {
            "id": a.id,
            "url": a.file.url if a.file else "",
            "notes": a.notes or "",
        }
        for a in items
    ]
    return JsonResponse({"ok": True, "results": data})


@login_required
@require_http_methods(["POST"])
def api_booking_return_damage_photos_upload(request, booking_id: int):
    guard = _perm_guard(request, "bookings.damage_photos")
    if guard:
        return guard
    b = Booking.objects.filter(id=booking_id).first()
    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    branch = get_active_branch(request)
    if branch and b.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    files = request.FILES.getlist("files")
    if not files:
        return JsonResponse({"ok": False, "error": "No Files"}, status=400)

    for f in files:
        BookingAttachment.objects.create(booking=b, file=f, kind="DAMAGE_PHOTO")

    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_booking_return_damage_photos_delete(request, booking_id: int, attachment_id: int):
    guard = _perm_guard(request, "bookings.damage_photos")
    if guard:
        return guard
    b = Booking.objects.filter(id=booking_id).first()
    if not b:
        return JsonResponse({"ok": False, "error": "Not Found"}, status=404)

    branch = get_active_branch(request)
    if branch and b.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    BookingAttachment.objects.filter(id=attachment_id, booking=b, kind="DAMAGE_PHOTO").delete()
    return JsonResponse({"ok": True})
