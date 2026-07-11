from datetime import timedelta

from django.core.cache import cache
from django.utils import timezone
from django.db.models import Sum, Q
from django.db.models.functions import ExtractMonth, TruncDate

from apps.accounts.permissions import has_perm
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment
from apps.settings_app.models import BusinessProfile


def _cache_key(name: str, active_branch=None, **kwargs) -> str:
    branch_id = getattr(active_branch, "id", "global")
    stable = "|".join(f"{k}={kwargs[k]}" for k in sorted(kwargs))
    return f"dashboard:{name}:branch={branch_id}:{stable}"


def _cached(name: str, ttl: int, active_branch=None, compute=None, **kwargs):
    key = _cache_key(name, active_branch=active_branch, **kwargs)
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = compute()
    cache.set(key, value, ttl)
    return value


def _pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 100.0 if current > 0 else 0.0
    return round(((current - previous) / previous) * 100, 1)


def get_dashboard_kpis(active_branch=None) -> dict:
    today = timezone.localdate()

    def _compute():
        qs_booking = Booking.objects.all()
        qs_vehicle = Vehicle.objects.all()
        qs_customer = Customer.objects.all()
        qs_payment = Payment.objects.filter(status="PAID")
        qs_maintenance = MaintenanceTask.objects.all()

        if active_branch:
            qs_booking = qs_booking.filter(branch=active_branch)
            qs_vehicle = qs_vehicle.filter(branch=active_branch)
            qs_payment = qs_payment.filter(branch=active_branch)
            qs_maintenance = qs_maintenance.filter(branch=active_branch)

        month_start = today.replace(day=1)
        prev_month_end = month_start - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        total_bookings = qs_booking.exclude(status="CANCELLED").count()
        if active_branch:
            active_customers = qs_booking.exclude(status="CANCELLED").values("customer_id").distinct().count()
        else:
            active_customers = qs_customer.filter(is_active=True).count()
        fleet_vehicles = qs_vehicle.count()

        active_rentals = qs_booking.filter(status="CHECKED_OUT").count()
        today_pickups = qs_booking.filter(pickup_date=today).exclude(status="CANCELLED").count()
        today_returns = qs_booking.filter(return_date=today).exclude(status="CANCELLED").count()
        overdue = qs_booking.filter(status="CHECKED_OUT", return_date__lt=today).count()

        earnings = qs_payment.aggregate(s=Sum("amount"))["s"] or 0
        current_bookings = qs_booking.exclude(status="CANCELLED").filter(created_at__date__gte=month_start, created_at__date__lte=today).count()
        prev_bookings = qs_booking.exclude(status="CANCELLED").filter(created_at__date__gte=prev_month_start, created_at__date__lte=prev_month_end).count()

        current_customers = qs_customer.filter(created_at__date__gte=month_start, created_at__date__lte=today).count()
        prev_customers = qs_customer.filter(created_at__date__gte=prev_month_start, created_at__date__lte=prev_month_end).count()

        current_fleet = qs_vehicle.filter(created_at__date__gte=month_start, created_at__date__lte=today).count()
        prev_fleet = qs_vehicle.filter(created_at__date__gte=prev_month_start, created_at__date__lte=prev_month_end).count()

        current_earnings = qs_payment.filter(payment_date__gte=month_start, payment_date__lte=today).aggregate(s=Sum("amount"))["s"] or 0
        prev_earnings = qs_payment.filter(payment_date__gte=prev_month_start, payment_date__lte=prev_month_end).aggregate(s=Sum("amount"))["s"] or 0

        due_vehicles = 0
        for vehicle in qs_vehicle.only("odometer_km", "last_service_odometer", "service_interval_km"):
            interval = int(vehicle.service_interval_km or 0)
            if interval > 0 and int(vehicle.odometer_km or 0) >= int(vehicle.last_service_odometer or 0) + interval:
                due_vehicles += 1

        expiring_documents = qs_vehicle.filter(
            Q(registration_expiry__gte=today, registration_expiry__lte=today + timedelta(days=30))
            | Q(insurance_expiry__gte=today, insurance_expiry__lte=today + timedelta(days=30))
        ).count()
        open_maintenance = qs_maintenance.filter(status__in=["OPEN", "IN_PROGRESS"]).count()
        fleet_utilization = round((active_rentals / fleet_vehicles) * 100, 1) if fleet_vehicles else 0.0

        return {
            "total_bookings": total_bookings,
            "active_customers": active_customers,
            "fleet_vehicles": fleet_vehicles,
            "earnings": float(earnings),
            "trend_total_bookings": _pct_change(current_bookings, prev_bookings),
            "trend_active_customers": _pct_change(current_customers, prev_customers),
            "trend_fleet_vehicles": _pct_change(current_fleet, prev_fleet),
            "trend_earnings": _pct_change(float(current_earnings), float(prev_earnings)),
            "active_rentals": active_rentals,
            "today_pickups": today_pickups,
            "today_returns": today_returns,
            "overdue_rentals": overdue,
            "fleet_utilization": fleet_utilization,
            "upcoming_services": due_vehicles,
            "expiring_documents": expiring_documents,
            "maintenance_open": open_maintenance,
        }

    return _cached(
        "kpis",
        ttl=120,
        active_branch=active_branch,
        compute=_compute,
        day=today.isoformat(),
    )


