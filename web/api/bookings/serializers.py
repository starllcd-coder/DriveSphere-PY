from decimal import Decimal

from rest_framework import serializers

from apps.bookings.models import Booking, BookingDriver
from apps.bookings.services import create_booking
from apps.core.services import get_active_branch
from apps.customers.models import Customer
from apps.fleet.models import Vehicle


class BookingCreateSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField(required=False)
    customer_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    customer_phone_number = serializers.CharField(required=False, allow_blank=True, max_length=40)
    customer_id_type = serializers.CharField(required=False, allow_blank=True, max_length=20)
    customer_id_number = serializers.CharField(required=False, allow_blank=True, max_length=80)
    customer_email = serializers.CharField(required=False, allow_blank=True, max_length=120)
    customer_address = serializers.CharField(required=False, allow_blank=True, max_length=200)
    customer_license_number = serializers.CharField(required=False, allow_blank=True, max_length=80)
    customer_license_issuer = serializers.CharField(required=False, allow_blank=True, max_length=80)
    customer_license_issue_date = serializers.DateField(required=False, allow_null=True)
    customer_license_expiry_date = serializers.DateField(required=False, allow_null=True)
    vehicle_id = serializers.IntegerField()

    pickup_date = serializers.DateField()
    return_date = serializers.DateField()

    pickup_time = serializers.TimeField(required=False, allow_null=True)
    return_time = serializers.TimeField(required=False, allow_null=True)

    pickup_location = serializers.CharField(required=False, allow_blank=True, max_length=200)
    return_location = serializers.CharField(required=False, allow_blank=True, max_length=200)

    notes = serializers.CharField(required=False, allow_blank=True)

    currency_code = serializers.CharField(required=False, allow_blank=True, max_length=10)
    currency_symbol = serializers.CharField(required=False, allow_blank=True, max_length=10)

    daily_rate = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)
    deposit_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)

    extras_total = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)
    vat_rate = serializers.DecimalField(required=False, max_digits=6, decimal_places=3)
    vat_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)

    subtotal_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)
    total_amount = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)

    included_km_per_day = serializers.IntegerField(required=False)
    rate_per_extra_km = serializers.DecimalField(required=False, max_digits=10, decimal_places=3)

    status = serializers.ChoiceField(required=False, choices=Booking.STATUS_CHOICES)
    extras = serializers.ListField(required=False)
    drivers = serializers.ListField(required=False)

    def validate_customer_id(self, value):
        try:
            Customer.objects.get(pk=value)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer not found.")
        return value

    def validate_vehicle_id(self, value):
        try:
            vehicle = Vehicle.objects.get(pk=value)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError("Vehicle not found.")
        return value

    def validate(self, attrs):
        pickup_date = attrs["pickup_date"]
        return_date = attrs["return_date"]

        customer_id = attrs.get("customer_id")
        customer_name = (attrs.get("customer_name") or "").strip()

        if not customer_id and not customer_name:
            raise serializers.ValidationError(
                {"customer_id": "customer_id or customer_name is required."}
            )

        if return_date < pickup_date:
            raise serializers.ValidationError(
                {"return_date": "Return date cannot be earlier than pickup date."}
            )

        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        extras = validated_data.pop("extras", None)
        drivers = validated_data.pop("drivers", None)

        customer_id = validated_data.pop("customer_id", None)
        customer_name = (validated_data.pop("customer_name", "") or "").strip()
        customer_phone_number = (validated_data.pop("customer_phone_number", "") or "").strip()
        customer_id_type = (validated_data.pop("customer_id_type", "") or "").strip() or "ID"
        customer_id_number = (validated_data.pop("customer_id_number", "") or "").strip()
        customer_email = (validated_data.pop("customer_email", "") or "").strip()
        customer_address = (validated_data.pop("customer_address", "") or "").strip()
        customer_license_number = (validated_data.pop("customer_license_number", "") or "").strip()
        customer_license_issuer = (validated_data.pop("customer_license_issuer", "") or "").strip()
        customer_license_issue_date = validated_data.pop("customer_license_issue_date", None)
        customer_license_expiry_date = validated_data.pop("customer_license_expiry_date", None)
        if customer_id:
            customer = Customer.objects.get(pk=customer_id)
        else:
            customer = Customer.objects.create(
                name=customer_name,
                phone_number=customer_phone_number,
                id_type=customer_id_type,
                id_number=customer_id_number,
                email=customer_email,
                address=customer_address,
                license_number=customer_license_number,
                license_issuer=customer_license_issuer,
                license_issue_date=customer_license_issue_date,
                license_expiry_date=customer_license_expiry_date,
            )
        vehicle = Vehicle.objects.get(pk=validated_data.pop("vehicle_id"))

        branch = get_active_branch(request)
        booking = create_booking(
            branch=branch,
            created_by=request.user,
            customer=customer,
            vehicle=vehicle,
            pickup_date=validated_data.get("pickup_date"),
            return_date=validated_data.get("return_date"),
            daily_rate=validated_data.get("daily_rate"),
            deposit_amount=validated_data.get("deposit_amount"),
            vat_rate=validated_data.get("vat_rate"),
            extras=extras,
            status=validated_data.get("status", "CONFIRMED"),
            notes=validated_data.get("notes", ""),
        )

        booking.pickup_time = validated_data.get("pickup_time")
        booking.return_time = validated_data.get("return_time")
        booking.pickup_location = validated_data.get("pickup_location", "")
        booking.return_location = validated_data.get("return_location", "")
        booking.notes = validated_data.get("notes", "")

        if validated_data.get("currency_code"):
            booking.currency_code = validated_data.get("currency_code")
        if validated_data.get("currency_symbol"):
            booking.currency_symbol = validated_data.get("currency_symbol")

        if validated_data.get("included_km_per_day") is not None:
            booking.included_km_per_day = validated_data.get("included_km_per_day")
        if validated_data.get("rate_per_extra_km") is not None:
            booking.rate_per_extra_km = validated_data.get("rate_per_extra_km")

        booking.save(
            update_fields=[
                "pickup_time",
                "return_time",
                "pickup_location",
                "return_location",
                "notes",
                "currency_code",
                "currency_symbol",
                "included_km_per_day",
                "rate_per_extra_km",
                "updated_at",
            ]
        )

        if drivers:
            BookingDriver.objects.filter(booking=booking).delete()
            for d in drivers:
                name = (d.get("name") or "").strip()
                if not name:
                    continue
                BookingDriver.objects.create(
                    booking=booking,
                    name=name,
                    phone_number=(d.get("phone_number") or d.get("phone") or "").strip(),
                    id_number=(d.get("id_number") or "").strip(),
                    license_number=(d.get("license_number") or d.get("license") or "").strip(),
                )

        return booking


class BookingListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "customer_name",
            "vehicle_display",
            "branch_name",
            "pickup_date",
            "return_date",
            "pickup_location",
            "return_location",
            "status",
            "currency_code",
            "daily_rate",
            "deposit_amount",
            "subtotal_amount",
            "total_amount",
            "created_by_username",
            "created_at",
            "updated_at",
        ]

    def get_vehicle_display(self, obj):
        vehicle = getattr(obj, "vehicle", None)
        if not vehicle:
            return ""

        brand_name = getattr(getattr(vehicle, "brand", None), "name", "")
        model_name = getattr(getattr(vehicle, "model", None), "name", "")
        plate_number = getattr(vehicle, "plate_number", "")
        return f"{brand_name} {model_name} ({plate_number})".strip()


class BookingDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    vehicle_display = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Booking
        fields = [
            "id",
            "reference",
            "branch",
            "branch_name",
            "customer",
            "customer_name",
            "vehicle",
            "vehicle_display",
            "created_by",
            "created_by_username",
            "pickup_date",
            "return_date",
            "pickup_time",
            "return_time",
            "pickup_location",
            "return_location",
            "status",
            "currency_code",
            "currency_symbol",
            "daily_rate",
            "deposit_amount",
            "extras_total",
            "vat_rate",
            "vat_amount",
            "subtotal_amount",
            "total_amount",
            "notes",
            "included_km_per_day",
            "rate_per_extra_km",
            "invoice_generated",
            "agreement_generated",
            "created_at",
            "updated_at",
        ]

    def get_vehicle_display(self, obj):
        vehicle = getattr(obj, "vehicle", None)
        if not vehicle:
            return ""

        brand_name = getattr(getattr(vehicle, "brand", None), "name", "")
        model_name = getattr(getattr(vehicle, "model", None), "name", "")
        plate_number = getattr(vehicle, "plate_number", "")
        return f"{brand_name} {model_name} ({plate_number})".strip()
