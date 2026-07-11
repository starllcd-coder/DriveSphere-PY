from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Sum

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.payments.models import Payment
from apps.settings_app.services import get_next_document_number


class Command(BaseCommand):
    help = "Backfill missing advance payments for bookings that have deposit amount but no PAID payment rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--commit",
            action="store_true",
            help="Persist created payments. Without this flag, command runs in dry-run mode.",
        )
        parser.add_argument(
            "--booking-id",
            type=int,
            default=None,
            help="Limit backfill to a specific booking id.",
        )

    @staticmethod
    def _money(value) -> Decimal:
        try:
            return Decimal(str(value or 0)).quantize(Decimal("0.001"))
        except Exception:
            return Decimal("0.000")

    @staticmethod
    def _paid_total(booking) -> Decimal:
        return (
            Payment.objects.filter(booking=booking, status="PAID").aggregate(s=Sum("amount"))["s"]
            or Decimal("0.000")
        )

    def handle(self, *args, **options):
        commit = bool(options.get("commit"))
        target_booking_id = options.get("booking_id")

        qs = Booking.objects.select_related("branch", "created_by").all().order_by("id")
        if target_booking_id:
            qs = qs.filter(id=target_booking_id)

        created = 0
        skipped = 0

        with transaction.atomic():
            for booking in qs:
                deposit = self._money(getattr(booking, "deposit_amount", 0))
                if deposit <= 0:
                    skipped += 1
                    continue

                already_paid = self._money(self._paid_total(booking))
                if already_paid > 0:
                    skipped += 1
                    continue

                if not commit:
                    self.stdout.write(
                        f"[DRY-RUN] booking #{booking.id}: would create advance payment amount={deposit}"
                    )
                    created += 1
                    continue

                branch = getattr(booking, "branch", None)
                receipt_number = get_next_document_number(
                    "RECEIPT",
                    branch_name=branch.name if branch else None,
                    branch_code=branch.code if branch else None,
                )
                created_by = getattr(booking, "created_by", None)
                if created_by is None:
                    created_by = User.objects.filter(is_superuser=True).order_by("id").first()

                Payment.objects.create(
                    branch=branch,
                    booking=booking,
                    receipt_number=receipt_number,
                    payment_date=booking.created_at.date(),
                    method="CASH",
                    amount=deposit,
                    currency_code=booking.currency_code or "OMR",
                    status="PAID",
                    notes="Backfilled advance payment",
                    idempotency_key=f"ADV-BACKFILL-{booking.id}",
                    created_by=created_by,
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created advance payment for booking #{booking.id} amount={deposit}"
                    )
                )
                created += 1

            if not commit:
                transaction.set_rollback(True)

        mode = "COMMIT" if commit else "DRY-RUN"
        self.stdout.write(self.style.WARNING(f"{mode} finished. created={created}, skipped={skipped}"))