def get_recent_reservations(active_branch=None, limit: int = 5) -> list[dict]:
    qs = Booking.objects.select_related(
        "customer",
        "vehicle",
        "vehicle__brand",
        "vehicle__model",
    ).exclude(status="CANCELLED").order_by("-created_at")
    if active_branch:
        qs = qs.filter(branch=active_branch)

    rows = []
    for b in qs[:limit]:
        vehicle = b.vehicle
        vehicle_name = ""
        if vehicle:
            vehicle_name = f"{getattr(vehicle.brand, 'name', '')} {getattr(vehicle.model, 'name', '')}".strip()
        rows.append(
            {
                "booking_id": b.id,
                "customer": getattr(b.customer, "name", ""),
                "pickup": b.pickup_date.isoformat() if b.pickup_date else "",
                "pickup_time": b.pickup_time.strftime("%H:%M") if b.pickup_time else "",
                "vehicle": vehicle_name or getattr(vehicle, "plate_number", ""),
            }
        )
    return rows


def get_recent_bookings(active_branch=None, limit: int = 5) -> list[dict]:
    qs = Booking.objects.select_related("customer").exclude(status="CANCELLED").order_by("-created_at")
    if active_branch:
        qs = qs.filter(branch=active_branch)

    rows = []
    for b in qs[:limit]:
        rows.append(
            {
                "booking_id": b.id,
                "ref": b.reference or f"#{b.id}",
                "customer": getattr(b.customer, "name", ""),
                "date": b.created_at.date().isoformat() if b.created_at else "",
                "amount": f"{float(b.total_amount or 0):.3f}",
            }
        )
    return rows


def get_recent_payments(active_branch=None, limit: int = 5) -> list[dict]:
    business = BusinessProfile.get_solo()
    qs = Payment.objects.select_related("booking", "booking__customer").filter(status="PAID").order_by("-payment_date", "-id")
    if active_branch:
        qs = qs.filter(branch=active_branch)

    rows = []
    for p in qs[:limit]:
        customer = ""
        if p.booking and p.booking.customer_id:
            customer = p.booking.customer.name
        currency = p.currency_code or business.currency_code or ""
        rows.append(
            {
                "payment_id": p.id,
                "customer": customer,
                "date": p.payment_date.isoformat() if p.payment_date else "",
                "amount": f"{float(p.amount or 0):.3f}",
                "currency": currency,
                "status": p.status,
            }
        )
    return rows


