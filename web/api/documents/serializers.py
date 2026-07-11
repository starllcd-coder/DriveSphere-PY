from rest_framework import serializers

from apps.customers.models import Customer, CustomerDocument


class CustomerDocumentListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomerDocument
        fields = [
            "id",
            "customer",
            "customer_name",
            "doc_type",
            "status",
            "file",
            "file_url",
            "expiry_date",
            "notes",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return ""
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url


class CustomerDocumentUploadSerializer(serializers.ModelSerializer):
    customer_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CustomerDocument
        fields = [
            "customer_id",
            "doc_type",
            "file",
            "expiry_date",
            "notes",
        ]

    def validate_customer_id(self, value):
        try:
            customer = Customer.objects.get(pk=value, is_active=True)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Active customer not found.")
        return value

    def validate_file(self, value):
        if not value:
            raise serializers.ValidationError("File is required.")
        return value

    def create(self, validated_data):
        customer_id = validated_data.pop("customer_id")
        customer = Customer.objects.get(pk=customer_id, is_active=True)

        document = CustomerDocument.objects.create(
            customer=customer,
            **validated_data,
        )
        return document


class CustomerDocumentDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = CustomerDocument
        fields = [
            "id",
            "customer",
            "customer_name",
            "doc_type",
            "status",
            "file",
            "file_url",
            "expiry_date",
            "notes",
            "created_at",
            "updated_at",
        ]

    def get_file_url(self, obj):
        request = self.context.get("request")
        if not obj.file:
            return ""
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url