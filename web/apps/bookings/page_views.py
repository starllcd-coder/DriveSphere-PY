from datetime import date

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models.deletion import ProtectedError

from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.bookings.models import BookingDriver, BookingExtra
from apps.accounts.permissions import has_perm, is_admin
from apps.bookings.services import create_booking, checkout_booking, BookingError, update_booking
from apps.payments.services import get_booking_net_paid

from apps.core.services import get_active_branch
from .models import Booking, BookingHandover


@login_required
def bookings_page(request):
    if not has_perm(request.user, "bookings.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    qs = Booking.objects.select_related(
        "customer",
        "vehicle",
        "vehicle__brand",
        "vehicle__model",
    ).order_by("-created_at")

    if branch:
        qs = qs.filter(branch=branch)

    # basic filter placeholders (frontend wiring later)
    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    context = {
        "title": "Bookings",
        "page_title": "Bookings",
        "bookings": qs[:200],
    }
    return render(request, "bookings/index.html", context)


@login_required
def upcoming_bookings_page(request):
    if not has_perm(request.user, "bookings.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    qs = Booking.objects.select_related(
        "customer",
        "vehicle",
        "vehicle__brand",
        "vehicle__model",
    ).filter(status="UPCOMING").order_by("pickup_date")

    if branch:
        qs = qs.filter(branch=branch)

    context = {
        "title": "Upcoming Bookings",
        "page_title": "Upcoming Bookings",
        "bookings": qs[:200],
        "today": timezone.localdate(),
    }
    return render(request, "bookings/upcoming.html", context)


@login_required
def booking_wizard_page(request):
    if not has_perm(request.user, "bookings.create"):
        return render(request, "errors/403.html", status=403)
    return redirect("booking_wizard_customer")


@login_required
def booking_detail_page(request, booking_id: int):
    if not has_perm(request.user, "bookings.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    booking = get_object_or_404(
        Booking.objects.select_related(
            "customer",
            "vehicle",
            "vehicle__brand",
            "vehicle__model",
        ),
        id=booking_id,
    )
    if branch and booking.branch_id != branch.id:
        return render(request, "errors/403.html", status=403)

    context = {
        "title": f"Booking #{booking.id}",
        "page_title": f"Booking #{booking.id}",
        "booking": booking,
    }
    return render(request, "bookings/detail.html", context)


@login_required
def booking_edit_page(request, booking_id: int):
    if not has_perm(request.user, "bookings.update"):
        return render(request, "errors/403.html", status=403)

    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)

    _ensure_edit_session(request, booking)
    return redirect("booking_edit_customer", booking_id=booking.id)


@login_required
def booking_delete_page(request, booking_id: int):
    if not has_perm(request.user, "bookings.delete"):
        return render(request, "errors/403.html", status=403)

    branch = get_active_branch(request)
    booking = get_object_or_404(Booking.objects.select_related("customer", "vehicle"), id=booking_id)
    if branch and booking.branch_id != branch.id:
        return render(request, "errors/403.html", status=403)

    error = ""
    if request.method == "POST":
        try:
            booking.delete()
            return redirect("bookings_page")
        except ProtectedError:
            error = "This booking cannot be deleted because it has related records."

    return render(request, "bookings/booking_delete.html", {"booking": booking, "error": error})


