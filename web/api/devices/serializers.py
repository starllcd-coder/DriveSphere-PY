from rest_framework import serializers

from apps.core.models import DeviceToken


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = [
            "token",
            "platform",
        ]

    def validate_platform(self, value):
        value_lower = value.lower()
        if value_lower not in {"ios", "android"}:
            raise serializers.ValidationError("Platform must be ios or android.")
        return value_lower
