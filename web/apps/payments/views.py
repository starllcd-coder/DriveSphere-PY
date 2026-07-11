import json
from datetime import date

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from apps.bookings.models import Booking
from apps.core.services import get_active_branch
from apps.documents.pdf_html import render_pdf_from_template
from apps.settings_app.models import BusinessProfile
from apps.settings_app.services import get_next_document_number
from apps.accounts.permissions import has_perm, is_admin
from apps.core.services import log_audit_event
from .models import Payment
from .services import create_payment, create_refund


def _json(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _date(v: str) -> date:
    return date.fromisoformat(v)


def _parse_date(v):
    if not v:
        return None
    try:
        return date.fromisoformat(str(v))
    except Exception:
        return None


# -------------------------
# PAGES
# -------------------------
@login_required
def payments_page(request):
    if not has_perm(request.user, "payments.view"):
        return render(request, "errors/403.html", status=403)
    return render(request, "payments/index.html")


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
def payments_report_print(request):
    if not has_perm(request.user, "payments.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    qs = Payment.objects.select_related("booking", "booking__customer", "branch").all().order_by("-payment_date", "-id")
    if branch:
        qs = qs.filter(branch=branch)

    doc_number = get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "pdf_url": _append_query("/api/payments/report.pdf", request, {"doc_number": doc_number}),
        "title": "Payments Report",
        "payments": list(qs[:2000]),
    }
    return render(request, "print/payments_report.html", context)


@login_required
def payment_new_page(request):
    if not has_perm(request.user, "payments.create"):
        return render(request, "errors/403.html", status=403)
    error = ""
    data = {}

    if request.method == "POST":
        booking_id = (request.POST.get("booking_id") or "").strip()
        amount = (request.POST.get("amount") or "").strip()
        method = request.POST.get("method") or "CASH"
        notes = (request.POST.get("notes") or "").strip()

        data = {
            "booking_id": booking_id,
            "amount": amount,
            "method": method,
            "notes": notes,
        }

        if not booking_id or not amount:
            error = "Booking ID and amount are required."
        else:
            booking = get_object_or_404(Booking, id=int(booking_id))
            try:
                create_payment(request=request, booking=booking, amount=amount, method=method, notes=notes)
                return redirect("payments_page")
            except Exception as exc:
                error = str(exc) or "Unable to create payment."

    context = {
        "title": "New Payment",
        "page_title": "New Payment",
        "payment": data,
        "error": error,
        "is_edit": False,
    }
    return render(request, "payments/payment_form.html", context)


@login_required
def payment_edit_page(request, payment_id: int):
    if not has_perm(request.user, "payments.manage"):
        return render(request, "errors/403.html", status=403)

    payment = get_object_or_404(Payment, id=payment_id)
    branch = get_active_branch(request)
    if branch and payment.branch_id != branch.id:
        return render(request, "errors/403.html", status=403)

    error = ""
    if request.method == "POST":
        amount = (request.POST.get("amount") or "").strip()
        method = request.POST.get("method") or payment.method
        notes = (request.POST.get("notes") or "").strip()

        if not amount:
            error = "Amount is required."
        else:
            payment.amount = amount
            payment.method = method
            payment.notes = notes[:200]
            payment.save(update_fields=["amount", "method", "notes"])
            return redirect("payments_page")

    context = {
        "title": "Edit Payment",
        "page_title": "Edit Payment",
        "payment": payment,
        "error": error,
        "is_edit": True,
    }
    return render(request, "payments/payment_form.html", context)


@login_required
def payment_delete_page(request, payment_id: int):
    if not has_perm(request.user, "payments.manage"):
        return render(request, "errors/403.html", status=403)

    payment = get_object_or_404(Payment, id=payment_id)
    branch = get_active_branch(request)
    if branch and payment.branch_id != branch.id:
        return render(request, "errors/403.html", status=403)

    if request.method == "POST":
        payment.status = "VOID"
        payment.save(update_fields=["status"])
        return redirect("payments_page")

    return render(request, "payments/payment_delete.html", {"payment": payment})


@login_required
def refund_new_page(request):
    if not has_perm(request.user, "payments.refund"):
        return render(request, "errors/403.html", status=403)
    error = ""
    data = {}

    if request.method == "POST":
        payment_id = (request.POST.get("payment_id") or "").strip()
        amount = (request.POST.get("amount") or "").strip()
        method = request.POST.get("method") or "CASH"
        notes = (request.POST.get("notes") or "").strip()

        data = {
            "payment_id": payment_id,
            "amount": amount,
            "method": method,
            "notes": notes,
        }

        if not payment_id or not amount:
            error = "Payment ID and amount are required."
        else:
            payment = get_object_or_404(Payment, id=int(payment_id))
            try:
                create_refund(request=request, payment=payment, amount=amount, method=method, notes=notes)
                return redirect("payments_page")
            except Exception as exc:
                error = str(exc) or "Unable to create refund."

    context = {
        "title": "Refund",
        "page_title": "Refund",
        "refund": data,
        "error": error,
    }
    return render(request, "payments/refund_form.html", context)


# -------------------------
# APIs
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_payments_list(request):
    if not has_perm(request.user, "payments.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    qs = Payment.objects.select_related("booking", "booking__customer", "branch").all().order_by("-payment_date", "-id")

    branch = get_active_branch(request)
    if branch:
        qs = qs.filter(branch=branch)

    booking_id = request.GET.get("booking_id")
    if booking_id:
        qs = qs.filter(booking_id=int(booking_id))

    method = (request.GET.get("method") or "").strip()
    if method:
        qs = qs.filter(method=method)

    date_from = _parse_date(request.GET.get("from") or request.GET.get("date_from"))
    if date_from:
        qs = qs.filter(payment_date__gte=date_from)

    date_to = _parse_date(request.GET.get("to") or request.GET.get("date_to"))
    if date_to:
        qs = qs.filter(payment_date__lte=date_to)

    status = request.GET.get("status")
    if status:
        qs = qs.filter(status=status)

    items = []
    for p in qs[:500]:
        items.append({
            "id": p.id,
            "receipt_number": p.receipt_number,
            "date": p.payment_date.isoformat(),
            "booking_id": p.booking_id,
            "customer_name": p.booking.customer.name,
            "method": p.method,
            "amount": str(p.amount),
            "currency": p.currency_code,
            "status": p.status,
            "notes": p.notes,
        })

    return JsonResponse({"ok": True, "results": items})


@login_required
@require_http_methods(["POST"])
def api_payments_create(request):
    if not has_perm(request.user, "payments.create"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    if "booking_id" not in data or "amount" not in data:
        return JsonResponse({"ok": False, "error": "booking_id and amount required"}, status=400)

    booking = get_object_or_404(Booking, id=int(data["booking_id"]))

    try:
        p = create_payment(
            request=request,
            booking=booking,
            amount=data["amount"],
            method=data.get("method", "CASH"),
            notes=data.get("notes", ""),
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True, "payment_id": p.id, "receipt_number": p.receipt_number})


@login_required
@require_http_methods(["POST"])
def api_refunds_create(request):
    if not has_perm(request.user, "payments.refund"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json(request)
    if "payment_id" not in data or "amount" not in data:
        return JsonResponse({"ok": False, "error": "payment_id and amount required"}, status=400)

    payment = get_object_or_404(Payment, id=int(data["payment_id"]))

    try:
        r = create_refund(
            request=request,
            payment=payment,
            amount=data["amount"],
            method=data.get("method", "CASH"),
            notes=data.get("notes", ""),
        )
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)

    return JsonResponse({"ok": True, "refund_id": r.id, "refund_number": r.refund_number})


@login_required
@require_http_methods(["POST"])
def api_payment_update(request, payment_id: int):
    if not has_perm(request.user, "payments.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    data = _json(request)
    payment = get_object_or_404(Payment, id=payment_id)

    branch = get_active_branch(request)
    if branch and payment.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)

    if "amount" in data:
        payment.amount = data.get("amount") or payment.amount
    if "method" in data:
        payment.method = data.get("method") or payment.method
    if "notes" in data:
        payment.notes = (data.get("notes") or "")[:200]

    payment.save(update_fields=["amount", "method", "notes"])
    log_audit_event(
        action="PAYMENT_UPDATED",
        entity_type="Payment",
        entity_id=payment.id,
        message=f"Payment {payment.receipt_number} updated",
        request=request,
        metadata={"amount": str(payment.amount), "method": payment.method},
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_payment_void(request, payment_id: int):
    if not has_perm(request.user, "payments.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    payment = get_object_or_404(Payment, id=payment_id)
    branch = get_active_branch(request)
    if branch and payment.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)

    payment.status = "VOID"
    payment.save(update_fields=["status"])
    log_audit_event(
        action="PAYMENT_VOIDED",
        entity_type="Payment",
        entity_id=payment.id,
        message=f"Payment {payment.receipt_number} voided",
        request=request,
    )
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["GET"])
def api_payment_receipt_pdf(request, payment_id: int):
    if not has_perm(request.user, "payments.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    payment = get_object_or_404(
        Payment.objects.select_related("booking", "booking__customer", "booking__vehicle"),
        id=payment_id
    )

    if branch and payment.branch_id != branch.id:
        return JsonResponse({"ok": False, "error": "Branch Access Denied"}, status=403)

    doc_number = request.GET.get("doc_number") or payment.receipt_number
    context = {
        **_print_base_context(),
        "payment": payment,
        "doc_number": doc_number,
    }
    return render_pdf_from_template(
        request=request,
        template="print/receipt.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="receipts",
    )


@login_required
@require_http_methods(["GET"])
def api_payments_report_pdf(request):
    if not has_perm(request.user, "payments.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)

    qs = Payment.objects.select_related("booking", "booking__customer", "branch").all().order_by("-payment_date", "-id")
    if branch:
        qs = qs.filter(branch=branch)

    doc_number = request.GET.get("doc_number") or get_next_document_number(
        "REPORT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )
    context = {
        **_print_base_context(),
        "doc_number": doc_number,
        "title": "Payments Report",
        "payments": list(qs[:2000]),
    }
    return render_pdf_from_template(
        request=request,
        template="print/payments_report.html",
        context=context,
        filename=f"{doc_number}.pdf",
        export_subdir="reports",
    )
