from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from api.responses import api_ok
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
)


class ProfileAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = ProfileSerializer(request.user)
        if request.path.startswith("/api/v1/"):
            return api_ok(data=serializer.data)
        return Response(serializer.data)


class ProfileUpdateAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request):

        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            payload = {
                "message": "Profile updated successfully",
                "user": ProfileSerializer(request.user).data
            }
            if request.path.startswith("/api/v1/"):
                return api_ok(message=payload["message"], data={"user": payload["user"]})
            return Response(payload)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
