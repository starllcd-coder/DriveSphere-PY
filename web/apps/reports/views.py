from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Sum, Max
from django.db.models.functions import TruncMonth, TruncDate
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.core.services import get_active_branch
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment, Refund
from apps.documents.pdf_html import render_pdf_from_template
from apps.settings_app.models import BusinessProfile
from apps.settings_app.services import get_next_document_number
from apps.accounts.permissions import has_perm
from .services import (
    get_overview,
    get_revenue_breakdown,
    get_financial,
    get_fleet,
    get_customers,
    get_maintenance,
    get_predictive_insights,
    detect_anomalies,
    create_accounting_export,
)
from .models import AnomalyEvent


# -------------------------
# PAGES
# -------------------------
@login_required
def reports_page(request):
    if not (
        has_perm(request.user, "reports.view")
        or has_perm(request.user, "reports.view_financial")
        or has_perm(request.user, "reports.view_maintenance")
        or has_perm(request.user, "reports.view_limited")
    ):
        return render(request, "errors/403.html", status=403)
    return render(request, "reports/index.html")


def _has_reports_access(user, perm_code: str | None = None) -> bool:
    if has_perm(user, "reports.view"):
        return True
    if perm_code and has_perm(user, perm_code):
        return True
    return False


# -------------------------
# Helpers
# -------------------------
def _month_axis(last_n_months: int = 6):
    """Return list of month starts (date) for last_n_months ending at current month."""
    today = timezone.localdate()
    cur = today.replace(day=1)
    # go back (n-1) months
    for _ in range(last_n_months - 1):
        cur = (cur - timedelta(days=1)).replace(day=1)
    axis = []
    for _ in range(last_n_months):
        axis.append(cur)
        cur = (cur.replace(day=28) + timedelta(days=4)).replace(day=1)
    return axis


def _day_axis(start, end):
    axis = []
    cur = start
    while cur <= end:
        axis.append(cur)
        cur = cur + timedelta(days=1)
    return axis


def _apply_branch(qs, branch, field_name: str = "branch"):
    if branch:
        return qs.filter(**{field_name: branch})
    return qs


def _range_for(period: str):
    today = timezone.localdate()
    if period == "today":
        start = today
        end = today
    elif period == "weekly":
        start = today - timedelta(days=6)
        end = today
    else:
        start = today - timedelta(days=29)
        end = today
    return start, end


def _resolve_report_filters(request, default_period: str = "monthly"):
    period = (request.GET.get("period") or default_period).strip().lower()
    if period not in {"today", "weekly", "monthly"}:
        period = default_period

    start, end = _range_for(period)
    custom_from_raw = (request.GET.get("date_from") or request.GET.get("from") or "").strip()
    custom_to_raw = (request.GET.get("date_to") or request.GET.get("to") or "").strip()
    is_custom = False
    if custom_from_raw and custom_to_raw:
        custom_from = parse_date(custom_from_raw)
        custom_to = parse_date(custom_to_raw)
        if custom_from and custom_to:
            if custom_from > custom_to:
                custom_from, custom_to = custom_to, custom_from
            start, end = custom_from, custom_to
            is_custom = True
    return period, start, end, is_custom


def _print_base_context():
    business = BusinessProfile.get_solo()
    return {
        "business": business,
        "now": timezone.now().strftime("%Y-%m-%d %H:%M"),
    }


def _append_query(path: str, request, extra: dict | None = None) -> str:
    query = request.GET.copy()
    if extra:
        for key, value in extra.items():
            query[key] = value
    query_str = query.urlencode()
    return f"{path}?{query_str}" if query_str else path


def _vehicle_display(vehicle):
    if not vehicle:
        return ""
    brand = getattr(vehicle, "brand", None)
    model = getattr(vehicle, "model", None)
    brand_name = getattr(brand, "name", "") if brand else ""
    model_name = getattr(model, "name", "") if model else ""
    return f"{vehicle.plate_number} - {brand_name} {model_name}".strip()


def _safe_related(obj, attr):
    try:
        return getattr(obj, attr)
    except ObjectDoesNotExist:
        return None