def get_earnings_chart(active_branch=None, period: str = "year") -> dict:
    today = timezone.localdate()
    cache_key_date = today.replace(day=1).isoformat() if period in {"month", "year"} else today.isoformat()

    def _compute():
        qs = Payment.objects.filter(status="PAID")
        if active_branch:
            qs = qs.filter(branch=active_branch)

        def _chart_points(values: list[float], labels: list[str], width: int = 520, height: int = 160, pad: int = 20):
            max_val = max(values) if values else 0
            if max_val <= 0:
                max_val = 1
            step = (width - (pad * 2)) / max(1, (len(values) - 1))
            points = []
            point_list = []
            for i, v in enumerate(values):
                x = pad + (step * i)
                y = height - pad - ((v / max_val) * (height - (pad * 2)))
                points.append(f"{x:.1f},{y:.1f}")
                point_list.append({"x": f"{x:.1f}", "y": f"{y:.1f}", "label": labels[i], "value": f"{v:.3f}"})
            return " ".join(points), point_list

        if period == "month":
            start = today.replace(day=1)
            end = today
            prev_end = start - timedelta(days=1)
            prev_start = prev_end.replace(day=1)
            label_count = (end - start).days + 1
            labels = [str(d.day) for d in (start + timedelta(days=i) for i in range(label_count))]

            def _series_range(s, e):
                series = [0.0] * ((e - s).days + 1)
                try:
                    rows = (
                        qs.filter(payment_date__gte=s, payment_date__lte=e)
                        .annotate(day=TruncDate("payment_date"))
                        .values("day")
                        .annotate(total=Sum("amount"))
                        .order_by("day")
                    )
                    for r in rows:
                        idx = (r["day"] - s).days
                        if 0 <= idx < len(series):
                            series[idx] = float(r["total"] or 0)
                except Exception:
                    qs_fallback = qs.filter(payment_date__gte=s, payment_date__lte=e).only("payment_date", "amount")
                    for p in qs_fallback:
                        pd = p.payment_date
                        try:
                            pd_date = pd.date() if hasattr(pd, "date") else pd
                        except Exception:
                            pd_date = pd
                        try:
                            idx = (pd_date - s).days
                        except Exception:
                            continue
                        if 0 <= idx < len(series):
                            series[idx] += float(p.amount or 0)
                return series

            current = _series_range(start, end)
            previous = _series_range(prev_start, prev_end)
            previous = previous[:len(current)]
            points_current, dots_current = _chart_points(current, labels)
            points_prev, dots_prev = _chart_points(previous, labels)
            return {
                "period": "month",
                "label_primary": "This Month",
                "label_secondary": "Last Month",
                "labels": labels,
                "primary_points": points_current,
                "secondary_points": points_prev,
                "primary_dots": dots_current,
                "secondary_dots": dots_prev,
            }

        if period == "week":
            start = today - timedelta(days=today.weekday())
            end = start + timedelta(days=6)
            prev_start = start - timedelta(days=7)
            prev_end = end - timedelta(days=7)
            labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            def _series_range(s, e):
                series = [0.0] * 7
                try:
                    rows = (
                        qs.filter(payment_date__gte=s, payment_date__lte=e)
                        .annotate(day=TruncDate("payment_date"))
                        .values("day")
                        .annotate(total=Sum("amount"))
                        .order_by("day")
                    )
                    for r in rows:
                        idx = (r["day"] - s).days
                        if 0 <= idx < 7:
                            series[idx] = float(r["total"] or 0)
                except Exception:
                    qs_fallback = qs.filter(payment_date__gte=s, payment_date__lte=e).only("payment_date", "amount")
                    for p in qs_fallback:
                        pd = p.payment_date
                        try:
                            pd_date = pd.date() if hasattr(pd, "date") else pd
                        except Exception:
                            pd_date = pd
                        try:
                            idx = (pd_date - s).days
                        except Exception:
                            continue
                        if 0 <= idx < 7:
                            series[idx] += float(p.amount or 0)
                return series

            current = _series_range(start, end)
            previous = _series_range(prev_start, prev_end)
            points_current, dots_current = _chart_points(current, labels)
            points_prev, dots_prev = _chart_points(previous, labels)
            return {
                "period": "week",
                "label_primary": "This Week",
                "label_secondary": "Last Week",
                "labels": labels,
                "primary_points": points_current,
                "secondary_points": points_prev,
                "primary_dots": dots_current,
                "secondary_dots": dots_prev,
            }

        year = today.year
        last_year = year - 1
        labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

        def _series(target_year: int) -> list[float]:
            series = [0.0] * 12
            try:
                rows = (
                    qs.filter(payment_date__year=target_year)
                    .annotate(month=ExtractMonth("payment_date"))
                    .values("month")
                    .annotate(total=Sum("amount"))
                    .order_by("month")
                )
                for r in rows:
                    m = int(r["month"] or 0)
                    if 1 <= m <= 12:
                        series[m - 1] = float(r["total"] or 0)
            except Exception:
                qs_fallback = qs.filter(payment_date__year=target_year).only("payment_date", "amount")
                for p in qs_fallback:
                    pd = p.payment_date
                    try:
                        m = pd.month if hasattr(pd, "month") else int(pd.strftime("%m"))
                    except Exception:
                        continue
                    if 1 <= m <= 12:
                        series[m - 1] += float(p.amount or 0)
            return series

        current = _series(year)
        previous = _series(last_year)
        points_current, dots_current = _chart_points(current, labels)
        points_prev, dots_prev = _chart_points(previous, labels)
        return {
            "period": "year",
            "label_primary": "This Year",
            "label_secondary": "Last Year",
            "labels": labels,
            "primary_points": points_current,
            "secondary_points": points_prev,
            "primary_dots": dots_current,
            "secondary_dots": dots_prev,
        }

    return _cached(
        "earnings_chart",
        ttl=300,
        active_branch=active_branch,
        compute=_compute,
        period=period,
        day=cache_key_date,
    )


