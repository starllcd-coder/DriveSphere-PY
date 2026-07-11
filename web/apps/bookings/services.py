from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.services import get_active_branch
from apps.fleet.models import Vehicle
from apps.settings_app.models import BusinessProfile

from .models import (
    Booking,
    BookingExtra,
    BookingDriver,
    BookingHandover,
    BookingReturn,
    BookingStatusHistory,
)


class BookingError(Exception):
    pass


def D(value) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal("0")


def money(value) -> Decimal:
    return D(value).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _days(pickup: date, ret: date) -> int:
    delta = (ret - pickup).days
    return max(delta, 1)


def _overlaps(pickup_a: date, return_a: date, pickup_b: date, return_b: date) -> bool:
    # [pickup, return) overlap check
    return pickup_a < return_b and return_a > pickup_b


def _assert_vehicle_available(branch, vehicle: Vehicle, pickup: date, ret: date, exclude_booking_id=None):
    qs = Booking.objects.filter(vehicle=vehicle).exclude(status__in=["CANCELLED", "CLOSED", "RETURNED"])
    if branch:
        qs = qs.filter(branch=branch)

    if exclude_booking_id:
        qs = qs.exclude(id=exclude_booking_id)

    for b in qs.only("pickup_date", "return_date"):
        if _overlaps(pickup, ret, b.pickup_date, b.return_date):
            raise BookingError("Vehicle Is Not Available For The Selected Dates.")


def _recalc_totals(booking: Booking):
    # extras
    extras_total = BookingExtra.objects.filter(booking=booking).aggregate(
        s=Sum("unit_price")
    )["s"] or Decimal("0")

    # NOTE: BookingExtra stores qty; we must compute qty*unit_price
    # Do it manually to avoid DB function differences
    extras_total = Decimal("0")
    for e in BookingExtra.objects.filter(booking=booking).only("qty", "unit_price"):
        extras_total += (e.unit_price * e.qty)

    days = _days(booking.pickup_date, booking.return_date)
    daily = money(booking.daily_rate)

    subtotal = money(daily * days + extras_total)
    vat_rate = D(booking.vat_rate)
    vat_amount = money(subtotal * vat_rate)

    booking.extras_total = money(extras_total)
    booking.subtotal_amount = subtotal
    booking.vat_amount = vat_amount
    booking.total_amount = money(subtotal + vat_amount)
    booking.save(update_fields=["extras_total", "subtotal_amount", "vat_amount", "total_amount", "updated_at"])


def _push_status(booking: Booking, to_status: str, by_user=None, note: str = ""):
    from_status = booking.status
    if from_status == to_status:
        return
    booking.status = to_status
    booking.save(update_fields=["status", "updated_at"])
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status=from_status,
        to_status=to_status,
        changed_by=by_user,
        note=note[:200],
    )

    if hasattr(booking, "vehicle") and booking.vehicle and hasattr(booking.vehicle, "status"):
        if to_status in ["CANCELLED", "CLOSED", "RETURNED", "DRAFT"]:
            booking.vehicle.status = "AVAILABLE"
        elif to_status in ["CONFIRMED", "UPCOMING", "RESERVED"]:
            booking.vehicle.status = "RESERVED"
        elif to_status == "CHECKED_OUT":
            booking.vehicle.status = "RENTED"
        booking.vehicle.save(update_fields=["status"])


def _make_reference(branch, booking_id: int) -> str:
    # Simple enterprise reference pattern: BR-YYYY-000123
    # If branch has code/short_name field, use it; else "BR"
    code = "BR"
    if branch:
        for field in ["code", "short_code", "slug", "name"]:
            if hasattr(branch, field):
                val = getattr(branch, field) or ""
                if val:
                    code = str(val).strip().upper().replace(" ", "")[:6]
                    break
    year = timezone.localdate().year
    return f"{code}-{year}-{booking_id:06d}"