def _date_key(value):
    return value.date() if hasattr(value, "date") else value


def _revenue_table_rows(period: str, branch, start=None, end=None):
    if start is None or end is None:
        start, end = _range_for(period)
    qs = Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end)
    if branch:
        qs = qs.filter(branch=branch)
    qs = qs.select_related(
        "booking",
        "booking__customer",
        "booking__vehicle",
        "booking__vehicle__brand",
        "booking__vehicle__model",
        "booking__handover",
        "booking__return_report",
    ).order_by("-payment_date", "-id")

    rows = []
    for payment in qs[:2000]:
        booking = payment.booking
        customer_name = booking.customer.name if booking and booking.customer_id else ""
        vehicle_name = _vehicle_display(booking.vehicle) if booking and booking.vehicle_id else ""

        distance = ""
        handover = _safe_related(booking, "handover")
        ret = _safe_related(booking, "return_report")
        if handover and ret:
            try:
                distance = max(ret.odometer_in_km - handover.odometer_out_km, 0)
            except TypeError:
                distance = ""

        rows.append(
            {
                "date": payment.payment_date.isoformat() if payment.payment_date else "",
                "trip_id": booking.id if booking else "",
                "customer": customer_name,
                "vehicle": vehicle_name,
                "distance": distance,
                "fare": str(booking.subtotal_amount) if booking else "0",
                "tax": str(booking.vat_amount) if booking else "0",
                "discount": "0",
                "total": str(booking.total_amount) if booking else str(payment.amount),
                "method": payment.method,
                "status": payment.status,
            }
        )

    return rows


def _financial_table_rows(period: str, branch, start=None, end=None):
    if start is None or end is None:
        start, end = _range_for(period)
    payments = Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end)
    refunds = Refund.objects.filter(status="REFUNDED", refund_date__gte=start, refund_date__lte=end)
    maint = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end, status="DONE")
    if branch:
        payments = payments.filter(branch=branch)
        refunds = refunds.filter(branch=branch)
        maint = maint.filter(branch=branch)

    revenue_buckets = (
        payments.values("payment_date")
        .annotate(total=Sum("amount"))
        .order_by("payment_date")
    )
    maintenance_buckets = (
        maint.values("task_date")
        .annotate(total=Sum("est_cost"))
        .order_by("task_date")
    )
    refund_buckets = (
        refunds.values("refund_date")
        .annotate(total=Sum("amount"))
        .order_by("refund_date")
    )

    revenue_map = {b["payment_date"]: float(b["total"] or 0) for b in revenue_buckets}
    maint_map = {b["task_date"]: float(b["total"] or 0) for b in maintenance_buckets}
    refund_map = {b["refund_date"]: float(b["total"] or 0) for b in refund_buckets}

    rows = []
    for day in _day_axis(start, end):
        revenue = revenue_map.get(day, 0.0)
        maintenance_cost = maint_map.get(day, 0.0)
        fuel_cost = 0.0
        other_expenses = refund_map.get(day, 0.0)
        total_expenses = maintenance_cost + fuel_cost + other_expenses
        net_profit = revenue - total_expenses
        rows.append(
            {
                "date": day.isoformat(),
                "revenue": f"{revenue:.3f}",
                "maintenance_cost": f"{maintenance_cost:.3f}",
                "fuel_cost": f"{fuel_cost:.3f}",
                "other_expenses": f"{other_expenses:.3f}",
                "total_expenses": f"{total_expenses:.3f}",
                "net_profit": f"{net_profit:.3f}",
            }
        )

    return rows


