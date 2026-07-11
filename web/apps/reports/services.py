from datetime import timedelta
import csv
import io
from statistics import mean, pstdev
from django.core.cache import cache
from django.db.models import Sum, Count
from django.utils import timezone

from apps.bookings.models import Booking
from apps.payments.models import Payment, Refund
from apps.maintenance.models import MaintenanceTask
from apps.customers.models import Customer
from apps.fleet.models import Vehicle
from apps.core.notification_dispatcher import dispatch_notification
from apps.accounts.models import User

from .models import InsightSnapshot, AnomalyEvent, AccountingExport


def _cache_key(name: str, period: str, branch=None) -> str:
    branch_id = getattr(branch, "id", "global")
    day = timezone.localdate().isoformat()
    return f"reports:{name}:period={period}:branch={branch_id}:day={day}"


def _cached(name: str, period: str, branch=None, ttl: int = 300, compute=None):
    key = _cache_key(name, period, branch=branch)
    cached = cache.get(key)
    if cached is not None:
        return cached
    value = compute()
    cache.set(key, value, ttl)
    return value


def _range_for(period: str):
    today = timezone.localdate()
    if period == "today":
        start = today
        end = today
    elif period == "weekly":
        start = today - timedelta(days=6)
        end = today
    else:  # monthly
        start = today - timedelta(days=29)
        end = today
    return start, end


def _resolved_range(period: str, date_from=None, date_to=None):
    if date_from and date_to:
        if date_from > date_to:
            date_from, date_to = date_to, date_from
        return date_from, date_to
    return _range_for(period)


def _cache_period(period: str, date_from=None, date_to=None) -> str:
    if date_from and date_to:
        return f"custom:{date_from.isoformat()}:{date_to.isoformat()}"
    return period


def get_overview(period: str = "today", branch=None, date_from=None, date_to=None) -> dict:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)

        bqs = Booking.objects.exclude(status="CANCELLED")
        pqs = Payment.objects.filter(status="PAID")
        rqs = Refund.objects.filter(status="REFUNDED")
        mqs = MaintenanceTask.objects.all()
        cqs = Customer.objects.filter(is_active=True)
        vqs = Vehicle.objects.all()

        if branch:
            bqs = bqs.filter(branch=branch)
            pqs = pqs.filter(branch=branch)
            rqs = rqs.filter(branch=branch)
            mqs = mqs.filter(branch=branch)
            vqs = vqs.filter(branch=branch)

        bookings_in_period = bqs.filter(pickup_date__gte=start, pickup_date__lte=end)
        bookings_count = bookings_in_period.count()
        active_rentals = bqs.filter(status="CHECKED_OUT").count()
        upcoming = bqs.filter(status="UPCOMING").count()
        overdue = bqs.filter(status="CHECKED_OUT", return_date__lt=timezone.localdate()).count()

        revenue = pqs.filter(payment_date__gte=start, payment_date__lte=end).aggregate(s=Sum("amount"))["s"] or 0
        refunds = rqs.filter(refund_date__gte=start, refund_date__lte=end).aggregate(s=Sum("amount"))["s"] or 0
        maintenance_cost = (
            mqs.filter(task_date__gte=start, task_date__lte=end, status="DONE").aggregate(s=Sum("est_cost"))["s"] or 0
        )
        billed_total = bookings_in_period.aggregate(s=Sum("total_amount"))["s"] or 0
        collected_for_period_bookings = pqs.filter(booking__in=bookings_in_period).aggregate(s=Sum("amount"))["s"] or 0
        net_revenue = (revenue or 0) - (refunds or 0)
        net_profit = net_revenue - (maintenance_cost or 0)
        pending_balance = max((billed_total or 0) - (collected_for_period_bookings or 0), 0)
        avg_booking_value = (billed_total / bookings_count) if bookings_count else 0
        collection_rate = round((float(collected_for_period_bookings or 0) / float(billed_total or 1)) * 100, 2) if billed_total else 0
        if collection_rate > 100:
            collection_rate = 100.0
        fleet = vqs.count()
        engaged_fleet = vqs.filter(status__in=["RENTED", "RESERVED", "MAINTENANCE"]).count()
        fleet_utilization = round((engaged_fleet / (fleet or 1)) * 100, 2) if fleet else 0

        maintenance_open = mqs.filter(status__in=["OPEN", "IN_PROGRESS"]).count()
        customers = cqs.count()

        return {
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "bookings_count": bookings_count,
            "active_rentals": active_rentals,
            "upcoming_bookings": upcoming,
            "overdue_rentals": overdue,
            "revenue_gross": str(revenue),
            "refunds_total": str(refunds),
            "maintenance_cost": str(maintenance_cost),
            "revenue_net": str(net_revenue),
            "net_profit": str(net_profit),
            "billed_total": str(billed_total),
            "pending_balance": str(pending_balance),
            "avg_booking_value": f"{float(avg_booking_value):.3f}",
            "collection_rate": collection_rate,
            "fleet_utilization": fleet_utilization,
            "maintenance_open": maintenance_open,
            "active_customers": customers,
            "fleet_vehicles": fleet,
        }

    return _cached(
        "overview",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=180,
        compute=_compute,
    )


