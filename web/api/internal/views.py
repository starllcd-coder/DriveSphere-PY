from decimal import Decimal, ROUND_HALF_UP

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import permissions, status
from rest_framework.views import APIView

from api.payments.serializers import PaymentDetailSerializer, PaymentListSerializer, RefundDetailSerializer
from api.bookings.serializers import BookingCreateSerializer, BookingDetailSerializer, BookingListSerializer
from api.responses import api_error, api_ok, paginated_list_response
from apps.accounts.permissions import has_perm
from apps.bookings.models import Booking
from apps.bookings.services import (
    BookingError,
    activate_upcoming_booking,
    checkout_booking,
    extend_booking,
    finalize_return,
)
from apps.customers.models import Customer
from apps.dashboard.services import get_dashboard_kpis
from apps.fleet.models import Vehicle
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment
from apps.payments.services import create_payment, create_refund, get_booking_net_paid
from apps.reports.services import (
    get_customers,
    get_financial,
    get_fleet,
    get_maintenance,
    get_overview,
)
from apps.settings_app.models import Branch, BusinessProfile

from .serializers import (
    StaffCustomerCreateUpdateSerializer,
    StaffCustomerListSerializer,
    StaffMaintenanceCreateSerializer,
    StaffMaintenanceListSerializer,
    StaffPaymentCreateSerializer,
    StaffRefundCreateSerializer,
    StaffUserSerializer,
)

User = get_user_model()


def _money(value) -> Decimal:
    try:
        amount = Decimal(str(value))
    except Exception:
        amount = Decimal("0")
    return amount.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def _is_admin_like(user) -> bool:
    return bool(getattr(user, "is_superuser", False) or has_perm(user, "settings.manage"))


def _resolve_branch_for_staff_request(request):
    requested_id = request.query_params.get("branch_id")
    if requested_id in (None, "") and hasattr(request, "data"):
        requested_id = request.data.get("branch_id")
    requested_id = str(requested_id).strip() if requested_id is not None else ""
    user_default_branch = getattr(request.user, "default_branch", None)

    if requested_id:
        branch = Branch.objects.filter(id=requested_id, is_active=True).first()
        if not branch:
            return None, api_error("Branch not found.", http_status=status.HTTP_404_NOT_FOUND)
        if _is_admin_like(request.user):
            return branch, None
        if user_default_branch and user_default_branch.id == branch.id:
            return branch, None
        return None, api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)

    if user_default_branch:
        return user_default_branch, None
    if _is_admin_like(request.user):
        return None, None
    return None, api_error("No default branch is assigned.", http_status=status.HTTP_403_FORBIDDEN)


