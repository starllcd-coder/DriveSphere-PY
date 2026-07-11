from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.settings_app.services import get_next_document_number
from apps.settings_app.models import BusinessProfile
from apps.core.services import get_active_branch, log_audit_event
from .models import Payment, Refund


def _dec(v) -> Decimal:
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


def get_booking_net_paid(booking) -> Decimal:
    paid_total = (
        Payment.objects.filter(booking=booking, status="PAID").aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )
    refunded_total = (
        Refund.objects.filter(payment__booking=booking, status="REFUNDED").aggregate(s=Sum("amount"))["s"]
        or Decimal("0")
    )
    return _dec(paid_total) - _dec(refunded_total)


@transaction.atomic
def create_payment(*, request, booking, amount, method="CASH", notes="", idempotency_key: str = "") -> Payment:
    branch = get_active_branch(request)

    # Enforce same branch if branch is active
    if branch and booking.branch_id != branch.id:
        raise ValueError("Branch Mismatch: booking is not in active branch")

    key = (idempotency_key or "").strip()[:80]
    if key:
        existing = Payment.objects.filter(idempotency_key=key).select_related("booking").first()
        if existing:
            if existing.booking_id != booking.id or str(existing.amount) != str(_dec(amount)) or existing.method != method:
                raise ValueError("Idempotency key already used with different payment payload")
            return existing

    receipt_number = get_next_document_number(
        "RECEIPT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )

    business = BusinessProfile.get_solo()
    p = Payment.objects.create(
        branch=branch,
        booking=booking,
        receipt_number=receipt_number,
        payment_date=timezone.localdate(),
        method=method,
        amount=_dec(amount),
        currency_code=booking.currency_code or business.currency_code or "OMR",
        status="PAID",
        notes=(notes or "")[:200],
        idempotency_key=key or None,
        created_by=request.user,
    )
    log_audit_event(
        action="PAYMENT_CREATED",
        entity_type="Payment",
        entity_id=p.id,
        message=f"Payment {p.receipt_number} created",
        request=request,
        metadata={"booking_id": booking.id, "amount": str(p.amount), "method": p.method},
    )
    return p


@transaction.atomic
def create_refund(*, request, payment: Payment, amount, method="CASH", notes="", idempotency_key: str = "") -> Refund:
    branch = get_active_branch(request)

    if branch and payment.branch_id != branch.id:
        raise ValueError("Branch Mismatch: payment is not in active branch")

    if payment.status != "PAID":
        raise ValueError("Only paid payments can be refunded")

    refund_amount = _dec(amount)
    if refund_amount <= Decimal("0"):
        raise ValueError("Refund amount must be greater than zero")

    refunded_total = payment.refunds.filter(status="REFUNDED").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    if (refunded_total + refund_amount) > payment.amount:
        raise ValueError("Refund exceeds original payment amount")

    key = (idempotency_key or "").strip()[:80]
    if key:
        existing = Refund.objects.filter(idempotency_key=key).select_related("payment").first()
        if existing:
            if existing.payment_id != payment.id or str(existing.amount) != str(refund_amount) or existing.method != method:
                raise ValueError("Idempotency key already used with different refund payload")
            return existing

    refund_number = get_next_document_number(
        "RECEIPT",
        branch_name=branch.name if branch else None,
        branch_code=branch.code if branch else None,
    )

    business = BusinessProfile.get_solo()
    r = Refund.objects.create(
        branch=branch,
        payment=payment,
        refund_number=refund_number,
        refund_date=timezone.localdate(),
        method=method,
        amount=refund_amount,
        currency_code=payment.currency_code or business.currency_code or "OMR",
        status="REFUNDED",
        notes=(notes or "")[:200],
        idempotency_key=key or None,
        created_by=request.user,
    )
    log_audit_event(
        action="REFUND_CREATED",
        entity_type="Refund",
        entity_id=r.id,
        message=f"Refund {r.refund_number} created",
        request=request,
        metadata={"payment_id": payment.id, "amount": str(r.amount), "method": r.method},
    )
    return r