@transaction.atomic
def create_booking(
    *,
    branch,
    created_by,
    customer,
    vehicle: Vehicle,
    pickup_date: date,
    return_date: date,
    daily_rate=None,
    deposit_amount=None,
    vat_rate=None,
    extras=None,
    status: str = "CONFIRMED",
    notes: str = "",
) -> Booking:
    if pickup_date >= return_date:
        raise BookingError("Return Date Must Be After Pickup Date.")

    if branch is None:
        # Allow None branch; callers should pass a branch object when applicable.
        branch = None

    # determine branch scope
    active_branch = branch

    _assert_vehicle_available(active_branch, vehicle, pickup_date, return_date)

    business = BusinessProfile.get_solo()
    b = Booking.objects.create(
        branch=active_branch if active_branch else None,
        created_by=created_by,
        customer=customer,
        vehicle=vehicle,
        pickup_date=pickup_date,
        return_date=return_date,
        pickup_time=None,
        return_time=None,
        pickup_location="",
        return_location="",
        status=status or "CONFIRMED",
        currency_code=(business.currency_code or "OMR"),
        currency_symbol=(business.currency_symbol or ""),
        daily_rate=money(daily_rate if daily_rate is not None else getattr(vehicle, "daily_rate", 0)),
        deposit_amount=money(deposit_amount if deposit_amount is not None else getattr(vehicle, "deposit", 0)),
        vat_rate=money(vat_rate if vat_rate is not None else Decimal("0")),
        notes=(notes or ""),
        included_km_per_day=getattr(vehicle, "included_km_per_day", 200) if hasattr(vehicle, "included_km_per_day") else 200,
        rate_per_extra_km=money(getattr(vehicle, "rate_per_extra_km", Decimal("0.250"))) if hasattr(vehicle, "rate_per_extra_km") else money("0.250"),
    )

    if hasattr(vehicle, "status") and status in ["CONFIRMED", "UPCOMING", "RESERVED"]:
        vehicle.status = "RESERVED"
        vehicle.save(update_fields=["status"])

    # generate reference
    b.reference = _make_reference(active_branch, b.id)
    b.save(update_fields=["reference"])

    # extras
    BookingExtra.objects.filter(booking=b).delete()
    if extras:
        for e in extras:
            name = (e.get("name") or "").strip()
            if not name:
                continue
            qty = int(e.get("qty") or 1)
            unit = money(e.get("unit_price") or 0)
            BookingExtra.objects.create(booking=b, name=name, qty=max(qty, 1), unit_price=unit)

    # Auto UPCOMING if pickup in the future and status is CONFIRMED
    today = timezone.localdate()
    if b.status == "CONFIRMED" and b.pickup_date > today:
        _push_status(b, "UPCOMING", by_user=created_by, note="Auto upcoming (future pickup date)")

    _recalc_totals(b)
    BookingStatusHistory.objects.create(
        booking=b,
        from_status="",
        to_status=b.status,
        changed_by=created_by,
        note="Created",
    )
    return b


@transaction.atomic
def update_booking(
    booking: Booking,
    *,
    customer,
    vehicle: Vehicle,
    pickup_date: date,
    return_date: date,
    daily_rate=None,
    deposit_amount=None,
    vat_rate=None,
    extras=None,
    notes: str = "",
) -> Booking:
    if pickup_date >= return_date:
        raise BookingError("Return Date Must Be After Pickup Date.")

    active_branch = booking.branch
    _assert_vehicle_available(active_branch, vehicle, pickup_date, return_date, exclude_booking_id=booking.id)

    booking.customer = customer
    booking.vehicle = vehicle
    booking.pickup_date = pickup_date
    booking.return_date = return_date
    booking.daily_rate = money(daily_rate if daily_rate is not None else getattr(vehicle, "daily_rate", 0))
    booking.deposit_amount = money(deposit_amount if deposit_amount is not None else getattr(vehicle, "deposit", 0))
    booking.vat_rate = money(vat_rate if vat_rate is not None else booking.vat_rate)
    booking.notes = notes or ""
    booking.included_km_per_day = getattr(vehicle, "included_km_per_day", 200) if hasattr(vehicle, "included_km_per_day") else 200
    booking.rate_per_extra_km = money(getattr(vehicle, "rate_per_extra_km", Decimal("0.250"))) if hasattr(vehicle, "rate_per_extra_km") else money("0.250")
    booking.save()

    BookingExtra.objects.filter(booking=booking).delete()
    if extras:
        for e in extras:
            name = (e.get("name") or "").strip()
            if not name:
                continue
            qty = int(e.get("qty") or 1)
            unit = money(e.get("unit_price") or 0)
            BookingExtra.objects.create(booking=booking, name=name, qty=max(qty, 1), unit_price=unit)

    _recalc_totals(booking)
    return booking


@transaction.atomic
def activate_upcoming_booking(booking: Booking, user=None):
    if booking.status != "UPCOMING":
        raise BookingError("Only Upcoming Bookings Can Be Activated.")
    _push_status(booking, "CONFIRMED", by_user=user, note="Activated")


@transaction.atomic
def extend_booking(booking: Booking, new_return_date: date, user=None):
    if booking.status in ["CANCELLED", "CLOSED"]:
        raise BookingError("Cannot Extend A Cancelled Or Closed Booking.")

    if new_return_date <= booking.pickup_date:
        raise BookingError("Return Date Must Be After Pickup Date.")

    if new_return_date == booking.return_date:
        return

    active_branch = booking.branch
    _assert_vehicle_available(active_branch, booking.vehicle, booking.pickup_date, new_return_date, exclude_booking_id=booking.id)

    booking.return_date = new_return_date
    booking.save(update_fields=["return_date", "updated_at"])
    _recalc_totals(booking)
    BookingStatusHistory.objects.create(
        booking=booking,
        from_status=booking.status,
        to_status=booking.status,
        changed_by=user,
        note="Extended",
    )


