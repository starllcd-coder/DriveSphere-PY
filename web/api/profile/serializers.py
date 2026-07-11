from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
        ]

    def get_full_name(self, obj):

        name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()

        if name:
            return name

        return obj.email


class ProfileUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
        ]