from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.accounts.permissions import ROLE_PERMISSIONS
from apps.customers.models import Customer
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment, Refund

User = get_user_model()


class StaffUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    default_branch = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "is_staff",
            "role",
            "permissions",
            "default_branch",
        ]

    def get_full_name(self, obj):
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or obj.username or obj.email

    def get_role(self, obj):
        role = getattr(obj, "role", None)
        if not role:
            return None
        return {"code": role.code, "name": role.name}

    def get_permissions(self, obj):
        if getattr(obj, "is_superuser", False):
            all_perms = set()
            for perm_list in ROLE_PERMISSIONS.values():
                all_perms.update(perm_list)
            return sorted(all_perms)
        role = getattr(obj, "role", None)
        return sorted(ROLE_PERMISSIONS.get(role.code, [])) if role else []

    def get_default_branch(self, obj):
        branch = getattr(obj, "default_branch", None)
        if not branch:
            return None
        return {"id": branch.id, "name": branch.name, "code": branch.code}


class StaffMaintenanceListSerializer(serializers.ModelSerializer):
    vehicle_display = serializers.SerializerMethodField()
    assignee_name = serializers.SerializerMethodField()
    branch_name = serializers.CharField(source="branch.name", read_only=True)

    class Meta:
        model = MaintenanceTask
        fields = [
            "id",
            "vehicle",
            "vehicle_display",
            "task_type",
            "priority",
            "status",
            "task_date",
            "due_date",
            "est_cost",
            "notes",
            "assignee",
            "assignee_name",
            "branch",
            "branch_name",
            "done_at",
            "created_at",
            "updated_at",
        ]

    def get_vehicle_display(self, obj):
        vehicle = getattr(obj, "vehicle", None)
        if not vehicle:
            return ""
        brand = getattr(getattr(vehicle, "brand", None), "name", "")
        model = getattr(getattr(vehicle, "model", None), "name", "")
        plate = getattr(vehicle, "plate_number", "")
        return f"{brand} {model} ({plate})".strip()

    def get_assignee_name(self, obj):
        assignee = getattr(obj, "assignee", None)
        if not assignee:
            return ""
        name = f"{assignee.first_name or ''} {assignee.last_name or ''}".strip()
        return name or assignee.email


class StaffMaintenanceCreateSerializer(serializers.Serializer):
    vehicle_id = serializers.IntegerField()
    task_type = serializers.ChoiceField(
        choices=[choice[0] for choice in MaintenanceTask.TYPE_CHOICES],
        default="SERVICE",
    )
    priority = serializers.ChoiceField(
        choices=[choice[0] for choice in MaintenanceTask.PRIORITY_CHOICES],
        default="MEDIUM",
    )
    due_date = serializers.DateField(required=False, allow_null=True)
    est_cost = serializers.DecimalField(
        max_digits=12,
        decimal_places=3,
        required=False,
        default=0,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    assignee_id = serializers.IntegerField(required=False, allow_null=True)
    branch_id = serializers.IntegerField(required=False, allow_null=True)


class StaffCustomerListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "id_type",
            "id_number",
            "phone_number",
            "email",
            "address",
            "license_number",
            "license_issuer",
            "license_issue_date",
            "license_expiry_date",
            "notes",
            "is_active",
            "created_at",
            "updated_at",
        ]


class StaffCustomerCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "name",
            "id_type",
            "id_number",
            "phone_number",
            "email",
            "address",
            "license_number",
            "license_issuer",
            "license_issue_date",
            "license_expiry_date",
            "notes",
            "is_active",
        ]


class StaffPaymentCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=3)
    method = serializers.ChoiceField(choices=[choice[0] for choice in Payment.METHOD_CHOICES], default="CASH")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=80)


class StaffRefundCreateSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=3)
    method = serializers.ChoiceField(choices=[choice[0] for choice in Refund.METHOD_CHOICES], default="CASH")
    notes = serializers.CharField(required=False, allow_blank=True, max_length=200)
    idempotency_key = serializers.CharField(required=False, allow_blank=True, max_length=80)