def _fleet_table_rows(period: str, branch, start=None, end=None):
    if start is None or end is None:
        start, end = _range_for(period)

    vehicles = Vehicle.objects.select_related("brand", "model")
    if branch:
        vehicles = vehicles.filter(branch=branch)

    bookings = Booking.objects.exclude(status="CANCELLED").filter(
        pickup_date__gte=start,
        pickup_date__lte=end,
        status__in=["RETURNED", "CLOSED"],
    )
    if branch:
        bookings = bookings.filter(branch=branch)
    bookings = bookings.select_related("vehicle", "handover", "return_report")

    trip_map = {}
    revenue_map = {}
    distance_map = {}
    for booking in bookings:
        vid = booking.vehicle_id
        if not vid:
            continue
        trip_map[vid] = trip_map.get(vid, 0) + 1
        revenue_map[vid] = revenue_map.get(vid, 0) + float(booking.total_amount or 0)

        handover = _safe_related(booking, "handover")
        ret = _safe_related(booking, "return_report")
        if handover and ret:
            try:
                distance = max(ret.odometer_in_km - handover.odometer_out_km, 0)
                distance_map[vid] = distance_map.get(vid, 0) + distance
            except TypeError:
                pass

    last_service = (
        MaintenanceTask.objects.filter(vehicle__in=vehicles)
        .values("vehicle_id")
        .annotate(last_service=Max("task_date"))
    )
    last_service_map = {r["vehicle_id"]: r["last_service"] for r in last_service}

    rows = []
    for vehicle in vehicles.order_by("plate_number")[:2000]:
        vid = vehicle.id
        rows.append(
            {
                "vehicle_id": vid,
                "vehicle_name": _vehicle_display(vehicle),
                "trips_completed": trip_map.get(vid, 0),
                "distance_driven": distance_map.get(vid, 0),
                "revenue_generated": f"{revenue_map.get(vid, 0.0):.3f}",
                "status": vehicle.status,
                "last_service": last_service_map.get(vid).isoformat() if last_service_map.get(vid) else "",
            }
        )

    return rows


# -------------------------
# APIs
# -------------------------
@login_required
def api_reports_overview(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="today")
    branch = get_active_branch(request)
    return JsonResponse(
        {
            "ok": True,
            "data": get_overview(
                period,
                branch=branch,
                date_from=start,
                date_to=end,
            ),
        }
    )


@login_required
def api_reports_overview_table(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="today")
    branch = get_active_branch(request)

    bookings = Booking.objects.exclude(status="CANCELLED")
    payments = Payment.objects.filter(status="PAID")
    vehicles = Vehicle.objects.all()

    if branch:
        bookings = bookings.filter(branch=branch)
        payments = payments.filter(branch=branch)
        vehicles = vehicles.filter(branch=branch)
    overview = get_overview(period, branch=branch, date_from=start, date_to=end)

    new_customers = Customer.objects.filter(created_at__date__gte=start, created_at__date__lte=end).count()
    total_customers = Customer.objects.count()

    trips = bookings.filter(pickup_date__gte=start, pickup_date__lte=end).count()
    completed_trips = bookings.filter(
        status__in=["RETURNED", "CLOSED"],
        return_date__gte=start,
        return_date__lte=end,
    ).count()
    cancelled_trips = Booking.objects.filter(
        status="CANCELLED",
        pickup_date__gte=start,
        pickup_date__lte=end,
    )
    if branch:
        cancelled_trips = cancelled_trips.filter(branch=branch)

    revenue = payments.filter(payment_date__gte=start, payment_date__lte=end).aggregate(s=Sum("amount"))["s"] or 0
    active_vehicles = vehicles.filter(status="AVAILABLE").count()

    row = {
        "period": f"{start.isoformat()} → {end.isoformat()}",
        "new_customers": new_customers,
        "total_customers": total_customers,
        "revenue": str(revenue),
        "trips": trips,
        "active_vehicles": active_vehicles,
        "completed_trips": completed_trips,
        "cancelled_trips": cancelled_trips.count(),
        "collection_rate": overview["collection_rate"],
        "pending_balance": overview["pending_balance"],
        "fleet_utilization": overview["fleet_utilization"],
    }

    return JsonResponse({"ok": True, "rows": [row]})


