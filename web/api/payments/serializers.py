from decimal import Decimal, InvalidOperation

from rest_framework import serializers

from apps.bookings.models import Booking
from apps.payments.models import Payment, Refund


class PaymentListSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source="booking.reference", read_only=True)
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
    customer_name = serializers.CharField(source="booking.customer.name", read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_number",
            "booking_id",
            "booking_reference",
            "customer_name",
            "vehicle_display",
            "branch_name",
            "payment_date",
            "method",
            "amount",
            "currency_code",
            "status",
            "notes",
            "created_by_email",
            "created_at",
            "updated_at",
        ]

    def get_vehicle_display(self, obj):
        booking = getattr(obj, "booking", None)
        if not booking or not booking.vehicle_id:
            return ""
        vehicle = booking.vehicle
        brand = getattr(getattr(vehicle, "brand", None), "name", "")
        model = getattr(getattr(vehicle, "model", None), "name", "")
        plate = getattr(vehicle, "plate_number", "")
        return f"{brand} {model} ({plate})".strip()


class PaymentDetailSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source="booking.reference", read_only=True)
    booking_id = serializers.IntegerField(source="booking.id", read_only=True)
    customer_name = serializers.CharField(source="booking.customer.name", read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "receipt_number",
            "booking_id",
            "booking_reference",
            "customer_name",
            "vehicle_display",
            "branch_name",
            "payment_date",
            "method",
            "amount",
            "currency_code",
            "status",
            "notes",
            "created_by_email",
            "created_at",
            "updated_at",
        ]

    def get_vehicle_display(self, obj):
        booking = getattr(obj, "booking", None)
        if not booking or not booking.vehicle_id:
            return ""
        vehicle = booking.vehicle
        brand = getattr(getattr(vehicle, "brand", None), "name", "")
        model = getattr(getattr(vehicle, "model", None), "name", "")
        plate = getattr(vehicle, "plate_number", "")
        return f"{brand} {model} ({plate})".strip()


class PaymentCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=3)
    method = serializers.ChoiceField(choices=Payment.METHOD_CHOICES, default="CASH")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=80)

    def validate_booking_id(self, value):
        try:
            booking = Booking.objects.get(pk=value)
        except Booking.DoesNotExist:
            raise serializers.ValidationError("Booking not found.")
        return value

    def validate_amount(self, value):
        try:
            amount = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError("Invalid amount.")
        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return amount

    def create(self, validated_data):
        return validated_data


class RefundCreateSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=3)
    method = serializers.ChoiceField(choices=Refund.METHOD_CHOICES, default="CASH")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=80)

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(pk=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Payment not found.")
        return value

    def validate_amount(self, value):
        try:
            amount = Decimal(value)
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError("Invalid amount.")
        if amount <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return amount

    def create(self, validated_data):
        return validated_data


class RefundDetailSerializer(serializers.ModelSerializer):
    payment_receipt_number = serializers.CharField(source="payment.receipt_number", read_only=True)
    booking_reference = serializers.CharField(source="payment.booking.reference", read_only=True)
    customer_name = serializers.CharField(source="payment.booking.customer.name", read_only=True)
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_email = serializers.CharField(source="created_by.email", read_only=True)

    class Meta:
        model = Refund
        fields = [
            "id",
            "refund_number",
            "payment",
            "payment_receipt_number",
            "booking_reference",
            "customer_name",
            "branch_name",
            "refund_date",
            "method",
            "amount",
            "currency_code",
            "status",
            "notes",
            "created_by_email",
            "created_at",
            "updated_at",
        ]
