import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.payments.models import Payment, Refund
from apps.payments.services import create_payment, create_refund

from api.responses import api_ok, paginated_list_response

from .serializers import (
    PaymentCreateSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    RefundCreateSerializer,
    RefundDetailSerializer,
)


class PaymentCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        booking = get_object_or_404(Booking, pk=serializer.validated_data["booking_id"])
        key = (
            (request.headers.get("Idempotency-Key") or "").strip()
            or (serializer.validated_data.get("idempotency_key") or "").strip()
        )
        existed_before = bool(key and Payment.objects.filter(idempotency_key=key).exists())

        try:
            payment = create_payment(
                request=request,
                booking=booking,
                amount=serializer.validated_data["amount"],
                method=serializer.validated_data["method"],
                notes=serializer.validated_data.get("notes", ""),
                idempotency_key=key,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "message": "Payment request replayed (idempotent)." if existed_before else "Payment created successfully.",
            "payment": PaymentDetailSerializer(payment).data,
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(
                message=payload["message"],
                data={"payment": payload["payment"]},
                http_status=status.HTTP_200_OK if existed_before else status.HTTP_201_CREATED,
            )
        return Response(payload, status=status.HTTP_200_OK if existed_before else status.HTTP_201_CREATED)


class PaymentListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        booking_id = request.query_params.get("booking_id")
        status_filter = request.query_params.get("status")
        method = request.query_params.get("method")
        ordering = (request.query_params.get("ordering") or "-payment_date").strip()
        allowed_ordering = {
            "payment_date",
            "-payment_date",
            "amount",
            "-amount",
            "created_at",
            "-created_at",
            "id",
            "-id",
        }
        if ordering not in allowed_ordering:
            ordering = "-payment_date"

        queryset = (
            Payment.objects.select_related(
                "booking",
                "booking__customer",
                "booking__vehicle",
                "booking__vehicle__brand",
                "booking__vehicle__model",
                "branch",
                "created_by",
            )
            .all()
            .order_by(ordering, "-id")
        )

        if booking_id:
            queryset = queryset.filter(booking_id=booking_id)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if method:
            queryset = queryset.filter(method=method)

        query = (request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(notes__icontains=query)
                | Q(receipt_number__icontains=query)
                | Q(booking__customer__name__icontains=query)
                | Q(booking__vehicle__plate_number__icontains=query)
            )

        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, queryset, PaymentListSerializer)
        serializer = PaymentListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PaymentDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        payment = get_object_or_404(
            Payment.objects.select_related(
                "booking",
                "booking__customer",
                "booking__vehicle",
                "booking__vehicle__brand",
                "booking__vehicle__model",
                "branch",
                "created_by",
            ),
            pk=pk,
        )
        data = PaymentDetailSerializer(payment).data
        if request.path.startswith("/api/v1/"):
            return api_ok(data=data)
        return Response(data, status=status.HTTP_200_OK)


class RefundCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = RefundCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        payment = get_object_or_404(Payment, pk=serializer.validated_data["payment_id"])
        key = (
            (request.headers.get("Idempotency-Key") or "").strip()
            or (serializer.validated_data.get("idempotency_key") or "").strip()
        )
        existed_before = bool(key and Refund.objects.filter(idempotency_key=key).exists())

        try:
            refund = create_refund(
                request=request,
                payment=payment,
                amount=serializer.validated_data["amount"],
                method=serializer.validated_data["method"],
                notes=serializer.validated_data.get("notes", ""),
                idempotency_key=key,
            )
        except ValueError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            "message": "Refund request replayed (idempotent)." if existed_before else "Refund created successfully.",
            "refund": RefundDetailSerializer(refund).data,
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(
                message=payload["message"],
                data={"refund": payload["refund"]},
                http_status=status.HTTP_200_OK if existed_before else status.HTTP_201_CREATED,
            )
        return Response(payload, status=status.HTTP_200_OK if existed_before else status.HTTP_201_CREATED)


def _hyperpay_configured() -> bool:
    return bool(
        settings.HYPERPAY_BASE_URL
        and settings.HYPERPAY_ENTITY_ID
        and settings.HYPERPAY_ACCESS_TOKEN
    )


def _hyperpay_request(method: str, path: str, data: dict | None = None) -> dict:
    url = f"{settings.HYPERPAY_BASE_URL.rstrip('/')}{path}"
    headers = {
        "Authorization": f"Bearer {settings.HYPERPAY_ACCESS_TOKEN}",
    }

    if data is not None:
        body = urllib.parse.urlencode(data).encode("utf-8")
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    else:
        body = None

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


class HyperPayCheckoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not _hyperpay_configured():
            return Response({"error": "HyperPay not configured."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        booking_id = request.data.get("booking_id")
        amount = request.data.get("amount")
        currency = request.data.get("currency")
        payment_brand = request.data.get("payment_brand")

        if not booking_id or not amount or not currency or not payment_brand:
            return Response(
                {"error": "booking_id, amount, currency, payment_brand required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        payment_brand = str(payment_brand).upper()
        if payment_brand not in {"VISA", "MASTER"}:
            return Response(
                {"error": "Unsupported payment brand."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        booking = get_object_or_404(Booking, pk=int(booking_id))

        try:
            payload = {
                "entityId": settings.HYPERPAY_ENTITY_ID,
                "amount": str(amount),
                "currency": str(currency),
                "paymentBrand": payment_brand,
                "paymentType": "DB",
                "merchantTransactionId": f"booking-{booking.id}",
            }
            response = _hyperpay_request("POST", "/v1/checkouts", payload)
        except Exception as exc:
            return Response(
                {"error": str(exc) or "HyperPay checkout failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        checkout_id = response.get("id") or response.get("checkoutId")
        if not checkout_id:
            return Response(
                {"error": "Invalid HyperPay response.", "response": response},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = {"checkout_id": checkout_id, "booking_id": booking.id}
        if request.path.startswith("/api/v1/"):
            return api_ok(data=payload, http_status=status.HTTP_201_CREATED)
        return Response(payload, status=status.HTTP_201_CREATED)


class HyperPayStatusAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not _hyperpay_configured():
            return Response(
                {"error": "HyperPay not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        checkout_id = request.query_params.get("checkout_id")
        if not checkout_id:
            return Response(
                {"error": "checkout_id required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            query = urllib.parse.urlencode({"entityId": settings.HYPERPAY_ENTITY_ID})
            response = _hyperpay_request(
                "GET",
                f"/v1/checkouts/{checkout_id}/payment?{query}",
            )
        except Exception as exc:
            return Response(
                {"error": str(exc) or "HyperPay status check failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        payload = {"result": response}
        if request.path.startswith("/api/v1/"):
            return api_ok(data=payload)
        return Response(payload, status=status.HTTP_200_OK)