def get_revenue_breakdown(period: str = "monthly", branch=None, date_from=None, date_to=None) -> list[dict]:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)
        pqs = Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end)
        if branch:
            pqs = pqs.filter(branch=branch)

        rows = pqs.values("method").annotate(total=Sum("amount"), count=Count("id")).order_by("-total")
        return [{"method": r["method"], "total": str(r["total"] or 0), "count": r["count"]} for r in rows]

    return _cached(
        "revenue_breakdown",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=300,
        compute=_compute,
    )


def get_financial(period: str = "monthly", branch=None, date_from=None, date_to=None) -> dict:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)

        pqs = Payment.objects.filter(status="PAID", payment_date__gte=start, payment_date__lte=end)
        rqs = Refund.objects.filter(status="REFUNDED", refund_date__gte=start, refund_date__lte=end)
        mqs = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end, status="DONE")
        if branch:
            pqs = pqs.filter(branch=branch)
            rqs = rqs.filter(branch=branch)
            mqs = mqs.filter(branch=branch)

        gross = pqs.aggregate(s=Sum("amount"))["s"] or 0
        refunded = rqs.aggregate(s=Sum("amount"))["s"] or 0
        maintenance_expense = mqs.aggregate(s=Sum("est_cost"))["s"] or 0
        total_expenses = (refunded or 0) + (maintenance_expense or 0)
        days = max((end - start).days + 1, 1)
        avg_daily_revenue = float(gross or 0) / days

        return {
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "gross_revenue": str(gross),
            "refunds": str(refunded),
            "maintenance_expense": str(maintenance_expense),
            "total_expenses": str(total_expenses),
            "net_revenue": str((gross or 0) - total_expenses),
            "avg_daily_revenue": f"{avg_daily_revenue:.3f}",
            "payments_count": pqs.count(),
            "refunds_count": rqs.count(),
            "maintenance_tasks_done": mqs.count(),
        }

    return _cached(
        "financial",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=300,
        compute=_compute,
    )


def get_fleet(period: str = "monthly", branch=None, date_from=None, date_to=None) -> dict:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)

        vqs = Vehicle.objects.all()
        bqs = Booking.objects.exclude(status="CANCELLED")

        if branch:
            vqs = vqs.filter(branch=branch)
            bqs = bqs.filter(branch=branch)

        status_counts = vqs.values("status").annotate(count=Count("id")).order_by("status")

        bookings_started = bqs.filter(pickup_date__gte=start, pickup_date__lte=end).count()
        fleet_count = vqs.count() or 1
        total_days = max((end - start).days + 1, 1)
        booked_days = 0
        overlapping = bqs.filter(pickup_date__lte=end, return_date__gte=start)
        for booking in overlapping:
            overlap_start = max(booking.pickup_date, start)
            overlap_end = min(booking.return_date, end)
            booked_days += max((overlap_end - overlap_start).days + 1, 0)
        utilization = round((booked_days / max(fleet_count * total_days, 1)) * 100, 2)

        return {
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "fleet_count": vqs.count(),
            "bookings_started": bookings_started,
            "utilization_percent": utilization,
            "booked_vehicle_days": booked_days,
            "status_counts": [{"status": r["status"], "count": r["count"]} for r in status_counts],
        }

    return _cached(
        "fleet",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=300,
        compute=_compute,
    )