def _resolve_report_filters(request, default_period="monthly"):
    period = (request.query_params.get("period") or default_period).strip().lower()
    if period not in {"today", "weekly", "monthly"}:
        period = default_period

    date_from = None
    date_to = None
    date_from_raw = (request.query_params.get("date_from") or "").strip()
    date_to_raw = (request.query_params.get("date_to") or "").strip()
    if date_from_raw or date_to_raw:
        if not (date_from_raw and date_to_raw):
            return None, None, api_error(
                "Both date_from and date_to are required for custom range.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
        date_from = parse_date(date_from_raw)
        date_to = parse_date(date_to_raw)
        if not date_from or not date_to:
            return None, None, api_error(
                "Invalid date format. Use YYYY-MM-DD.",
                http_status=status.HTTP_400_BAD_REQUEST,
            )
    return period, (date_from, date_to), None


class StaffBootstrapAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        branch, err = _resolve_branch_for_staff_request(request)
        if err:
            return err
        business = BusinessProfile.get_solo()
        logo_url = ""
        if getattr(business, "logo", None):
            try:
                logo_url = request.build_absolute_uri(business.logo.url)
            except Exception:
                logo_url = ""

        profile = StaffUserSerializer(request.user).data
        branches_qs = Branch.objects.filter(is_active=True).order_by("name")
        if not _is_admin_like(request.user):
            if branch:
                branches_qs = branches_qs.filter(id=branch.id)
            else:
                branches_qs = Branch.objects.none()

        return api_ok(
            data={
                "profile": profile,
                "active_branch": (
                    {"id": branch.id, "name": branch.name, "code": branch.code}
                    if branch
                    else None
                ),
                "branches": [
                    {"id": item.id, "name": item.name, "code": item.code}
                    for item in branches_qs
                ],
                "business_profile": {
                    "name": (business.business_name or "").strip(),
                    "logo_url": logo_url,
                },
            }
        )


class StaffEmployeesListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "employees.manage"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        query = (request.query_params.get("q") or "").strip()
        queryset = User.objects.select_related("role", "default_branch").filter(is_active=True)
        if query:
            queryset = queryset.filter(
                Q(email__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(username__icontains=query)
            )
        queryset = queryset.order_by("-id")
        return paginated_list_response(request, queryset, StaffUserSerializer)


class StaffMaintenanceListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "maintenance.view"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        branch, err = _resolve_branch_for_staff_request(request)
        if err:
            return err

        queryset = MaintenanceTask.objects.select_related(
            "vehicle",
            "vehicle__brand",
            "vehicle__model",
            "assignee",
            "branch",
        ).order_by("-task_date", "-id")
        if branch:
            queryset = queryset.filter(branch=branch)

        show_done = (request.query_params.get("show_done") or "").lower() in {
            "1",
            "true",
            "yes",
        }
        if not show_done:
            queryset = queryset.exclude(status__in=["DONE", "CANCELLED"])

        return paginated_list_response(request, queryset, StaffMaintenanceListSerializer)

    def post(self, request, *args, **kwargs):
        if not has_perm(request.user, "maintenance.create"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        serializer = StaffMaintenanceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        branch, err = _resolve_branch_for_staff_request(request)
        if err:
            return err

        vehicle = get_object_or_404(Vehicle, pk=data["vehicle_id"])
        assignee = request.user
        assignee_id = data.get("assignee_id")
        if assignee_id:
            assignee = get_object_or_404(User, pk=assignee_id)

        task = MaintenanceTask.objects.create(
            branch=branch if branch else getattr(vehicle, "branch", None),
            vehicle=vehicle,
            task_type=data.get("task_type", "SERVICE"),
            priority=data.get("priority", "MEDIUM"),
            status="OPEN",
            assignee=assignee,
            due_date=data.get("due_date"),
            est_cost=data.get("est_cost") or 0,
            notes=data.get("notes") or "",
        )
        if vehicle.status != "MAINTENANCE":
            vehicle.status = "MAINTENANCE"
            vehicle.save(update_fields=["status"])

        output = StaffMaintenanceListSerializer(task).data
        return api_ok(
            message="Maintenance task created.",
            data=output,
            http_status=status.HTTP_201_CREATED,
        )


class StaffMaintenanceMarkDoneAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, task_id, *args, **kwargs):
        if not has_perm(request.user, "maintenance.update"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err

        task = get_object_or_404(MaintenanceTask.objects.select_related("vehicle", "branch"), pk=task_id)
        if branch and task.branch_id and task.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)

        task.status = "DONE"
        task.done_at = timezone.now()
        task.save(update_fields=["status", "done_at", "updated_at"])

        vehicle = getattr(task, "vehicle", None)
        if vehicle and vehicle.status == "MAINTENANCE":
            vehicle.status = "AVAILABLE"
            vehicle.save(update_fields=["status"])

        return api_ok(message="Task marked done.", data={"task_id": task.id, "status": task.status})


class StaffReportsOverviewAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not (
            has_perm(request.user, "reports.view")
            or has_perm(request.user, "reports.view_financial")
            or has_perm(request.user, "reports.view_limited")
            or has_perm(request.user, "reports.view_maintenance")
        ):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        period, date_range, err = _resolve_report_filters(request, default_period="today")
        if err:
            return err

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err

        date_from, date_to = date_range if date_range else (None, None)
        return api_ok(
            data=get_overview(
                period=period,
                branch=branch,
                date_from=date_from,
                date_to=date_to,
            )
        )


class StaffDashboardKpisAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        return api_ok(data=get_dashboard_kpis(active_branch=branch))


class StaffCustomersListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not (has_perm(request.user, "customers.view") or has_perm(request.user, "customers.manage")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        queryset = Customer.objects.all().order_by("name", "id")
        query = (request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(phone_number__icontains=query)
                | Q(email__icontains=query)
                | Q(id_number__icontains=query)
                | Q(license_number__icontains=query)
            )

        return paginated_list_response(request, queryset, StaffCustomerListSerializer)

    def post(self, request, *args, **kwargs):
        if not has_perm(request.user, "customers.manage"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        serializer = StaffCustomerCreateUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = serializer.save()
        return api_ok(
            message="Customer created.",
            data=StaffCustomerListSerializer(customer).data,
            http_status=status.HTTP_201_CREATED,
        )


class StaffCustomerDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, customer_id, *args, **kwargs):
        if not (has_perm(request.user, "customers.view") or has_perm(request.user, "customers.manage")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        customer = get_object_or_404(Customer, pk=customer_id)
        return api_ok(data=StaffCustomerListSerializer(customer).data)

    def put(self, request, customer_id, *args, **kwargs):
        if not has_perm(request.user, "customers.manage"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        customer = get_object_or_404(Customer, pk=customer_id)
        serializer = StaffCustomerCreateUpdateSerializer(customer, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return api_ok(message="Customer updated.", data=StaffCustomerListSerializer(customer).data)

    def delete(self, request, customer_id, *args, **kwargs):
        if not has_perm(request.user, "customers.manage"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        customer = get_object_or_404(Customer, pk=customer_id)
        customer.delete()
        return api_ok(message="Customer deleted.", data={"customer_id": customer_id})


class StaffPaymentsListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "payments.view"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err

        queryset = Payment.objects.select_related(
            "booking",
            "booking__customer",
            "booking__vehicle",
            "booking__vehicle__brand",
            "booking__vehicle__model",
            "branch",
            "created_by",
        ).order_by("-payment_date", "-id")
        if branch:
            queryset = queryset.filter(branch=branch)

        booking_id = request.query_params.get("booking_id")
        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        method = request.query_params.get("method")
        if method:
            queryset = queryset.filter(method=method)
        query = (request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(receipt_number__icontains=query)
                | Q(notes__icontains=query)
                | Q(booking__customer__name__icontains=query)
            )

        return paginated_list_response(request, queryset, PaymentListSerializer)

    def post(self, request, *args, **kwargs):
        if not has_perm(request.user, "payments.create"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        serializer = StaffPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        booking = get_object_or_404(Booking, pk=data["booking_id"])

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        effective_branch = branch or getattr(booking, "branch", None)
        if effective_branch:
            request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = effective_branch.id

        try:
            payment = create_payment(
                request=request,
                booking=booking,
                amount=data["amount"],
                method=data.get("method", "CASH"),
                notes=data.get("notes", ""),
                idempotency_key=data.get("idempotency_key", ""),
            )
        except ValueError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)

        return api_ok(
            message="Payment created.",
            data=PaymentDetailSerializer(payment).data,
            http_status=status.HTTP_201_CREATED,
        )


class StaffRefundCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not (has_perm(request.user, "payments.refund") or has_perm(request.user, "payments.manage")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        serializer = StaffRefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        payment = get_object_or_404(Payment, pk=data["payment_id"])

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        effective_branch = branch or getattr(payment, "branch", None)
        if effective_branch:
            request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = effective_branch.id

        try:
            refund = create_refund(
                request=request,
                payment=payment,
                amount=data["amount"],
                method=data.get("method", "CASH"),
                notes=data.get("notes", ""),
                idempotency_key=data.get("idempotency_key", ""),
            )
        except ValueError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)

        return api_ok(
            message="Refund created.",
            data=RefundDetailSerializer(refund).data,
            http_status=status.HTTP_201_CREATED,
        )


class StaffReportsFinancialAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not (has_perm(request.user, "reports.view_financial") or has_perm(request.user, "reports.view")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        period, date_range, err = _resolve_report_filters(request, default_period="monthly")
        if err:
            return err
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        date_from, date_to = date_range if date_range else (None, None)
        return api_ok(
            data=get_financial(
                period=period,
                branch=branch,
                date_from=date_from,
                date_to=date_to,
            )
        )


class StaffReportsFleetAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "reports.view"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        period, date_range, err = _resolve_report_filters(request, default_period="monthly")
        if err:
            return err
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        date_from, date_to = date_range if date_range else (None, None)
        return api_ok(
            data=get_fleet(
                period=period,
                branch=branch,
                date_from=date_from,
                date_to=date_to,
            )
        )


class StaffReportsCustomersAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not (has_perm(request.user, "reports.view_limited") or has_perm(request.user, "reports.view")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        period, date_range, err = _resolve_report_filters(request, default_period="monthly")
        if err:
            return err
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        date_from, date_to = date_range if date_range else (None, None)
        return api_ok(
            data=get_customers(
                period=period,
                branch=branch,
                date_from=date_from,
                date_to=date_to,
            )
        )


class StaffReportsMaintenanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not (has_perm(request.user, "reports.view_maintenance") or has_perm(request.user, "reports.view")):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        period, date_range, err = _resolve_report_filters(request, default_period="monthly")
        if err:
            return err
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        date_from, date_to = date_range if date_range else (None, None)
        return api_ok(
            data=get_maintenance(
                period=period,
                branch=branch,
                date_from=date_from,
                date_to=date_to,
            )
        )


class StaffBookingsListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "bookings.view"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err

        queryset = Booking.objects.select_related(
            "branch",
            "customer",
            "vehicle",
            "vehicle__brand",
            "vehicle__model",
            "created_by",
        ).order_by("-pickup_date", "-id")
        if branch:
            queryset = queryset.filter(branch=branch)

        query = (request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(customer__name__icontains=query)
                | Q(reference__icontains=query)
                | Q(vehicle__plate_number__icontains=query)
            )
        status_filter = (request.query_params.get("status") or "").strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return paginated_list_response(request, queryset, BookingListSerializer)

    def post(self, request, *args, **kwargs):
        if not has_perm(request.user, "bookings.create"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch:
            request.session[settings.ACTIVE_BRANCH_SESSION_KEY] = branch.id

        serializer = BookingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        try:
            booking = serializer.save()
        except BookingError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)

        return api_ok(
            message="Booking created.",
            data={"booking": BookingDetailSerializer(booking).data},
            http_status=status.HTTP_201_CREATED,
        )


class StaffBookingActivateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.update"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)
        try:
            activate_upcoming_booking(booking, user=request.user)
        except BookingError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)
        return api_ok(message="Booking activated.", data={"booking_id": booking.id, "status": booking.status})


class StaffBookingExtendAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.extend"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)

        new_return_date = request.data.get("new_return_date")
        if not new_return_date:
            return api_error("new_return_date is required.", http_status=status.HTTP_400_BAD_REQUEST)
        try:
            parsed_date = timezone.datetime.fromisoformat(str(new_return_date)).date()
        except Exception:
            return api_error("Invalid date format.", http_status=status.HTTP_400_BAD_REQUEST)

        try:
            extend_booking(booking, new_return_date=parsed_date, user=request.user)
        except BookingError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)
        return api_ok(
            message="Booking extended.",
            data={"booking_id": booking.id, "return_date": booking.return_date.isoformat()},
        )


class StaffBookingCheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.checkout"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)
        try:
            checkout_booking(
                booking,
                inspector=request.user,
                odometer_out_km=request.data.get("odometer_out_km") or request.data.get("odo") or 0,
                fuel_out_percent=request.data.get("fuel_out_percent") or request.data.get("fuel") or 100,
                checklist=request.data.get("checklist") or {},
                customer_signature_data=request.data.get("signature") or "",
            )
        except BookingError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)
        return api_ok(message="Booking checked out.", data={"booking_id": booking.id, "status": booking.status})


class StaffBookingReturnAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.return"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)

        date_value = request.data.get("actual_return_date") or request.data.get("date")
        if date_value:
            try:
                actual_return_date = timezone.datetime.fromisoformat(str(date_value)).date()
            except Exception:
                return api_error("Invalid return date format.", http_status=status.HTTP_400_BAD_REQUEST)
        else:
            actual_return_date = timezone.localdate()

        try:
            if booking.status != "CHECKED_OUT":
                checkout_booking(
                    booking,
                    inspector=request.user,
                    odometer_out_km=request.data.get("odometer_out_km") or 0,
                    fuel_out_percent=request.data.get("fuel_out_percent") or 100,
                    checklist=request.data.get("checklist") or {},
                    customer_signature_data=request.data.get("signature") or "",
                )
            ret = finalize_return(
                booking,
                inspector=request.user,
                inspector_name=request.data.get("inspector_name") or request.user.get_full_name() or request.user.email,
                actual_return_date=actual_return_date,
                odometer_in_km=request.data.get("odometer_in_km") or request.data.get("odo") or 0,
                fuel_return_percent=request.data.get("fuel_return_percent") or request.data.get("fuel") or 100,
                fuel_charge=request.data.get("fuel_charge") or 0,
                late_fee=request.data.get("late_fee") or 0,
                damage_fee=request.data.get("damage_fee") or 0,
                other_fee=request.data.get("other_fee") or 0,
                damage_details=request.data.get("damage_details") or request.data.get("damage") or "",
                inspector_signature_data=request.data.get("signature") or "",
                extra_km_override=request.data.get("extra_km"),
            )
            payable_total = _money(ret.final_due)
            already_paid = _money(get_booking_net_paid(booking))
            balance_before_payment = _money(payable_total - already_paid)
            payment_amount_raw = str(request.data.get("payment_amount") or "").strip()
            if not payment_amount_raw:
                payment_amount_raw = str(max(balance_before_payment, Decimal("0")))
            payment_amount = _money(payment_amount_raw)

            if payment_amount > 0:
                already_paid_today = Payment.objects.filter(
                    booking=booking,
                    status="PAID",
                    payment_date=timezone.localdate(),
                    amount=payment_amount,
                ).exists()
                if not already_paid_today:
                    create_payment(
                        request=request,
                        booking=booking,
                        amount=str(payment_amount),
                        method=(request.data.get("payment_method") or "CASH"),
                        notes=(request.data.get("payment_notes") or "Return settlement"),
                    )
            balance_due = _money(balance_before_payment - payment_amount)
        except BookingError as exc:
            return api_error(str(exc), http_status=status.HTTP_400_BAD_REQUEST)

        return api_ok(
            message="Booking returned.",
            data={
                "booking_id": booking.id,
                "status": booking.status,
                "final_due": str(ret.final_due),
                "early_return_credit": str(getattr(ret, "early_return_credit", 0)),
                "payable_total": str(payable_total),
                "already_paid": str(already_paid),
                "collected_amount": str(payment_amount),
                "balance_before_payment": str(balance_before_payment),
                "balance_due": str(balance_due),
            },
        )


class StaffBookingCancelAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.delete"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)
        if booking.status in {"RETURNED", "CLOSED", "CANCELLED"}:
            return api_error("Booking cannot be cancelled in current status.", http_status=status.HTTP_400_BAD_REQUEST)
        booking.status = "CANCELLED"
        booking.save(update_fields=["status", "updated_at"])
        vehicle = getattr(booking, "vehicle", None)
        if vehicle and getattr(vehicle, "status", "") != "AVAILABLE":
            vehicle.status = "AVAILABLE"
            vehicle.save(update_fields=["status"])
        return api_ok(message="Booking cancelled.", data={"booking_id": booking.id, "status": booking.status})


class StaffBookingDetailUpdateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.view"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(
            Booking.objects.select_related(
                "branch",
                "customer",
                "vehicle",
                "vehicle__brand",
                "vehicle__model",
                "created_by",
            ),
            pk=booking_id,
        )
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)
        return api_ok(data=BookingDetailSerializer(booking).data)

    def put(self, request, booking_id, *args, **kwargs):
        if not has_perm(request.user, "bookings.update"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)
        booking = get_object_or_404(Booking, pk=booking_id)
        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err
        if branch and booking.branch_id and booking.branch_id != branch.id:
            return api_error("Branch access denied.", http_status=status.HTTP_403_FORBIDDEN)

        pickup_date = request.data.get("pickup_date")
        return_date = request.data.get("return_date")
        status_value = request.data.get("status")
        notes = request.data.get("notes")
        pickup_location = request.data.get("pickup_location")
        return_location = request.data.get("return_location")

        if pickup_date:
            try:
                booking.pickup_date = timezone.datetime.fromisoformat(str(pickup_date)).date()
            except Exception:
                return api_error("Invalid pickup_date format.", http_status=status.HTTP_400_BAD_REQUEST)
        if return_date:
            try:
                booking.return_date = timezone.datetime.fromisoformat(str(return_date)).date()
            except Exception:
                return api_error("Invalid return_date format.", http_status=status.HTTP_400_BAD_REQUEST)
        if booking.return_date < booking.pickup_date:
            return api_error("return_date cannot be earlier than pickup_date.", http_status=status.HTTP_400_BAD_REQUEST)

        allowed_statuses = {choice[0] for choice in Booking.STATUS_CHOICES}
        if status_value is not None:
            if status_value not in allowed_statuses:
                return api_error("Invalid booking status.", http_status=status.HTTP_400_BAD_REQUEST)
            booking.status = status_value
        if notes is not None:
            booking.notes = str(notes)
        if pickup_location is not None:
            booking.pickup_location = str(pickup_location)
        if return_location is not None:
            booking.return_location = str(return_location)

        booking.save()
        return api_ok(message="Booking updated.", data=BookingDetailSerializer(booking).data)


class StaffVehicleAvailabilityAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not has_perm(request.user, "bookings.create"):
            return api_error("Forbidden", http_status=status.HTTP_403_FORBIDDEN)

        pickup = parse_date(request.query_params.get("pickup"))
        ret = parse_date(request.query_params.get("return"))

        if not pickup or not ret:
            return api_error("Dates Required", http_status=status.HTTP_400_BAD_REQUEST)

        branch, err = _resolve_branch_for_staff_request(request)
        if err and not _is_admin_like(request.user):
            return err

        booked = Booking.objects.filter(
            pickup_date__lt=ret,
            return_date__gt=pickup,
        ).exclude(status__in=["CANCELLED", "RETURNED", "CLOSED"])

        if branch:
            booked = booked.filter(branch=branch)

        vehicles = Vehicle.objects.exclude(
            id__in=booked.values_list("vehicle_id", flat=True)
        ).select_related("brand", "model")

        out = []
        for v in vehicles:
            out.append(
                {
                    "id": v.id,
                    "name": f"{getattr(v.brand, 'name', '')} {getattr(v.model, 'name', '')}".strip(),
                    "plate": v.plate_number,
                    "rate": float(getattr(v, "daily_rate", 0) or 0),
                    "deposit": float(getattr(v, "deposit", 0) or 0),
                }
            )

        return api_ok(data=out)