@login_required
def api_reports_revenue(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """Monthly revenue (Payments) last 6 months."""
    period, start, end, is_custom = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)

    if period == "monthly" and not is_custom:
        axis = _month_axis(6)
        month_start = axis[0]

        qs = Payment.objects.filter(status="PAID", payment_date__gte=month_start)
        qs = _apply_branch(qs, branch)

        buckets = (
            qs.annotate(m=TruncMonth("payment_date"))
            .values("m")
            .annotate(total=Sum("amount"))
            .order_by("m")
        )

        def _month_key(value):
            return value.date() if hasattr(value, "date") else value

        mapping = {_month_key(b["m"]): float(b["total"] or 0) for b in buckets}
        labels = [d.strftime("%b") for d in axis]
        data = [mapping.get(d, 0.0) for d in axis]
    else:
        axis = _day_axis(start, end)

        qs = Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end)
        qs = _apply_branch(qs, branch)

        buckets = (
            qs.values("payment_date")
            .annotate(total=Sum("amount"))
            .order_by("payment_date")
        )
        mapping = {b["payment_date"]: float(b["total"] or 0) for b in buckets}
        labels = [d.strftime("%b %d") for d in axis]
        data = [mapping.get(d, 0.0) for d in axis]

    return JsonResponse({"ok": True, "labels": labels, "data": data})


@login_required
def api_reports_financial(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """Financial trend based on realized profit signals."""
    period, start, end, is_custom = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)

    if period == "monthly" and not is_custom:
        axis = _month_axis(6)
        month_start = axis[0]

        payments = _apply_branch(Payment.objects.filter(status="PAID", payment_date__gte=month_start), branch)
        refunds = _apply_branch(Refund.objects.filter(status="REFUNDED", refund_date__gte=month_start), branch)
        maintenance = _apply_branch(MaintenanceTask.objects.filter(status="DONE", task_date__gte=month_start), branch)

        payment_buckets = payments.annotate(m=TruncMonth("payment_date")).values("m").annotate(total=Sum("amount")).order_by("m")
        refund_buckets = refunds.annotate(m=TruncMonth("refund_date")).values("m").annotate(total=Sum("amount")).order_by("m")
        maintenance_buckets = maintenance.annotate(m=TruncMonth("task_date")).values("m").annotate(total=Sum("est_cost")).order_by("m")

        payment_map = {_date_key(b["m"]): float(b["total"] or 0) for b in payment_buckets}
        refund_map = {_date_key(b["m"]): float(b["total"] or 0) for b in refund_buckets}
        maintenance_map = {_date_key(b["m"]): float(b["total"] or 0) for b in maintenance_buckets}
        labels = [d.strftime("%b") for d in axis]
        data = [round(payment_map.get(d, 0.0) - refund_map.get(d, 0.0) - maintenance_map.get(d, 0.0), 3) for d in axis]
    else:
        axis = _day_axis(start, end)

        payments = _apply_branch(Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end), branch)
        refunds = _apply_branch(Refund.objects.filter(status="REFUNDED", refund_date__gte=start, refund_date__lte=end), branch)
        maintenance = _apply_branch(MaintenanceTask.objects.filter(status="DONE", task_date__gte=start, task_date__lte=end), branch)

        payment_buckets = payments.values("payment_date").annotate(total=Sum("amount")).order_by("payment_date")
        refund_buckets = refunds.values("refund_date").annotate(total=Sum("amount")).order_by("refund_date")
        maintenance_buckets = maintenance.values("task_date").annotate(total=Sum("est_cost")).order_by("task_date")

        payment_map = {b["payment_date"]: float(b["total"] or 0) for b in payment_buckets}
        refund_map = {b["refund_date"]: float(b["total"] or 0) for b in refund_buckets}
        maintenance_map = {b["task_date"]: float(b["total"] or 0) for b in maintenance_buckets}
        labels = [d.strftime("%b %d") for d in axis]
        data = [round(payment_map.get(d, 0.0) - refund_map.get(d, 0.0) - maintenance_map.get(d, 0.0), 3) for d in axis]

    return JsonResponse({"ok": True, "labels": labels, "data": data})


