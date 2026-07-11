from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from decimal import Decimal, ROUND_HALF_UP

from apps.core.services import get_active_branch
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.settings_app.models import BusinessProfile
from apps.settings_app.services import get_next_document_number
from apps.payments.services import get_booking_net_paid
from .pdf_html import render_pdf_from_template


def _branch_guard(request, booking: Booking):
    branch = get_active_branch(request)
    if branch and booking.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)
    return None


def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception:
        amount = Decimal("0")
    return amount.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _days(pickup_date, return_date) -> int:
    return max((return_date - pickup_date).days, 1)


def _invoice_settlement_context(booking: Booking) -> dict:
    booked_days = _days(booking.pickup_date, booking.return_date)
    used_days = booked_days
    actual_return_date = booking.return_date
    additions_subtotal = Decimal("0")
    final_due = _money((booking.total_amount or 0) - (booking.deposit_amount or 0))

    return_report = getattr(booking, "return_report", None)
    if return_report and getattr(return_report, "actual_return_date", None):
        actual_return_date = return_report.actual_return_date
        if actual_return_date < booking.return_date:
            used_days = _days(booking.pickup_date, actual_return_date)
        used_days = min(max(used_days, 1), booked_days)
        additions_subtotal = _money(getattr(return_report, "additions_subtotal", 0))
        final_due = _money(getattr(return_report, "final_due", 0))

    net_paid = _money(get_booking_net_paid(booking))
    balance_due = _money(final_due - net_paid)

    prorated_subtotal = _money((_money(booking.daily_rate) * used_days) + _money(booking.extras_total))
    prorated_vat = _money(prorated_subtotal * Decimal(str(booking.vat_rate or 0)))
    prorated_total = _money(prorated_subtotal + prorated_vat)
    early_return_credit = _money(max(_money(booking.total_amount) - prorated_total, Decimal("0")))

    return {
        "settlement_days": used_days,
        "settlement_return_date": actual_return_date,
        "settlement_subtotal": prorated_subtotal,
        "settlement_vat": prorated_vat,
        "settlement_total_excl_deposit": prorated_total,
        "settlement_early_return_credit": early_return_credit,
        "settlement_additions_subtotal": additions_subtotal,
        "settlement_already_paid": net_paid,
        "settlement_final_due": balance_due,
    }


@login_required
@require_http_methods(["GET"])
def api_booking_invoice_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model", "return_report"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "INVOICE",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        **_invoice_settlement_context(booking),
    }
    return render_pdf_from_template(
        request=request,
        template="print/invoice.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="invoices",
    )


@login_required
@require_http_methods(["GET"])
def api_booking_agreement_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "AGREEMENT",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/agreement.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="agreements",
    )


@login_required
@require_http_methods(["GET"])
def api_booking_confirmation_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "CONFIRMATION",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/booking_confirmation.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="confirmations",
    )


@login_required
@require_http_methods(["GET"])
def api_booking_quotation_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "QUOTATION",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/quotation.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="quotations",
    )


@login_required
@require_http_methods(["GET"])
def api_booking_return_report_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").prefetch_related("return_report"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "RETURN_REPORT",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/return_report.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="return_reports",
    )


@login_required
@require_http_methods(["GET"])
def api_booking_handover_checklist_pdf(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").prefetch_related("handover"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "HANDOVER",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/handover_checklist.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="handovers",
    )


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


@login_required
@require_http_methods(["GET"])
def booking_invoice_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model", "return_report"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "INVOICE",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/invoice.pdf", request, {"doc_number": doc_number}),
        **_invoice_settlement_context(booking),
    }
    return render(request, "print/invoice.html", context)


@login_required
@require_http_methods(["GET"])
def booking_agreement_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "AGREEMENT",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/agreement.pdf", request, {"doc_number": doc_number}),
        "doc_meta_extra_class": "doc-meta-inline--tight",
    }
    return render(request, "print/agreement.html", context)


@login_required
@require_http_methods(["GET"])
def booking_confirmation_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "CONFIRMATION",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/confirmation.pdf", request, {"doc_number": doc_number}),
    }
    return render(request, "print/booking_confirmation.html", context)


@login_required
@require_http_methods(["GET"])
def booking_quotation_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "QUOTATION",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/quotation.pdf", request, {"doc_number": doc_number}),
    }
    return render(request, "print/quotation.html", context)


@login_required
@require_http_methods(["GET"])
def booking_return_report_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").prefetch_related("return_report"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "RETURN_REPORT",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/return-report.pdf", request, {"doc_number": doc_number}),
    }
    return render(request, "print/return_report.html", context)


@login_required
@require_http_methods(["GET"])
def booking_handover_checklist_print(request, booking_id: int):
    booking = get_object_or_404(
        Booking.objects.select_related("customer", "vehicle", "vehicle__brand", "vehicle__model").prefetch_related("handover"),
        id=booking_id,
    )
    guard = _branch_guard(request, booking)
    if guard:
        return guard
    doc_number = get_next_document_number(
        "HANDOVER",
        branch_name=booking.branch.name if booking.branch else None,
        branch_code=booking.branch.code if booking.branch else None,
    )
    context = {
        **_print_base_context(),
        "booking": booking,
        "doc_number": doc_number,
        "pdf_url": _append_query(f"/api/bookings/{booking.id}/handover-checklist.pdf", request, {"doc_number": doc_number}),
    }
    return render(request, "print/handover_checklist.html", context)


@login_required
@require_http_methods(["GET"])
def payment_receipt_print(request, payment_id: int):
    payment = get_object_or_404(
        Payment.objects.select_related("booking", "booking__customer", "booking__vehicle"),
        id=payment_id,
    )
    branch = get_active_branch(request)
    if branch and payment.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)
    context = {
        **_print_base_context(),
        "payment": payment,
        "doc_number": payment.receipt_number,
        "pdf_url": _append_query(f"/api/payments/{payment.id}/receipt.pdf", request, {"doc_number": payment.receipt_number}),
    }
    return render(request, "print/receipt.html", context)
