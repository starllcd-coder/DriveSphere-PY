from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from twilio.rest import Client

from apps.accounts.permissions import has_perm
from apps.bookings.models import Booking
from apps.bookings.services import BookingError

from api.responses import api_ok, paginated_list_response

from .serializers import (
    BookingCreateSerializer,
    BookingDetailSerializer,
    BookingListSerializer,
)


class BookingCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        if not has_perm(request.user, "bookings.create"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookingCreateSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        try:
            booking = serializer.save()
        except BookingError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        whatsapp_sent = _send_whatsapp_booking_confirmation(booking)

        payload = {
            "message": "Booking created successfully.",
            "booking": BookingDetailSerializer(booking).data,
            "whatsapp_sent": whatsapp_sent,
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(message=payload["message"], data={"booking": payload["booking"], "whatsapp_sent": whatsapp_sent}, http_status=status.HTTP_201_CREATED)
        return Response(payload, status=status.HTTP_201_CREATED)


class BookingListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        customer_id = request.query_params.get("customer_id")
        status_filter = request.query_params.get("status")
        ordering = (request.query_params.get("ordering") or "-pickup_date").strip()

        allowed_ordering = {
            "pickup_date",
            "-pickup_date",
            "return_date",
            "-return_date",
            "created_at",
            "-created_at",
            "id",
            "-id",
        }
        if ordering not in allowed_ordering:
            ordering = "-pickup_date"

        queryset = (
            Booking.objects.select_related(
                "branch",
                "customer",
                "vehicle",
                "vehicle__brand",
                "vehicle__model",
                "created_by",
            )
            .all()
            .order_by(ordering, "-id")
        )

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        if status_filter:
            queryset = queryset.filter(status=status_filter)

        query = (request.query_params.get("q") or "").strip()
        if query:
            queryset = queryset.filter(
                Q(customer__name__icontains=query)
                | Q(vehicle__plate_number__icontains=query)
                | Q(reference__icontains=query)
            )

        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, queryset, BookingListSerializer)
        serializer = BookingListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class BookingDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        booking = get_object_or_404(
            Booking.objects.select_related(
                "branch",
                "customer",
                "vehicle",
                "vehicle__brand",
                "vehicle__model",
                "created_by",
            ),
            pk=pk,
        )

        data = BookingDetailSerializer(booking).data
        if request.path.startswith("/api/v1/"):
            return api_ok(data=data)
        return Response(data, status=status.HTTP_200_OK)


def _send_whatsapp_booking_confirmation(booking: Booking) -> bool:
    phone = (getattr(booking.customer, "phone_number", "") or "").strip()
    if not phone:
        return False

    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
        return False
    if not settings.TWILIO_WHATSAPP_FROM:
        return False

    to_number = phone if phone.startswith("+") else f"+{phone}"
    reference = booking.reference or f"DS-{booking.id}"
    message = (
        "DriveSphere booking confirmed. "
        f"Reference: {reference}. "
        f"Pickup: {booking.pickup_date} Return: {booking.return_date}."
    )

    try:
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{to_number}",
            body=message,
        )
        return True
    except Exception:
        return False
