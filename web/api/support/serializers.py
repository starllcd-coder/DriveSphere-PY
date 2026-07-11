from rest_framework import serializers

from apps.core.models import SupportMessage


class SupportMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportMessage
        fields = [
            "id",
            "message",
            "sender",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]