@login_required
def api_reports_fleet(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    fleet = get_fleet(period, branch=branch, date_from=start, date_to=end)
    labels = ["Bookings Started", "Booked Vehicle Days", "Utilization %"]
    data = [
        int(fleet.get("bookings_started") or 0),
        int(fleet.get("booked_vehicle_days") or 0),
        float(fleet.get("utilization_percent") or 0),
    ]
    return JsonResponse({"ok": True, "labels": labels, "data": data})


@login_required
def api_reports_maintenance(request):
    if not _has_reports_access(request.user, "reports.view_maintenance"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """Maintenance tasks count per week bucket (last 4 weeks)."""
    period, start, end, is_custom = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)

    if period == "monthly" and not is_custom:
        today = end
        qs = MaintenanceTask.objects.filter(task_date__gte=today - timedelta(days=27), task_date__lte=today)
        qs = _apply_branch(qs, branch)

        labels = []
        data = []
        for i in range(4):
            start = today - timedelta(days=(27 - i * 7))
            end = start + timedelta(days=6)
            labels.append(f"W{i+1}")
            data.append(qs.filter(task_date__gte=start, task_date__lte=end).count())
    else:
        axis = _day_axis(start, end)

        qs = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end)
        qs = _apply_branch(qs, branch)

        buckets = (
            qs.values("task_date")
            .annotate(total=Count("id"))
            .order_by("task_date")
        )
        mapping = {b["task_date"]: int(b["total"] or 0) for b in buckets}
        labels = [d.strftime("%b %d") for d in axis]
        data = [mapping.get(d, 0) for d in axis]

    return JsonResponse({"ok": True, "labels": labels, "data": data})


