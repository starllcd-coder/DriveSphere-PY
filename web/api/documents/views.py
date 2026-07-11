from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.customers.models import CustomerDocument
from api.responses import api_ok, paginated_list_response

from .serializers import (
    CustomerDocumentDetailSerializer,
    CustomerDocumentListSerializer,
    CustomerDocumentUploadSerializer,
)


class CustomerDocumentUploadAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        serializer = CustomerDocumentUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        payload = {
            "message": "Document uploaded successfully.",
            "document": CustomerDocumentDetailSerializer(
                document,
                context={"request": request},
            ).data,
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(message=payload["message"], data={"document": payload["document"]}, http_status=status.HTTP_201_CREATED)
        return Response(payload, status=status.HTTP_201_CREATED)


class CustomerDocumentListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        customer_id = request.query_params.get("customer_id")

        queryset = CustomerDocument.objects.select_related("customer").all().order_by("-created_at")

        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)

        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, queryset, CustomerDocumentListSerializer)

        serializer = CustomerDocumentListSerializer(
            queryset,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CustomerDocumentDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        try:
            return CustomerDocument.objects.select_related("customer").get(pk=pk)
        except CustomerDocument.DoesNotExist:
            return None

    def get(self, request, pk, *args, **kwargs):
        document = self.get_object(pk)
        if document is None:
            return Response(
                {"detail": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerDocumentDetailSerializer(
            document,
            context={"request": request},
        )
        if request.path.startswith("/api/v1/"):
            return api_ok(data=serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk, *args, **kwargs):
        document = self.get_object(pk)
        if document is None:
            return Response(
                {"detail": "Document not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        document.delete()
        if request.path.startswith("/api/v1/"):
            return api_ok(message="Document deleted successfully.")
        return Response(
            {"message": "Document deleted successfully."},
            status=status.HTTP_200_OK,
        )
