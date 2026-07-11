from rest_framework import serializers

from apps.fleet.models import VehicleReview


class VehicleReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleReview
        fields = [
            "id",
            "vehicle",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "vehicle", "created_at"]

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
