from rest_framework import serializers

from apps.settings_app.models import IntegrationProfile, IntegrationSyncLog


class IntegrationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntegrationProfile
        fields = [
            "id",
            "branch",
            "integration_type",
            "base_url",
            "client_id",
            "org_id",
            "metadata",
            "is_active",
            "created_at",
            "updated_at",
        ]


class IntegrationProfileUpsertSerializer(serializers.Serializer):
    integration_type = serializers.ChoiceField(choices=IntegrationProfile.INTEGRATION_CHOICES)
    branch_id = serializers.IntegerField(required=False, allow_null=True)
    base_url = serializers.CharField(required=False, allow_blank=True)
    client_id = serializers.CharField(required=False, allow_blank=True)
    client_secret = serializers.CharField(required=False, allow_blank=True)
    access_token = serializers.CharField(required=False, allow_blank=True)
    refresh_token = serializers.CharField(required=False, allow_blank=True)
    org_id = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)
    is_active = serializers.BooleanField(required=False)


class IntegrationSyncLogSerializer(serializers.ModelSerializer):
    profile_type = serializers.CharField(source="profile.integration_type", read_only=True)

    class Meta:
        model = IntegrationSyncLog
        fields = [
            "id",
            "profile",
            "profile_type",
            "direction",
            "status",
            "summary",
            "details",
            "created_at",
        ]


class IntegrationSyncRunSerializer(serializers.Serializer):
    integration_type = serializers.ChoiceField(choices=IntegrationProfile.INTEGRATION_CHOICES)
    period = serializers.ChoiceField(choices=[("today", "today"), ("weekly", "weekly"), ("monthly", "monthly")], default="monthly")
    since_hours = serializers.IntegerField(required=False, min_value=1, max_value=168, default=6)