@login_required
def booking_return_page(request, booking_id: int):
    if not has_perm(request.user, "bookings.return"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    booking = get_object_or_404(
        Booking.objects.select_related(
            "customer",
            "vehicle",
            "vehicle__brand",
            "vehicle__model",
        ),
        id=booking_id
    )
    if branch and booking.branch_id != branch.id:
        # simple guard; you can later show a styled 403 page
        return render(request, "errors/403.html", status=403)

    context = {
        "title": "Finalize Return",
        "page_title": "Finalize Return",
        "booking": booking,
        "already_paid": get_booking_net_paid(booking),
        "today": timezone.localdate(),
        "now": timezone.localtime(),
    }
    return render(request, "bookings/return.html", context)


def _wizard_get(request):
    return request.session.get("booking_wizard", {})


def _wizard_set(request, data):
    request.session["booking_wizard"] = data
    request.session.modified = True


def _wizard_clear(request):
    if "booking_wizard" in request.session:
        del request.session["booking_wizard"]
        request.session.modified = True


def _wizard_is_edit(data) -> bool:
    return bool(data.get("edit_mode") and data.get("edit_booking_id"))


def _wizard_urls(data):
    if _wizard_is_edit(data):
        booking_id = data.get("edit_booking_id")
        return f"/bookings/{booking_id}/edit", f"/bookings/{booking_id}/", f"/bookings/{booking_id}/"
    return "/bookings/new", "/bookings/", "/bookings/"


def _wizard_context(data):
    wizard_base, wizard_cancel_url, wizard_finish_url = _wizard_urls(data)
    return {
        "wizard_base": wizard_base,
        "wizard_cancel_url": wizard_cancel_url,
        "wizard_finish_url": wizard_finish_url,
        "edit_mode": _wizard_is_edit(data),
    }


def _wizard_guard(request, data):
    perm = "bookings.update" if _wizard_is_edit(data) else "bookings.create"
    return has_perm(request.user, perm)


def _coerce_int_id(raw_value):
    try:
        value = int(raw_value)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def _get_booking_or_403(request, booking_id: int):
    branch = get_active_branch(request)
    booking = get_object_or_404(
        Booking.objects.select_related(
            "customer",
            "vehicle",
            "vehicle__brand",
            "vehicle__model",
        ),
        id=booking_id,
    )
    if branch and booking.branch_id != branch.id:
        return None
    return booking


def _ensure_edit_session(request, booking):
    data = _wizard_get(request)
    if data.get("edit_booking_id") == booking.id and data.get("edit_mode"):
        return

    drivers = []
    for d in BookingDriver.objects.filter(booking=booking).order_by("id"):
        drivers.append(
            {
                "name": d.name,
                "phone_number": d.phone_number,
                "id_number": d.id_number,
                "license_number": d.license_number,
                "license_expiry_date": d.license_expiry_date.isoformat() if d.license_expiry_date else "",
            }
        )

    extras = []
    for e in BookingExtra.objects.filter(booking=booking).order_by("id"):
        extras.append(
            {
                "name": e.name,
                "qty": e.qty,
                "unit_price": str(e.unit_price),
            }
        )

    try:
        handover = booking.handover
    except BookingHandover.DoesNotExist:
        handover = None

    data = {
        "edit_mode": True,
        "edit_booking_id": booking.id,
        "booking_id": booking.id,
        "customer_mode": "existing",
        "customer_id": str(booking.customer_id),
        "customer_new": {
            "name": booking.customer.name,
            "id_type": booking.customer.id_type or "ID",
            "id_number": booking.customer.id_number or "",
            "phone_number": booking.customer.phone_number or "",
            "email": booking.customer.email or "",
            "address": booking.customer.address or "",
            "license_number": booking.customer.license_number or "",
            "license_issuer": booking.customer.license_issuer or "",
            "license_issue_date": booking.customer.license_issue_date.isoformat() if booking.customer.license_issue_date else "",
            "license_expiry_date": booking.customer.license_expiry_date.isoformat() if booking.customer.license_expiry_date else "",
        },
        "pickup_date": booking.pickup_date.isoformat(),
        "return_date": booking.return_date.isoformat(),
        "vehicle_id": str(booking.vehicle_id),
        "drivers": drivers,
        "extras": extras,
        "vat_rate": str(booking.vat_rate),
        "deposit_amount": str(booking.deposit_amount),
        "notes": booking.notes or "",
        "handover": {
            "odometer_out_km": str(getattr(handover, "odometer_out_km", 0) or 0),
            "fuel_out_percent": str(getattr(handover, "fuel_out_percent", 100) or 100),
            "checklist": {
                "spare": bool(getattr(handover, "accessory_spare", False)),
                "jack": bool(getattr(handover, "accessory_jack", False)),
                "triangle": bool(getattr(handover, "accessory_triangle", False)),
                "docs": bool(getattr(handover, "accessory_docs", False)),
                "child_seat": bool(getattr(handover, "accessory_child_seat", False)),
                "gps": bool(getattr(handover, "accessory_gps", False)),
            },
            "checkout_now": False,
        },
        "customer_signature_data": getattr(handover, "customer_signature_data", "") if handover else "",
    }
    _wizard_set(request, data)


@login_required
def booking_wizard_customer(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)
    mode = data.get("customer_mode", "existing")
    error = ""

    q = (request.GET.get("q") or "").strip()
    customers = Customer.objects.all().order_by("name")
    if q:
        customers = customers.filter(name__icontains=q) | customers.filter(phone_number__icontains=q) | customers.filter(id_number__icontains=q)

    if request.method == "POST":
        mode = request.POST.get("customer_mode") or "existing"
        data["customer_mode"] = mode

        if mode == "existing":
            data["customer_id"] = request.POST.get("customer_id") or ""
            data.pop("customer_new", None)
            if not data["customer_id"]:
                error = "Please select an existing customer."
        else:
            customer_name = (request.POST.get("name") or "").strip()
            data["customer_new"] = {
                "name": customer_name,
                "id_type": request.POST.get("id_type") or "ID",
                "id_number": (request.POST.get("id_number") or "").strip(),
                "phone_number": (request.POST.get("phone_number") or "").strip(),
                "email": (request.POST.get("email") or "").strip(),
                "address": (request.POST.get("address") or "").strip(),
                "license_number": (request.POST.get("license_number") or "").strip(),
                "license_issuer": (request.POST.get("license_issuer") or "").strip(),
                "license_issue_date": request.POST.get("license_issue_date") or "",
                "license_expiry_date": request.POST.get("license_expiry_date") or "",
            }
            data.pop("customer_id", None)
            if not customer_name:
                error = "Please enter a customer name."

        if not error:
            _wizard_set(request, data)
            return redirect("booking_wizard_driver")

    context = {
        "title": "New Booking",
        "step": 1,
        "mode": mode,
        "customers": customers[:200],
        "data": data,
        "q": q,
        "error": error,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/customer.html", context)


@login_required
def booking_wizard_driver(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        drivers = []
        indexes = set()
        for key in request.POST.keys():
            if not key.startswith("driver_name_"):
                continue
            try:
                indexes.add(int(key.split("driver_name_")[-1]))
            except Exception:
                continue

        for idx in sorted(indexes):
            name = (request.POST.get(f"driver_name_{idx}") or "").strip()
            if not name:
                continue
            drivers.append(
                {
                    "name": name,
                    "phone_number": (request.POST.get(f"driver_phone_{idx}") or "").strip(),
                    "id_number": (request.POST.get(f"driver_id_{idx}") or "").strip(),
                    "license_number": (request.POST.get(f"driver_license_{idx}") or "").strip(),
                    "license_expiry_date": request.POST.get(f"driver_expiry_{idx}") or "",
                }
            )

        data["drivers"] = drivers
        _wizard_set(request, data)
        return redirect("booking_wizard_dates")

    context = {
        "title": "New Booking",
        "step": 2,
        "data": data,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/driver.html", context)


@login_required
def booking_wizard_dates(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        data["pickup_date"] = request.POST.get("pickup_date") or ""
        data["return_date"] = request.POST.get("return_date") or ""
        _wizard_set(request, data)
        return redirect("booking_wizard_vehicle")

    context = {
        "title": "New Booking",
        "step": 3,
        "data": data,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/dates.html", context)


def _available_vehicles(branch, pickup, ret, exclude_booking_id=None):
    booked = Booking.objects.filter(
        pickup_date__lt=ret,
        return_date__gt=pickup,
    ).exclude(status__in=["CANCELLED", "RETURNED", "CLOSED"])

    if branch:
        booked = booked.filter(branch=branch)

    if exclude_booking_id:
        booked = booked.exclude(id=exclude_booking_id)

    return Vehicle.objects.exclude(id__in=booked.values_list("vehicle_id", flat=True))


@login_required
def booking_wizard_vehicle(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)
    pickup = data.get("pickup_date")
    ret = data.get("return_date")
    vehicles = []

    branch = get_active_branch(request)
    if pickup and ret:
        try:
            pickup_date = date.fromisoformat(pickup)
            return_date = date.fromisoformat(ret)
            exclude_id = data.get("edit_booking_id") if _wizard_is_edit(data) else None
            vehicles = _available_vehicles(branch, pickup_date, return_date, exclude_booking_id=exclude_id).select_related("brand", "model")
        except Exception:
            vehicles = []

    if request.method == "POST":
        data["vehicle_id"] = request.POST.get("vehicle_id") or ""
        _wizard_set(request, data)
        return redirect("booking_wizard_extras")

    context = {
        "title": "New Booking",
        "step": 4,
        "vehicles": vehicles,
        "data": data,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/vehicle.html", context)


@login_required
def booking_wizard_extras(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        extras = []
        for key in ["baby_seat", "gps", "driver_service", "fuel_package", "wifi_router"]:
            if request.POST.get(f"extra_{key}"):
                extras.append(
                    {
                        "key": key,
                        "name": request.POST.get(f"extra_label_{key}") or key.replace("_", " ").title(),
                        "qty": int(request.POST.get(f"extra_qty_{key}") or 1),
                        "unit_price": request.POST.get(f"extra_rate_{key}") or "0",
                    }
                )
        data["extras"] = extras
        _wizard_set(request, data)
        return redirect("booking_wizard_pricing")

    extras_map = {
        "baby_seat": {"checked": False, "rate": "2.000", "qty": "1"},
        "gps": {"checked": False, "rate": "1.000", "qty": "1"},
        "driver_service": {"checked": False, "rate": "10.000", "qty": "1"},
        "fuel_package": {"checked": False, "rate": "5.000", "qty": "1"},
        "wifi_router": {"checked": False, "rate": "3.000", "qty": "1"},
    }
    labels = {
        "baby_seat": "Baby Seat",
        "gps": "GPS",
        "driver_service": "Driver Service",
        "fuel_package": "Fuel Package",
        "wifi_router": "WiFi Router",
    }
    for e in data.get("extras") or []:
        name = (e.get("name") or "").strip().lower()
        key = e.get("key")
        if key in extras_map:
            extras_map[key]["checked"] = True
            extras_map[key]["rate"] = str(e.get("unit_price") or extras_map[key]["rate"])
            extras_map[key]["qty"] = str(e.get("qty") or extras_map[key]["qty"])
            continue
        for k, label in labels.items():
            if name == label.lower() or name == k.replace("_", " "):
                extras_map[k]["checked"] = True
                extras_map[k]["rate"] = str(e.get("unit_price") or extras_map[k]["rate"])
                extras_map[k]["qty"] = str(e.get("qty") or extras_map[k]["qty"])
                break

    context = {
        "title": "New Booking",
        "step": 5,
        "data": data,
        "extras_map": extras_map,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/extras.html", context)


@login_required
def booking_wizard_pricing(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)
    vehicle = None
    daily_rate = 0
    if data.get("vehicle_id"):
        vehicle = Vehicle.objects.filter(id=data.get("vehicle_id")).first()
        try:
            daily_rate = float(getattr(vehicle, "daily_rate", 0) or 0)
        except Exception:
            daily_rate = 0

    days = 0
    extras_total = 0
    if data.get("pickup_date") and data.get("return_date"):
        try:
            pickup = date.fromisoformat(data.get("pickup_date"))
            ret = date.fromisoformat(data.get("return_date"))
            days = max((ret - pickup).days, 1)
        except Exception:
            days = 0

    for e in data.get("extras") or []:
        try:
            qty = int(e.get("qty") or 1)
            unit = float(e.get("unit_price") or 0)
            extras_total += qty * unit
        except Exception:
            continue

    if request.method == "POST":
        data["vat_rate"] = request.POST.get("vat_rate") or "0"
        data["deposit_amount"] = request.POST.get("deposit_amount") or ""
        data["notes"] = (request.POST.get("notes") or "").strip()
        _wizard_set(request, data)
        return redirect("booking_wizard_signature")

    context = {
        "title": "New Booking",
        "step": 6,
        "data": data,
        "vehicle": vehicle,
        "days": days,
        "extras_total": extras_total,
        "daily_rate": daily_rate,
        "subtotal": (daily_rate * days) + extras_total,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/pricing.html", context)


@login_required
def booking_wizard_signature(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        data["customer_signature_data"] = request.POST.get("signature_data") or ""
        _wizard_set(request, data)
        return redirect("booking_wizard_handover")

    context = {
        "title": "New Booking",
        "step": 7,
        "data": data,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/signature.html", context)


@login_required
def booking_wizard_handover(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        data["handover"] = {
            "odometer_out_km": request.POST.get("odometer_out_km") or "0",
            "fuel_out_percent": request.POST.get("fuel_out_percent") or "100",
            "checklist": {
                "spare": bool(request.POST.get("checklist_spare")),
                "jack": bool(request.POST.get("checklist_jack")),
                "triangle": bool(request.POST.get("checklist_triangle")),
                "docs": bool(request.POST.get("checklist_docs")),
                "child_seat": bool(request.POST.get("checklist_child_seat")),
                "gps": bool(request.POST.get("checklist_gps")),
            },
            "inspector_signature_data": request.POST.get("inspector_signature_data") or "",
            "checkout_now": bool(request.POST.get("checkout_now")),
        }
        _wizard_set(request, data)
        return redirect("booking_wizard_documents")

    context = {
        "title": "New Booking",
        "step": 8,
        "data": data,
        "now": timezone.now(),
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/handover.html", context)


@login_required
def booking_wizard_documents(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)
    booking_id = data.get("booking_id")
    error = ""

    if _wizard_is_edit(data):
        if not booking_id:
            error = "Missing booking id for edit."
        else:
            booking = _get_booking_or_403(request, booking_id)
            if not booking:
                return render(request, "errors/403.html", status=403)

            customer = None
            mode = data.get("customer_mode", "existing")
            if mode == "existing" and data.get("customer_id"):
                customer_id = _coerce_int_id(data.get("customer_id"))
                if customer_id:
                    customer = Customer.objects.filter(id=customer_id).first()
                if not customer:
                    error = "Please select an existing customer."
            else:
                cdata = data.get("customer_new") or {}
                if cdata.get("name"):
                    customer = Customer.objects.create(
                        name=cdata.get("name"),
                        id_type=cdata.get("id_type") or "ID",
                        id_number=cdata.get("id_number") or "",
                        phone_number=cdata.get("phone_number") or "",
                        email=cdata.get("email") or "",
                        address=cdata.get("address") or "",
                        license_number=cdata.get("license_number") or "",
                        license_issuer=cdata.get("license_issuer") or "",
                        license_issue_date=cdata.get("license_issue_date") or None,
                        license_expiry_date=cdata.get("license_expiry_date") or None,
                    )
                else:
                    error = "Please enter a customer name."

            vehicle_id = _coerce_int_id(data.get("vehicle_id"))
            vehicle = Vehicle.objects.filter(id=vehicle_id).first() if vehicle_id else None
            if not vehicle and not error:
                error = "Please select a vehicle."
            pickup = data.get("pickup_date")
            ret = data.get("return_date")
            if (not pickup or not ret) and not error:
                error = "Please select rental dates."

            if customer and vehicle and pickup and ret and not error:
                try:
                    booking = update_booking(
                        booking,
                        customer=customer,
                        vehicle=vehicle,
                        pickup_date=date.fromisoformat(pickup),
                        return_date=date.fromisoformat(ret),
                        daily_rate=vehicle.daily_rate,
                        deposit_amount=data.get("deposit_amount") or vehicle.deposit,
                        vat_rate=data.get("vat_rate") or "0",
                        extras=data.get("extras") or [],
                        notes=data.get("notes") or "",
                    )

                    BookingDriver.objects.filter(booking=booking).delete()
                    for d in data.get("drivers") or []:
                        BookingDriver.objects.create(
                            booking=booking,
                            name=d.get("name") or "",
                            phone_number=d.get("phone_number") or "",
                            id_number=d.get("id_number") or "",
                            license_number=d.get("license_number") or "",
                            license_expiry_date=d.get("license_expiry_date") or None,
                        )

                    handover = data.get("handover") or {}
                    if handover.get("checkout_now") and booking.pickup_date <= timezone.localdate():
                        checkout_booking(
                            booking,
                            inspector=request.user,
                            odometer_out_km=handover.get("odometer_out_km") or 0,
                            fuel_out_percent=handover.get("fuel_out_percent") or 100,
                            checklist=handover.get("checklist") or {},
                            customer_signature_data=data.get("customer_signature_data") or "",
                        )
                    else:
                        try:
                            odo_val = int(handover.get("odometer_out_km") or 0)
                        except Exception:
                            odo_val = 0
                        try:
                            fuel_val = int(handover.get("fuel_out_percent") or 100)
                        except Exception:
                            fuel_val = 100
                        checklist = handover.get("checklist") or {}
                        BookingHandover.objects.update_or_create(
                            booking=booking,
                            defaults={
                                "inspector": request.user,
                                "timestamp": timezone.now(),
                                "odometer_out_km": max(odo_val, 0),
                                "fuel_out_percent": max(min(fuel_val, 100), 0),
                                "accessory_spare": bool(checklist.get("spare")),
                                "accessory_jack": bool(checklist.get("jack")),
                                "accessory_triangle": bool(checklist.get("triangle")),
                                "accessory_docs": bool(checklist.get("docs")),
                                "accessory_child_seat": bool(checklist.get("child_seat")),
                                "accessory_gps": bool(checklist.get("gps")),
                                "customer_signature_data": data.get("customer_signature_data") or "",
                            },
                        )

                    data["booking_id"] = booking.id
                    _wizard_set(request, data)
                    booking_id = booking.id
                except BookingError as exc:
                    error = str(exc) or "Unable to update booking."
                except ValueError:
                    error = "Invalid pickup or return date."

    if not booking_id and not _wizard_is_edit(data):
        # create booking from wizard data
        customer = None
        mode = data.get("customer_mode", "existing")
        if mode == "existing" and data.get("customer_id"):
            customer_id = _coerce_int_id(data.get("customer_id"))
            if customer_id:
                customer = Customer.objects.filter(id=customer_id).first()
            if not customer:
                error = "Please select an existing customer."
        else:
            cdata = data.get("customer_new") or {}
            if cdata.get("name"):
                customer = Customer.objects.create(
                    name=cdata.get("name"),
                    id_type=cdata.get("id_type") or "ID",
                    id_number=cdata.get("id_number") or "",
                    phone_number=cdata.get("phone_number") or "",
                    email=cdata.get("email") or "",
                    address=cdata.get("address") or "",
                    license_number=cdata.get("license_number") or "",
                    license_issuer=cdata.get("license_issuer") or "",
                    license_issue_date=cdata.get("license_issue_date") or None,
                    license_expiry_date=cdata.get("license_expiry_date") or None,
                )
            else:
                error = "Please enter a customer name."

        vehicle_id = _coerce_int_id(data.get("vehicle_id"))
        vehicle = Vehicle.objects.filter(id=vehicle_id).first() if vehicle_id else None
        if not vehicle and not error:
            error = "Please select a vehicle."
        pickup = data.get("pickup_date")
        ret = data.get("return_date")
        if (not pickup or not ret) and not error:
            error = "Please select rental dates."

        if customer and vehicle and pickup and ret:
            try:
                booking = create_booking(
                    branch=get_active_branch(request),
                    created_by=request.user,
                    customer=customer,
                    vehicle=vehicle,
                    pickup_date=date.fromisoformat(pickup),
                    return_date=date.fromisoformat(ret),
                    daily_rate=vehicle.daily_rate,
                    deposit_amount=data.get("deposit_amount") or vehicle.deposit,
                    vat_rate=data.get("vat_rate") or "0",
                    extras=data.get("extras") or [],
                    status="CONFIRMED",
                    notes=data.get("notes") or "",
                )

                for d in data.get("drivers") or []:
                    BookingDriver.objects.create(
                        booking=booking,
                        name=d.get("name") or "",
                        phone_number=d.get("phone_number") or "",
                        id_number=d.get("id_number") or "",
                        license_number=d.get("license_number") or "",
                        license_expiry_date=d.get("license_expiry_date") or None,
                    )

                handover = data.get("handover") or {}
                # If user chose to checkout now (and pickup date allows), perform full checkout which sets status
                if handover.get("checkout_now") and booking.pickup_date <= timezone.localdate():
                    checkout_booking(
                        booking,
                        inspector=request.user,
                        odometer_out_km=handover.get("odometer_out_km") or 0,
                        fuel_out_percent=handover.get("fuel_out_percent") or 100,
                        checklist=handover.get("checklist") or {},
                        customer_signature_data=data.get("customer_signature_data") or "",
                    )
                else:
                    # Persist handover details to BookingHandover even if not checking out now,
                    # so documents like the agreement can display the entered odometer/fuel values.
                    try:
                        odo_val = int(handover.get("odometer_out_km") or 0)
                    except Exception:
                        odo_val = 0
                    try:
                        fuel_val = int(handover.get("fuel_out_percent") or 100)
                    except Exception:
                        fuel_val = 100
                    checklist = handover.get("checklist") or {}
                    has_handover_data = odo_val > 0 or fuel_val != 100 or any(checklist.values()) or bool(data.get("customer_signature_data"))
                    if has_handover_data:
                        BookingHandover.objects.update_or_create(
                            booking=booking,
                            defaults={
                                "inspector": request.user,
                                "timestamp": timezone.now(),
                                "odometer_out_km": max(odo_val, 0),
                                "fuel_out_percent": max(min(fuel_val, 100), 0),
                                "accessory_spare": bool(checklist.get("spare")),
                                "accessory_jack": bool(checklist.get("jack")),
                                "accessory_triangle": bool(checklist.get("triangle")),
                                "accessory_docs": bool(checklist.get("docs")),
                                "accessory_child_seat": bool(checklist.get("child_seat")),
                                "accessory_gps": bool(checklist.get("gps")),
                                "customer_signature_data": data.get("customer_signature_data") or "",
                            },
                        )

                data["booking_id"] = booking.id
                _wizard_set(request, data)
                booking_id = booking.id
            except BookingError as exc:
                error = str(exc) or "Unable to create booking."
            except ValueError:
                error = "Invalid pickup or return date."

    context = {
        "title": "Booking Documents",
        "step": 9,
        "data": data,
        "booking_id": booking_id,
        "error": error,
        **_wizard_context(data),
    }
    return render(request, "bookings/wizard/documents.html", context)


@login_required
def booking_wizard_finish(request):
    data = _wizard_get(request)
    if not _wizard_guard(request, data):
        return render(request, "errors/403.html", status=403)
    booking_id = data.get("edit_booking_id") if _wizard_is_edit(data) else None
    _wizard_clear(request)
    if booking_id:
        return redirect("booking_detail_page", booking_id=booking_id)
    return redirect("bookings_page")


@login_required
def booking_edit_customer(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_customer(request)


@login_required
def booking_edit_driver(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_driver(request)


@login_required
def booking_edit_dates(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_dates(request)


@login_required
def booking_edit_vehicle(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_vehicle(request)


@login_required
def booking_edit_extras(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_extras(request)


@login_required
def booking_edit_pricing(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_pricing(request)


@login_required
def booking_edit_signature(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_signature(request)


@login_required
def booking_edit_handover(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_handover(request)


@login_required
def booking_edit_documents(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_documents(request)


@login_required
def booking_edit_finish(request, booking_id: int):
    booking = _get_booking_or_403(request, booking_id)
    if not booking:
        return render(request, "errors/403.html", status=403)
    _ensure_edit_session(request, booking)
    return booking_wizard_finish(request)