@login_required
def api_reports_customers(request):
    if not _has_reports_access(request.user, "reports.view_limited"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """New customers per month last 6 months."""
    period, start, end, is_custom = _resolve_report_filters(request, default_period="monthly")

    if period == "monthly" and not is_custom:
        axis = _month_axis(6)
        month_start = axis[0]

        qs = Customer.objects.filter(created_at__date__gte=month_start)

        buckets = (
            qs.annotate(m=TruncMonth("created_at"))
            .values("m")
            .annotate(total=Count("id"))
            .order_by("m")
        )
        mapping = {b["m"].date(): int(b["total"] or 0) for b in buckets}
        labels = [d.strftime("%b") for d in axis]
        data = [mapping.get(d, 0) for d in axis]
    else:
        axis = _day_axis(start, end)

        qs = Customer.objects.filter(created_at__date__gte=start, created_at__date__lte=end)

        buckets = (
            qs.values("created_at__date")
            .annotate(total=Count("id"))
            .order_by("created_at__date")
        )
        mapping = {b["created_at__date"]: int(b["total"] or 0) for b in buckets}
        labels = [d.strftime("%b %d") for d in axis]
        data = [mapping.get(d, 0) for d in axis]

    return JsonResponse({"ok": True, "labels": labels, "data": data})


@login_required
def api_reports_revenue_table(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    rows = _revenue_table_rows(period, branch, start=start, end=end)
    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_financial_table(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    rows = _financial_table_rows(period, branch, start=start, end=end)
    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_fleet_table(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    rows = _fleet_table_rows(period, branch, start=start, end=end)
    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_maintenance_table(request):
    if not _has_reports_access(request.user, "reports.view_maintenance"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    _, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)

    tasks = MaintenanceTask.objects.select_related("vehicle", "vehicle__brand", "vehicle__model", "assignee")
    tasks = tasks.filter(task_date__gte=start, task_date__lte=end).order_by("-task_date", "-id")
    if branch:
        tasks = tasks.filter(branch=branch)

    rows = []
    for task in tasks[:2000]:
        rows.append(
            {
                "date": task.task_date.isoformat() if task.task_date else "",
                "vehicle": _vehicle_display(task.vehicle),
                "service_type": task.task_type,
                "description": task.notes,
                "cost": str(task.est_cost),
                "mechanic": task.assignee.get_full_name() if task.assignee else "",
                "status": task.status,
            }
        )

    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_customers_table(request):
    if not _has_reports_access(request.user, "reports.view_limited"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    _, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)

    bookings = Booking.objects.exclude(status="CANCELLED").filter(pickup_date__gte=start, pickup_date__lte=end)
    if branch:
        bookings = bookings.filter(branch=branch)

    booking_sums = (
        bookings.values("customer_id")
        .annotate(trips=Count("id"), spent=Sum("total_amount"), last_trip=Max("pickup_date"))
    )
    booking_map = {r["customer_id"]: r for r in booking_sums}

    last_trip_all = Booking.objects.exclude(status="CANCELLED")
    if branch:
        last_trip_all = last_trip_all.filter(branch=branch)
    last_trip_map = {
        r["customer_id"]: r["last_trip"]
        for r in last_trip_all.values("customer_id").annotate(last_trip=Max("pickup_date"))
    }

    rows = []
    for customer in Customer.objects.all().order_by("name", "id")[:2000]:
        data = booking_map.get(customer.id, {})
        rows.append(
            {
                "customer_id": customer.id,
                "name": customer.name,
                "total_trips": data.get("trips", 0) or 0,
                "total_spent": f"{float(data.get('spent') or 0):.3f}",
                "last_trip": last_trip_map.get(customer.id).isoformat() if last_trip_map.get(customer.id) else "",
                "status": "Active" if customer.is_active else "Inactive",
            }
        )

    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_insights(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period = (request.GET.get("period") or "monthly").strip().lower()
    branch = get_active_branch(request)
    payload = get_predictive_insights(period=period, branch=branch)
    return JsonResponse({"ok": True, "data": payload})


@login_required
def api_reports_anomalies(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    period = (request.GET.get("period") or "monthly").strip().lower()
    branch = get_active_branch(request)
    run_scan = (request.GET.get("scan") or "0") == "1"

    if run_scan:
        detect_anomalies(period=period, branch=branch, notify=True)

    qs = AnomalyEvent.objects.all().order_by("-detected_on", "-created_at")
    if branch:
        qs = qs.filter(branch=branch)
    rows = [
        {
            "id": row.id,
            "type": row.anomaly_type,
            "severity": row.severity,
            "title": row.title,
            "details": row.details,
            "detected_on": row.detected_on.isoformat(),
            "is_resolved": row.is_resolved,
        }
        for row in qs[:200]
    ]
    return JsonResponse({"ok": True, "rows": rows})


@login_required
def api_reports_anomaly_resolve(request, anomaly_id: int):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    try:
        anomaly = AnomalyEvent.objects.get(id=anomaly_id)
    except AnomalyEvent.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Not found"}, status=404)

    anomaly.is_resolved = True
    anomaly.resolved_at = timezone.now()
    anomaly.save(update_fields=["is_resolved", "resolved_at", "updated_at"])
    return JsonResponse({"ok": True})


@login_required
def api_reports_accounting_export(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    provider = (request.POST.get("provider") or request.GET.get("provider") or "MANUAL").strip().upper()
    export_type = (request.POST.get("type") or request.GET.get("type") or "PAYMENTS").strip().upper()
    period = (request.POST.get("period") or request.GET.get("period") or "monthly").strip().lower()
    branch = get_active_branch(request)

    try:
        payload = create_accounting_export(provider=provider, export_type=export_type, period=period, branch=branch)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)

    response = HttpResponse(payload["csv"], content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{payload["file_name"]}"'
    return response


@login_required
def api_reports_overview_pdf(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="today")
    branch = get_active_branch(request)
    overview = get_overview(period, branch=branch, date_from=start, date_to=end)
    revenue = get_revenue_breakdown(period, branch=branch, date_from=start, date_to=end)
    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Reports Overview",
        "overview": overview,
        "revenue": revenue,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_overview.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


@login_required
def api_reports_revenue_pdf(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    rows = _revenue_table_rows(period, branch, start=start, end=end)
    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Revenue Report",
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "rows": rows,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_revenue.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


@login_required
def api_reports_financial_pdf(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_financial(period, branch=branch, date_from=start, date_to=end)
    rows = _financial_table_rows(period, branch, start=start, end=end)
    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Financial Report",
        "data": data,
        "rows": rows,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_financial.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


@login_required
def api_reports_fleet_pdf(request):
    if not _has_reports_access(request.user, "reports.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_fleet(period, branch=branch, date_from=start, date_to=end)
    rows = _fleet_table_rows(period, branch, start=start, end=end)
    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Fleet Report",
        "data": data,
        "rows": rows,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_fleet.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


@login_required
def api_reports_maintenance_pdf(request):
    if not _has_reports_access(request.user, "reports.view_maintenance"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_maintenance(period, branch=branch, date_from=start, date_to=end)
    tasks = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end).order_by("-task_date")
    if branch:
        tasks = tasks.filter(branch=branch)
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
        "tasks": tasks,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_maintenance.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


@login_required
def api_reports_customers_pdf(request):
    if not _has_reports_access(request.user, "reports.view_limited"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_customers(period, branch=branch, date_from=start, date_to=end)
    customers = Customer.objects.all().order_by("name", "id")
    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Customers Report",
        "data": data,
        "customers": customers,
    }
    return render_pdf_from_template(
        request=request,
        template="print/reports_customers.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )


# -------------------------
# PRINT (HTML)
# -------------------------
@login_required
def reports_overview_print(request):
    if not _has_reports_access(request.user, "reports.view"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="today")
    branch = get_active_branch(request)
    overview = get_overview(period, branch=branch, date_from=start, date_to=end)
    revenue = get_revenue_breakdown(period, branch=branch, date_from=start, date_to=end)
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/overview.pdf", request, {"doc_number": doc_number}),
        "title": "Reports Overview",
        "overview": overview,
        "revenue": revenue,
    }
    return render(request, "print/reports_overview.html", context)


@login_required
def reports_revenue_print(request):
    if not _has_reports_access(request.user, "reports.view"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    rows = _revenue_table_rows(period, branch, start=start, end=end)
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/revenue.pdf", request, {"doc_number": doc_number}),
        "title": "Revenue Report",
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "rows": rows,
    }
    return render(request, "print/reports_revenue.html", context)


@login_required
def reports_financial_print(request):
    if not _has_reports_access(request.user, "reports.view_financial"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_financial(period, branch=branch, date_from=start, date_to=end)
    rows = _financial_table_rows(period, branch, start=start, end=end)
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/financial.pdf", request, {"doc_number": doc_number}),
        "title": "Financial Report",
        "data": data,
        "rows": rows,
    }
    return render(request, "print/reports_financial.html", context)


@login_required
def reports_fleet_print(request):
    if not _has_reports_access(request.user, "reports.view"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_fleet(period, branch=branch, date_from=start, date_to=end)
    rows = _fleet_table_rows(period, branch, start=start, end=end)
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/fleet.pdf", request, {"doc_number": doc_number}),
        "title": "Fleet Report",
        "data": data,
        "rows": rows,
    }
    return render(request, "print/reports_fleet.html", context)


@login_required
def reports_maintenance_print(request):
    if not _has_reports_access(request.user, "reports.view_maintenance"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_maintenance(period, branch=branch, date_from=start, date_to=end)
    tasks = MaintenanceTask.objects.select_related("vehicle", "vehicle__brand", "vehicle__model", "assignee", "branch").order_by("-task_date", "-id")
    tasks = tasks.filter(task_date__gte=start, task_date__lte=end)
    if branch:
        tasks = tasks.filter(branch=branch)
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/maintenance.pdf", request, {"doc_number": doc_number}),
        "title": "Maintenance Report",
        "data": data,
        "tasks": tasks,
    }
    return render(request, "print/reports_maintenance.html", context)


@login_required
def reports_customers_print(request):
    if not _has_reports_access(request.user, "reports.view_limited"):
        return render(request, "errors/403.html", status=403)
    period, start, end, _ = _resolve_report_filters(request, default_period="monthly")
    branch = get_active_branch(request)
    data = get_customers(period, branch=branch, date_from=start, date_to=end)
    customers = Customer.objects.all().order_by("name", "id")
    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/reports/customers.pdf", request, {"doc_number": doc_number}),
        "title": "Customers Report",
        "data": data,
        "customers": customers,
    }
    return render(request, "print/reports_customers.html", context)
