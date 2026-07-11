from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.core.services import get_active_branch
from .services import (
    get_dashboard_kpis,
    get_recent_reservations,
    get_recent_bookings,
    get_recent_payments,
    get_earnings_chart,
    get_global_search_results,
)


@login_required
def dashboard_view(request):
    active_branch = get_active_branch(request)
    chart_period = (request.GET.get("chart_period") or "year").strip().lower()
    kpis = get_dashboard_kpis(active_branch=active_branch)
    reservations = get_recent_reservations(active_branch=active_branch, limit=4)
    bookings = get_recent_bookings(active_branch=active_branch, limit=3)
    payments = get_recent_payments(active_branch=active_branch, limit=4)
    chart = get_earnings_chart(active_branch=active_branch, period=chart_period)
    context = {
        "kpis": kpis,
        "recent_reservations": reservations,
        "recent_bookings": bookings,
        "recent_payments": payments,
        "earnings_chart": chart,
        "chart_period": chart_period,
    }
    return render(request, "dashboard/dashboard.html", context)


@login_required
def api_global_search(request):
    query = (request.GET.get("q") or "").strip()
    active_branch = get_active_branch(request)
    groups = get_global_search_results(
        query=query,
        user=request.user,
        active_branch=active_branch,
    )
    return JsonResponse({"ok": True, "query": query, "groups": groups})
