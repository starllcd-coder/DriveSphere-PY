from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.models import DeviceToken
from api.responses import api_ok
from .serializers import DeviceTokenSerializer


class DeviceTokenRegisterAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeviceTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        platform = serializer.validated_data["platform"]

        DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user,
                "platform": platform,
            },
        )

        if request.path.startswith("/api/v1/"):
            return api_ok(message="Device registered.")
        return Response({"message": "Device registered."}, status=status.HTTP_200_OK)
