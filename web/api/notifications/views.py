from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from apps.core.models import Notification
from api.responses import api_ok, paginated_list_response
from .serializers import NotificationSerializer


class NotificationListAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        notifications = Notification.objects.filter(user=request.user).order_by("-created_at", "-id")
        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, notifications, NotificationSerializer)

        serializer = NotificationSerializer(notifications, many=True)

        return Response(serializer.data)


class NotificationMarkReadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):

        try:
            notification = Notification.objects.get(
                id=pk,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.is_read = True
        notification.save()

        if request.path.startswith("/api/v1/"):
            return api_ok(message="Notification marked as read")
        return Response({"message": "Notification marked as read"})


class NotificationDeleteAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):

        try:
            notification = Notification.objects.get(
                id=pk,
                user=request.user
            )
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        notification.delete()

        if request.path.startswith("/api/v1/"):
            return api_ok(message="Notification deleted")
        return Response({"message": "Notification deleted"})