def get_customers(period: str = "monthly", branch=None, date_from=None, date_to=None) -> dict:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)

        cqs = Customer.objects.all()
        bqs = Booking.objects.exclude(status="CANCELLED")
        if branch:
            bqs = bqs.filter(branch=branch)

        new_customers = cqs.filter(created_at__date__gte=start, created_at__date__lte=end).count()
        repeat_customers = (
            bqs.values("customer_id").annotate(bookings=Count("id")).filter(bookings__gte=2).count()
        )
        customer_spend_total = bqs.aggregate(s=Sum("total_amount"))["s"] or 0

        top = (
            bqs.values("customer_id", "customer__name")
            .annotate(bookings=Count("id"), spent=Sum("total_amount"))
            .order_by("-bookings")[:10]
        )

        return {
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "new_customers": new_customers,
            "repeat_customers": repeat_customers,
            "avg_customer_value": f"{(float(customer_spend_total) / max(cqs.count(), 1)):.3f}" if cqs.exists() else "0.000",
            "top_customers": [
                {
                    "customer_id": r["customer_id"],
                    "name": r["customer__name"],
                    "bookings": r["bookings"],
                    "spent": str(r["spent"] or 0),
                }
                for r in top
            ],
        }

    return _cached(
        "customers",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=300,
        compute=_compute,
    )


def get_maintenance(period: str = "monthly", branch=None, date_from=None, date_to=None) -> dict:
    def _compute():
        start, end = _resolved_range(period, date_from=date_from, date_to=date_to)

        mqs = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end)
        if branch:
            mqs = mqs.filter(branch=branch)

        by_status = mqs.values("status").annotate(count=Count("id")).order_by("status")
        est_total = mqs.filter(status="DONE").aggregate(s=Sum("est_cost"))["s"] or 0
        overdue_open = mqs.filter(status__in=["OPEN", "IN_PROGRESS"], due_date__lt=timezone.localdate()).count()
        avg_cost = (float(est_total) / max(mqs.filter(status="DONE").count(), 1)) if mqs.filter(status="DONE").exists() else 0

        return {
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "tasks_count": mqs.count(),
            "est_cost_total": str(est_total),
            "overdue_open": overdue_open,
            "avg_cost_completed": f"{avg_cost:.3f}",
            "status_counts": [{"status": r["status"], "count": r["count"]} for r in by_status],
        }

    return _cached(
        "maintenance",
        _cache_period(period, date_from=date_from, date_to=date_to),
        branch=branch,
        ttl=300,
        compute=_compute,
    )


def get_predictive_insights(period: str = "monthly", branch=None) -> dict:
    start, end = _range_for(period)
    today = timezone.localdate()

    bookings = Booking.objects.exclude(status="CANCELLED")
    payments = Payment.objects.filter(status="PAID")
    maintenance = MaintenanceTask.objects.all()
    vehicles = Vehicle.objects.all()
    if branch:
        bookings = bookings.filter(branch=branch)
        payments = payments.filter(branch=branch)
        maintenance = maintenance.filter(branch=branch)
        vehicles = vehicles.filter(branch=branch)

    prev_start = start - timedelta(days=(end - start).days + 1)
    prev_end = start - timedelta(days=1)

    prev_revenue = payments.filter(payment_date__gte=prev_start, payment_date__lte=prev_end).aggregate(s=Sum("amount"))["s"] or 0
    current_revenue = payments.filter(payment_date__gte=start, payment_date__lte=end).aggregate(s=Sum("amount"))["s"] or 0
    growth = 0.0 if float(prev_revenue or 0) == 0 else (float(current_revenue) - float(prev_revenue)) / float(prev_revenue)

    recent_windows = []
    for i in range(3):
        w_end = start - timedelta(days=1 + (i * ((end - start).days + 1)))
        w_start = w_end - timedelta(days=(end - start).days)
        total = payments.filter(payment_date__gte=w_start, payment_date__lte=w_end).aggregate(s=Sum("amount"))["s"] or 0
        recent_windows.append(float(total))
    moving_avg = mean(recent_windows) if recent_windows else float(current_revenue)
    growth_forecast = float(current_revenue) * (1 + growth)
    next_revenue = round((growth_forecast * 0.6) + (moving_avg * 0.4), 3)

    prev_demand = bookings.filter(pickup_date__gte=prev_start, pickup_date__lte=prev_end).count()
    current_demand = bookings.filter(pickup_date__gte=start, pickup_date__lte=end).count()
    demand_growth = 0.0 if prev_demand == 0 else (current_demand - prev_demand) / prev_demand
    next_demand = max(int(round(current_demand * (1 + demand_growth))), 0)

    maintenance_done = maintenance.filter(
        task_date__gte=start,
        task_date__lte=end,
        status="DONE",
    ).count()
    fleet_count = max(vehicles.count(), 1)
    maintenance_risk = round(min((maintenance_done / fleet_count) * 100, 100.0), 2)

    overdue = bookings.filter(status="CHECKED_OUT", return_date__lt=today).count()
    downtime_risk = round(min((overdue / fleet_count) * 100, 100.0), 2)

    confidence = 100.0
    if len(recent_windows) >= 2:
        volatility = pstdev(recent_windows)
        baseline = max(mean(recent_windows), 1.0)
        confidence = max(40.0, min(98.0, 100.0 - ((volatility / baseline) * 100.0)))

    payload = {
        "period": period,
        "date_from": start.isoformat(),
        "date_to": end.isoformat(),
        "forecast_revenue_next_period": f"{next_revenue:.3f}",
        "forecast_demand_next_period": next_demand,
        "maintenance_cost_risk_percent": maintenance_risk,
        "vehicle_downtime_risk_percent": downtime_risk,
        "trend_signals": {
            "revenue_growth_percent": round(growth * 100, 2),
            "demand_growth_percent": round(demand_growth * 100, 2),
        },
        "model_confidence_percent": round(confidence, 2),
    }

    InsightSnapshot.objects.update_or_create(
        branch=branch,
        period=period,
        generated_for=today,
        defaults={"payload": payload},
    )
    return payload


