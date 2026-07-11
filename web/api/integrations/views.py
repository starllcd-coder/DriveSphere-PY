from django.shortcuts import get_object_or_404
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from api.responses import api_ok
from apps.accounts.permissions import has_perm
from apps.core.services import get_active_branch
from apps.settings_app.integration_services import run_accounting_sync, run_telematics_pull
from apps.settings_app.models import Branch, IntegrationProfile, IntegrationSyncLog

from .serializers import (
    IntegrationProfileSerializer,
    IntegrationProfileUpsertSerializer,
    IntegrationSyncLogSerializer,
    IntegrationSyncRunSerializer,
)


class IntegrationProfileListCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not has_perm(request.user, "settings.manage"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        qs = IntegrationProfile.objects.select_related("branch").order_by("integration_type")
        data = IntegrationProfileSerializer(qs, many=True).data
        if request.path.startswith("/api/v1/"):
            return api_ok(data={"profiles": data})
        return Response({"profiles": data})

    def post(self, request):
        if not has_perm(request.user, "settings.manage"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        serializer = IntegrationProfileUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        profile, _ = IntegrationProfile.objects.get_or_create(integration_type=data["integration_type"])
        if "branch_id" in data:
            profile.branch = Branch.objects.filter(id=data.get("branch_id")).first()
        profile.base_url = data.get("base_url", profile.base_url)
        profile.client_id = data.get("client_id", profile.client_id)
        profile.org_id = data.get("org_id", profile.org_id)
        profile.metadata = data.get("metadata", profile.metadata)
        if "is_active" in data:
            profile.is_active = data["is_active"]
        if "client_secret" in data and data.get("client_secret") is not None:
            profile.set_client_secret(data.get("client_secret", ""))
        if "access_token" in data and data.get("access_token") is not None:
            profile.set_access_token(data.get("access_token", ""))
        if "refresh_token" in data and data.get("refresh_token") is not None:
            profile.set_refresh_token(data.get("refresh_token", ""))
        profile.save()

        payload = IntegrationProfileSerializer(profile).data
        if request.path.startswith("/api/v1/"):
            return api_ok(message="Integration profile saved.", data={"profile": payload}, http_status=status.HTTP_201_CREATED)
        return Response({"profile": payload}, status=status.HTTP_201_CREATED)


class IntegrationSyncRunAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not has_perm(request.user, "settings.manage"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        serializer = IntegrationSyncRunSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        profile = get_object_or_404(IntegrationProfile, integration_type=data["integration_type"])

        branch = get_active_branch(request)
        if "ACCOUNTING" in profile.integration_type:
            result = run_accounting_sync(profile=profile, branch=branch, period=data["period"])
        else:
            result = run_telematics_pull(profile=profile, since_hours=data.get("since_hours", 6))

        if request.path.startswith("/api/v1/"):
            return api_ok(data=result)
        return Response(result)


class IntegrationSyncLogListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not has_perm(request.user, "settings.manage"):
            return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
        integration_type = (request.query_params.get("integration_type") or "").strip().upper()
        qs = IntegrationSyncLog.objects.select_related("profile").order_by("-created_at")
        if integration_type:
            qs = qs.filter(profile__integration_type=integration_type)
        data = IntegrationSyncLogSerializer(qs[:200], many=True).data
        if request.path.startswith("/api/v1/"):
            return api_ok(data={"logs": data})
        return Response({"logs": data})
