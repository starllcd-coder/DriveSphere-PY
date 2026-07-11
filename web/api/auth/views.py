import random

from django.conf import settings
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from twilio.rest import Client
from api.responses import api_ok, api_error

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    UserProfileSerializer,
)


class LoginAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth_login"

    @staticmethod
    def _client_ip(request) -> str:
        forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")

    def _login_limit_key(self, request, identifier: str) -> str:
        return f"api:login:limit:{self._client_ip(request)}:{identifier.lower()}"

    def _login_block_key(self, request, identifier: str) -> str:
        return f"api:login:block:{self._client_ip(request)}:{identifier.lower()}"

    def _is_temporarily_blocked(self, request, identifier: str) -> bool:
        return bool(cache.get(self._login_block_key(request, identifier)))

    def _register_failed_attempt(self, request, identifier: str) -> None:
        limit_key = self._login_limit_key(request, identifier)
        block_key = self._login_block_key(request, identifier)
        current = int(cache.get(limit_key) or 0) + 1
        cache.set(limit_key, current, timeout=settings.LOGIN_ATTEMPT_WINDOW_SECONDS)
        if current >= settings.LOGIN_ATTEMPT_LIMIT:
            cache.set(block_key, 1, timeout=settings.LOGIN_BLOCK_SECONDS)

    def _clear_failed_attempts(self, request, identifier: str) -> None:
        cache.delete(self._login_limit_key(request, identifier))
        cache.delete(self._login_block_key(request, identifier))

    def post(self, request, *args, **kwargs):
        is_v1 = request.path.startswith("/api/v1/")
        identifier = (request.data.get("identifier") or request.data.get("email") or "").strip()
        if identifier and self._is_temporarily_blocked(request, identifier):
            if is_v1:
                return api_error("Too many failed login attempts. Try again later.", http_status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({"error": "Too many failed login attempts. Try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )
        if not serializer.is_valid():
            if identifier:
                self._register_failed_attempt(request, identifier)
            if is_v1:
                return api_error("Invalid login request.", details=serializer.errors, http_status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.validated_data["user"]
        if identifier:
            self._clear_failed_attempts(request, identifier)
        refresh = RefreshToken.for_user(user)

        payload = {
            "message": "Login successful.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserProfileSerializer(user).data,
        }
        if is_v1:
            return api_ok(message=payload["message"], data={"tokens": payload["tokens"], "user": payload["user"]})
        return Response(payload, status=status.HTTP_200_OK)


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        is_v1 = request.path.startswith("/api/v1/")
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        payload = {
            "message": "Registration successful.",
            "tokens": {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            "user": UserProfileSerializer(user).data,
        }
        if is_v1:
            return api_ok(
                message=payload["message"],
                data={"tokens": payload["tokens"], "user": payload["user"]},
                http_status=status.HTTP_201_CREATED,
            )
        return Response(payload, status=status.HTTP_201_CREATED)


class ProfileAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        is_v1 = request.path.startswith("/api/v1/")
        serializer = UserProfileSerializer(request.user)
        if is_v1:
            return api_ok(data=serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class OTPRequestAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def _rate_limit_key(self, phone: str) -> str:
        return f"otp:limit:{phone}"

    def _otp_key(self, phone: str) -> str:
        return f"otp:{phone}"

    def _increment_rate_limit(self, phone: str) -> bool:
        key = self._rate_limit_key(phone)
        current = cache.get(key)
        if current is None:
            cache.set(key, 1, timeout=settings.OTP_RATE_LIMIT_WINDOW_SECONDS)
            return True

        if int(current) >= settings.OTP_RATE_LIMIT_MAX:
            return False

        cache.set(key, int(current) + 1, timeout=settings.OTP_RATE_LIMIT_WINDOW_SECONDS)
        return True

    def _is_voip_number(self, client: Client, phone: str) -> bool:
        if not settings.OTP_BLOCK_VOIP:
            return False
        try:
            lookup = client.lookups.v2.phone_numbers(phone).fetch(
                fields="line_type_intelligence"
            )
            info = getattr(lookup, "line_type_intelligence", None) or {}
            line_type = (info.get("type") or "").lower()
            return line_type == "voip"
        except Exception:
            return False

    def post(self, request, *args, **kwargs):
        is_v1 = request.path.startswith("/api/v1/")
        phone = (request.data.get("phone") or "").strip()
        if not phone:
            if is_v1:
                return api_error("Phone is required.", http_status=status.HTTP_400_BAD_REQUEST)
            return Response({"success": False, "error": "Phone is required."}, status=status.HTTP_400_BAD_REQUEST)

        if not self._increment_rate_limit(phone):
            if is_v1:
                return api_error("Too many OTP requests. Please try again later.", http_status=status.HTTP_429_TOO_MANY_REQUESTS)
            return Response({"success": False, "error": "Too many OTP requests. Please try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

        otp = f"{random.randint(100000, 999999)}"
        cache_key = self._otp_key(phone)
        cache.set(cache_key, otp, timeout=settings.OTP_TTL_SECONDS)

        if not (settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN):
            payload = {
                "success": True,
                "channel": "debug",
                "otp": otp if settings.OTP_DEBUG_RETURN_CODE else "",
            }
            if is_v1:
                return api_ok(data={"channel": payload["channel"], "otp": payload["otp"]})
            return Response(payload, status=status.HTTP_200_OK)

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        if self._is_voip_number(client, phone):
            if is_v1:
                return api_error("VOIP numbers are not supported.", http_status=status.HTTP_400_BAD_REQUEST)
            return Response({"success": False, "error": "VOIP numbers are not supported."}, status=status.HTTP_400_BAD_REQUEST)

        ttl_seconds = settings.OTP_TTL_SECONDS
        ttl_text = (
            f"{ttl_seconds} seconds" if ttl_seconds < 60 else f"{ttl_seconds // 60} minutes"
        )
        message_body = f"Your DriveSphere OTP is {otp}. It expires in {ttl_text}."

        whatsapp_sent = False
        sms_sent = False

        try:
            if settings.TWILIO_WHATSAPP_FROM:
                client.messages.create(
                    from_=settings.TWILIO_WHATSAPP_FROM,
                    to=f"whatsapp:{phone}",
                    body=message_body,
                )
                whatsapp_sent = True
        except Exception:
            whatsapp_sent = False

        if not whatsapp_sent:
            try:
                if settings.TWILIO_SMS_FROM:
                    client.messages.create(
                        from_=settings.TWILIO_SMS_FROM,
                        to=phone,
                        body=message_body,
                    )
                    sms_sent = True
            except Exception:
                sms_sent = False

        if not whatsapp_sent and not sms_sent:
            if is_v1:
                return api_error("OTP delivery failed.", http_status=status.HTTP_502_BAD_GATEWAY)
            return Response({"success": False, "error": "OTP delivery failed."}, status=status.HTTP_502_BAD_GATEWAY)

        payload = {
            "success": True,
            "channel": "whatsapp" if whatsapp_sent else "sms",
            "otp": otp if settings.OTP_DEBUG_RETURN_CODE else "",
        }
        if is_v1:
            return api_ok(data={"channel": payload["channel"], "otp": payload["otp"]})
        return Response(payload, status=status.HTTP_200_OK)


class OTPVerifyAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request, *args, **kwargs):
        is_v1 = request.path.startswith("/api/v1/")
        phone = (request.data.get("phone") or "").strip()
        otp = (request.data.get("otp") or "").strip()
        if not phone or not otp:
            if is_v1:
                return api_error("Phone and OTP are required.", http_status=status.HTTP_400_BAD_REQUEST)
            return Response({"success": False, "error": "Phone and OTP are required."}, status=status.HTTP_400_BAD_REQUEST)

        cache_key = f"otp:{phone}"
        cached = cache.get(cache_key)
        if cached and cached == otp:
            cache.delete(cache_key)
            if is_v1:
                return api_ok(data={"verified": True})
            return Response({"success": True}, status=status.HTTP_200_OK)

        if is_v1:
            return api_error("Invalid OTP.", http_status=status.HTTP_200_OK, verified=False)
        return Response({"success": False}, status=status.HTTP_200_OK)