def detect_anomalies(period: str = "monthly", branch=None, notify: bool = True) -> list[dict]:
    start, end = _range_for(period)
    window_days = max((end - start).days + 1, 1)
    prev_start = start - timedelta(days=window_days)
    prev_end = start - timedelta(days=1)

    payments = Payment.objects.filter(status="PAID")
    refunds = Refund.objects.filter(status="REFUNDED")
    maintenance = MaintenanceTask.objects.all()
    bookings = Booking.objects.exclude(status="CANCELLED")
    if branch:
        payments = payments.filter(branch=branch)
        refunds = refunds.filter(branch=branch)
        maintenance = maintenance.filter(branch=branch)
        bookings = bookings.filter(branch=branch)

    anomalies: list[dict] = []

    current_expenses = (refunds.filter(refund_date__gte=start, refund_date__lte=end).aggregate(s=Sum("amount"))["s"] or 0) + (
        maintenance.filter(task_date__gte=start, task_date__lte=end, status="DONE").aggregate(s=Sum("est_cost"))["s"] or 0
    )
    prev_expenses = (refunds.filter(refund_date__gte=prev_start, refund_date__lte=prev_end).aggregate(s=Sum("amount"))["s"] or 0) + (
        maintenance.filter(task_date__gte=prev_start, task_date__lte=prev_end, status="DONE").aggregate(s=Sum("est_cost"))["s"] or 0
    )
    if float(prev_expenses or 0) > 0 and float(current_expenses) > float(prev_expenses) * 1.5:
        anomalies.append(
            {
                "type": "EXPENSE_SPIKE",
                "severity": "HIGH",
                "title": "Unusual expense spike detected",
                "details": f"Expenses rose from {float(prev_expenses):.3f} to {float(current_expenses):.3f}",
                "metadata": {"previous": float(prev_expenses), "current": float(current_expenses)},
            }
        )

    daily_expenses = []
    for i in range(window_days):
        day = start + timedelta(days=i)
        day_total = (refunds.filter(refund_date=day).aggregate(s=Sum("amount"))["s"] or 0) + (
            maintenance.filter(task_date=day, status="DONE").aggregate(s=Sum("est_cost"))["s"] or 0
        )
        daily_expenses.append(float(day_total))
    if len(daily_expenses) >= 5:
        mu = mean(daily_expenses)
        sigma = pstdev(daily_expenses)
        if sigma > 0:
            latest = daily_expenses[-1]
            z_score = (latest - mu) / sigma
            if z_score >= 2.2:
                anomalies.append(
                    {
                        "type": "EXPENSE_SPIKE",
                        "severity": "HIGH",
                        "title": "Expense outlier detected",
                        "details": f"Latest day expense z-score={z_score:.2f} (value={latest:.3f})",
                        "metadata": {"z_score": round(z_score, 2), "latest": latest, "mean": round(mu, 3)},
                    }
                )

    current_repairs = maintenance.filter(task_date__gte=start, task_date__lte=end, task_type="REPAIR").count()
    prev_repairs = maintenance.filter(task_date__gte=prev_start, task_date__lte=prev_end, task_type="REPAIR").count()
    if prev_repairs > 0 and current_repairs > int(prev_repairs * 1.6):
        anomalies.append(
            {
                "type": "REPAIR_SPIKE",
                "severity": "MEDIUM",
                "title": "Frequent repair anomaly detected",
                "details": f"Repairs increased from {prev_repairs} to {current_repairs}",
                "metadata": {"previous": prev_repairs, "current": current_repairs},
            }
        )

    delayed_returns = bookings.filter(status="CHECKED_OUT", return_date__lt=timezone.localdate()).count()
    fleet_count = max(Vehicle.objects.filter(branch=branch).count() if branch else Vehicle.objects.count(), 1)
    if delayed_returns > max(3, int(fleet_count * 0.15)):
        anomalies.append(
            {
                "type": "PAYMENT_DELAY",
                "severity": "MEDIUM",
                "title": "Delayed return/payment risk anomaly",
                "details": f"{delayed_returns} active delayed returns currently open.",
                "metadata": {"delayed_returns": delayed_returns, "fleet": fleet_count},
            }
        )

    detected_on = timezone.localdate()
    saved: list[dict] = []
    for item in anomalies:
        event = AnomalyEvent.objects.create(
            branch=branch,
            anomaly_type=item["type"],
            severity=item["severity"],
            title=item["title"],
            details=item["details"],
            detected_on=detected_on,
            metadata=item["metadata"],
        )
        saved.append(
            {
                "id": event.id,
                "type": event.anomaly_type,
                "severity": event.severity,
                "title": event.title,
                "details": event.details,
                "detected_on": event.detected_on.isoformat(),
            }
        )

        if notify:
            admins = User.objects.filter(is_active=True).select_related("role")
            for user in admins:
                if getattr(user, "is_superuser", False) or getattr(getattr(user, "role", None), "code", "") in {"ADMIN", "MANAGER"}:
                    dispatch_notification(
                        user=user,
                        title=f"[Anomaly] {event.title}",
                        message=event.details,
                        notification_type="REMINDER",
                        metadata={"source": "anomaly_detection", "anomaly_id": event.id},
                        send_email_channel=True,
                        send_sms_channel=False,
                        send_whatsapp_channel=False,
                    )
    return saved