@transaction.atomic
def checkout_booking(
    booking: Booking,
    *,
    inspector,
    odometer_out_km: int,
    fuel_out_percent: int,
    checklist: dict,
    customer_signature_data: str,
) -> BookingHandover:
    if booking.status not in ["CONFIRMED", "UPCOMING"]:
        raise BookingError("Booking Must Be Confirmed Or Upcoming To Checkout.")

    # create or update handover
    handover, _created = BookingHandover.objects.get_or_create(booking=booking)
    handover.inspector = inspector
    handover.timestamp = timezone.now()
    handover.odometer_out_km = max(int(odometer_out_km or 0), 0)
    handover.fuel_out_percent = max(min(int(fuel_out_percent or 0), 100), 0)

    checklist = checklist or {}
    handover.accessory_spare = bool(checklist.get("spare"))
    handover.accessory_jack = bool(checklist.get("jack"))
    handover.accessory_triangle = bool(checklist.get("triangle"))
    handover.accessory_docs = bool(checklist.get("docs"))
    handover.accessory_child_seat = bool(checklist.get("child_seat"))
    handover.accessory_gps = bool(checklist.get("gps"))

    handover.customer_signature_data = customer_signature_data or ""
    handover.save()

    # status and vehicle status
    _push_status(booking, "CHECKED_OUT", by_user=inspector, note="Checked out")

    if hasattr(booking.vehicle, "status"):
        booking.vehicle.status = "RENTED"
        booking.vehicle.save(update_fields=["status"])

    return handover


@transaction.atomic
def finalize_return(
    booking: Booking,
    *,
    inspector,
    inspector_name: str,
    actual_return_date: date,
    odometer_in_km: int,
    fuel_return_percent: int,
    fuel_charge,
    late_fee,
    damage_fee,
    other_fee,
    damage_details: str,
    inspector_signature_data: str,
    extra_km_override=None,
) -> BookingReturn:
    if booking.status != "CHECKED_OUT":
        raise BookingError("Only Checked Out Bookings Can Be Returned.")

    if not hasattr(booking, "handover") or not booking.handover:
        raise BookingError("Cannot Return Booking Without Handover Data.")

    # base computations
    booked_days = _days(booking.pickup_date, booking.return_date)
    used_days = booked_days
    if actual_return_date and actual_return_date < booking.return_date:
        used_days = _days(booking.pickup_date, actual_return_date)
    used_days = min(max(used_days, 1), booked_days)

    included_km = int(booking.included_km_per_day or 200) * used_days

    odo_out = int(booking.handover.odometer_out_km or 0)
    odo_in = max(int(odometer_in_km or 0), 0)
    total_km = max(0, odo_in - odo_out)

    if extra_km_override is not None and str(extra_km_override).strip() != "":
        try:
            extra_km = max(int(extra_km_override), 0)
        except Exception:
            extra_km = max(0, total_km - included_km)
    else:
        extra_km = max(0, total_km - included_km)
    extra_km_charge = money(D(extra_km) * money(booking.rate_per_extra_km or "0.250"))

    # Auto credit when vehicle is returned earlier than planned return date.
    # This prorates rental days while keeping extras fixed.
    early_return_credit = Decimal("0")
    if used_days < booked_days:
        prorated_subtotal = money(money(booking.daily_rate or 0) * used_days + money(booking.extras_total or 0))
        prorated_vat = money(prorated_subtotal * D(booking.vat_rate or 0))
        prorated_total = money(prorated_subtotal + prorated_vat)
        early_return_credit = max(money(booking.total_amount or 0) - prorated_total, Decimal("0"))

    fuel_charge = money(fuel_charge or 0)
    late_fee = money(late_fee or 0)
    damage_fee = money(damage_fee or 0)
    other_fee = money(other_fee or 0) - money(early_return_credit)

    additions = money(extra_km_charge + fuel_charge + late_fee + damage_fee + other_fee)

    final_due = money(booking.total_amount + additions - booking.deposit_amount)

    ret, _created = BookingReturn.objects.get_or_create(booking=booking)
    ret.inspector = inspector
    ret.inspector_name = (inspector_name or "").strip()
    ret.actual_return_date = actual_return_date or timezone.localdate()
    ret.odometer_in_km = odo_in
    ret.fuel_return_percent = max(min(int(fuel_return_percent or 0), 100), 0)
    ret.damage_details = (damage_details or "")
    ret.inspector_signature_data = inspector_signature_data or ""

    ret.extra_km = extra_km
    ret.extra_km_charge = extra_km_charge
    ret.fuel_charge = fuel_charge
    ret.late_fee = late_fee
    ret.damage_fee = damage_fee
    ret.other_fee = other_fee
    ret.additions_subtotal = additions
    ret.final_due = final_due
    ret.save()
    # Non-persistent convenience for immediate API responses.
    ret.early_return_credit = money(early_return_credit)

    _push_status(booking, "RETURNED", by_user=inspector, note="Returned")

    if hasattr(booking.vehicle, "status"):
        booking.vehicle.status = "AVAILABLE"
        booking.vehicle.save(update_fields=["status"])

    return ret
