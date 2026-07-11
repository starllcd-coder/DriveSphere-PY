from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from apps.fleet.models import Vehicle, VehicleReview
from api.responses import api_ok, paginated_list_response
from .review_serializers import VehicleReviewSerializer


class VehicleReviewListCreateAPIView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, pk):
        reviews = VehicleReview.objects.filter(vehicle_id=pk).order_by("-created_at")
        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, reviews, VehicleReviewSerializer)
        serializer = VehicleReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = VehicleReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        VehicleReview.objects.create(
            vehicle=vehicle,
            rating=serializer.validated_data["rating"],
            comment=serializer.validated_data.get("comment", ""),
        )
        if request.path.startswith("/api/v1/"):
            return api_ok(message="Review submitted.", http_status=status.HTTP_201_CREATED)
        return Response({"message": "Review submitted."}, status=status.HTTP_201_CREATED)