def get_global_search_results(*, query: str, user, active_branch=None, limit_per_group: int = 5) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []

    groups: list[dict] = []

    if has_perm(user, "bookings.view"):
        bookings = Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").exclude(status="CANCELLED")
        if active_branch:
            bookings = bookings.filter(branch=active_branch)
        bookings = bookings.filter(
            Q(reference__icontains=query)
            | Q(customer__name__icontains=query)
            | Q(customer__phone_number__icontains=query)
            | Q(vehicle__plate_number__icontains=query)
        ).order_by("-created_at")

        items = []
        for booking in bookings[:limit_per_group]:
            vehicle_label = ""
            if booking.vehicle_id:
                vehicle_label = f"{getattr(booking.vehicle.brand, 'name', '')} {getattr(booking.vehicle.model, 'name', '')} {booking.vehicle.plate_number}".strip()
            items.append(
                {
                    "title": booking.reference or f"Booking #{booking.id}",
                    "subtitle": f"{booking.customer.name} · {vehicle_label or '-'}",
                    "meta": f"{booking.pickup_date} → {booking.return_date}",
                    "url": f"/bookings/{booking.id}/",
                }
            )
        if items:
            groups.append({"label": "Bookings", "items": items})

    if has_perm(user, "customers.view"):
        customers = Customer.objects.filter(
            Q(name__icontains=query)
            | Q(phone_number__icontains=query)
            | Q(id_number__icontains=query)
            | Q(email__icontains=query)
        ).order_by("name")

        items = [
            {
                "title": customer.name,
                "subtitle": customer.phone_number or customer.email or customer.id_number or "Customer",
                "meta": customer.license_number or customer.address or "",
                "url": f"/customers/{customer.id}/edit/",
            }
            for customer in customers[:limit_per_group]
        ]
        if items:
            groups.append({"label": "Customers", "items": items})

    if has_perm(user, "fleet.view"):
        vehicles = Vehicle.objects.select_related("brand", "model").filter(
            Q(plate_number__icontains=query)
            | Q(vin__icontains=query)
            | Q(brand__name__icontains=query)
            | Q(model__name__icontains=query)
            | Q(tags__icontains=query)
        ).order_by("plate_number")
        if active_branch:
            vehicles = vehicles.filter(branch=active_branch)

        items = [
            {
                "title": vehicle.plate_number,
                "subtitle": f"{vehicle.brand.name} {vehicle.model.name} · {vehicle.status.title()}",
                "meta": f"{vehicle.year} · Rate {float(vehicle.daily_rate or 0):.3f}",
                "url": f"/vehicles/{vehicle.id}/edit/",
            }
            for vehicle in vehicles[:limit_per_group]
        ]
        if items:
            groups.append({"label": "Vehicles", "items": items})

    if has_perm(user, "payments.view"):
        payments = Payment.objects.select_related("booking", "booking__customer").filter(
            Q(receipt_number__icontains=query)
            | Q(booking__reference__icontains=query)
            | Q(booking__customer__name__icontains=query)
        ).order_by("-payment_date", "-id")
        if active_branch:
            payments = payments.filter(branch=active_branch)

        items = [
            {
                "title": payment.receipt_number,
                "subtitle": payment.booking.customer.name if payment.booking_id else "Payment",
                "meta": f"{payment.payment_date} · {payment.currency_code} {float(payment.amount or 0):.3f}",
                "url": f"/payments/{payment.id}/edit/",
            }
            for payment in payments[:limit_per_group]
        ]
        if items:
            groups.append({"label": "Payments", "items": items})

    if has_perm(user, "maintenance.view"):
        maintenance = MaintenanceTask.objects.select_related("vehicle", "vehicle__brand", "vehicle__model").filter(
            Q(notes__icontains=query)
            | Q(vehicle__plate_number__icontains=query)
            | Q(vehicle__brand__name__icontains=query)
            | Q(vehicle__model__name__icontains=query)
        ).order_by("-task_date", "-id")
        if active_branch:
            maintenance = maintenance.filter(branch=active_branch)

        items = []
        for task in maintenance[:limit_per_group]:
            vehicle = task.vehicle
            items.append(
                {
                    "title": f"{vehicle.plate_number} · {task.task_type.title()}",
                    "subtitle": f"{getattr(vehicle.brand, 'name', '')} {getattr(vehicle.model, 'name', '')}".strip(),
                    "meta": f"{task.status.replace('_', ' ').title()} · Due {task.due_date or '-'}",
                    "url": "/maintenance/",
                }
            )
        if items:
            groups.append({"label": "Maintenance", "items": items})

    return groups