def create_accounting_export(provider: str, export_type: str, period: str = "monthly", branch=None) -> dict:
    start, end = _range_for(period)
    provider = (provider or "MANUAL").upper()
    export_type = (export_type or "").upper()

    output = io.StringIO()
    writer = csv.writer(output)
    row_count = 0

    if export_type == "INVOICES":
        writer.writerow(["booking_id", "reference", "customer", "pickup_date", "return_date", "total_amount", "currency"])
        qs = Booking.objects.exclude(status="CANCELLED").filter(pickup_date__gte=start, pickup_date__lte=end).select_related("customer")
        if branch:
            qs = qs.filter(branch=branch)
        for b in qs:
            writer.writerow([b.id, b.reference, b.customer.name if b.customer_id else "", b.pickup_date, b.return_date, b.total_amount, b.currency_code])
            row_count += 1
    elif export_type == "PAYMENTS":
        writer.writerow(["payment_id", "receipt_number", "booking_id", "date", "method", "amount", "currency", "status"])
        qs = Payment.objects.filter(payment_date__gte=start, payment_date__lte=end).order_by("payment_date", "id")
        if branch:
            qs = qs.filter(branch=branch)
        for p in qs:
            writer.writerow([p.id, p.receipt_number, p.booking_id, p.payment_date, p.method, p.amount, p.currency_code, p.status])
            row_count += 1
    elif export_type == "EXPENSES":
        writer.writerow(["maintenance_id", "vehicle_id", "task_date", "task_type", "status", "est_cost"])
        qs = MaintenanceTask.objects.filter(task_date__gte=start, task_date__lte=end).order_by("task_date", "id")
        if branch:
            qs = qs.filter(branch=branch)
        for m in qs:
            writer.writerow([m.id, m.vehicle_id, m.task_date, m.task_type, m.status, m.est_cost])
            row_count += 1
    else:
        raise ValueError("Unsupported export_type. Use INVOICES, PAYMENTS, or EXPENSES.")

    file_content = output.getvalue()
    filename = f"accounting-{provider.lower()}-{export_type.lower()}-{timezone.now().strftime('%Y%m%d-%H%M%S')}.csv"
    export = AccountingExport.objects.create(
        branch=branch,
        provider=provider if provider in {"QUICKBOOKS", "ZOHO", "MANUAL"} else "MANUAL",
        export_type=export_type,
        status="EXPORTED",
        generated_on=timezone.localdate(),
        row_count=row_count,
        file_name=filename,
        metadata={
            "period": period,
            "date_from": start.isoformat(),
            "date_to": end.isoformat(),
            "csv": file_content,
        },
    )

    return {
        "id": export.id,
        "provider": export.provider,
        "export_type": export.export_type,
        "file_name": export.file_name,
        "row_count": export.row_count,
        "csv": file_content,
    }
