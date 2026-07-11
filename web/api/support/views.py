from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.models import SupportMessage
from api.responses import api_ok, paginated_list_response
from .serializers import SupportMessageSerializer


class SupportMessageListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        messages = SupportMessage.objects.filter(user=request.user).order_by("created_at")
        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, messages, SupportMessageSerializer)
        serializer = SupportMessageSerializer(messages, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SupportMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        SupportMessage.objects.create(
            user=request.user,
            sender="customer",
            message=serializer.validated_data["message"],
        )
        if request.path.startswith("/api/v1/"):
            return api_ok(message="Message sent.", http_status=status.HTTP_201_CREATED)
        return Response({"message": "Message sent."}, status=status.HTTP_201_CREATED)
