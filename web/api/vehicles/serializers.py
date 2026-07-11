from django.db.models import Avg
from rest_framework import serializers
from apps.fleet.models import Vehicle, TelematicsPing
from apps.settings_app.models import BusinessProfile


class VehicleListSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    daily_rate = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()
    company_verified = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "brand_name",
            "model_name",
            "year",
            "daily_rate",
            "deposit_amount",
            "status",
            "image_url",
            "rating",
            "review_count",
            "company_name",
            "pickup_location",
            "city",
            "company_verified",
            "whatsapp_number",
        ]

    def get_brand_name(self, obj):
        brand = getattr(obj, "brand", None)
        return getattr(brand, "name", "")

    def get_model_name(self, obj):
        model = getattr(obj, "model", None)
        return getattr(model, "name", "")

    def get_daily_rate(self, obj):
        return getattr(obj, "daily_rate", None)

    def get_deposit_amount(self, obj):
        return getattr(obj, "deposit", None)

    def get_status(self, obj):
        return getattr(obj, "status", "")

    def get_image_url(self, obj):
        request = self.context.get("request")

        possible_fields = [
            "image",
            "photo",
            "thumbnail",
            "main_image",
        ]

        for field_name in possible_fields:
            file_obj = getattr(obj, field_name, None)
            if file_obj:
                try:
                    url = file_obj.url
                    if request is not None:
                        return request.build_absolute_uri(url)
                    return url
                except Exception:
                    continue

        return ""

    def get_company_name(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_pickup_location(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_city(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_company_verified(self, obj):
        branch = getattr(obj, "branch", None)
        return bool(getattr(branch, "is_verified", False))

    def get_whatsapp_number(self, obj):
        business = BusinessProfile.get_solo()
        return (business.phone_number or "").strip()

    def get_rating(self, obj):
        return obj.reviews.aggregate(avg=Avg("rating")).get("avg") or 0

    def get_review_count(self, obj):
        return obj.reviews.count()


class VehicleDetailSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()
    company_verified = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = "__all__"

    def get_brand_name(self, obj):
        brand = getattr(obj, "brand", None)
        return getattr(brand, "name", "")

    def get_model_name(self, obj):
        model = getattr(obj, "model", None)
        return getattr(model, "name", "")

    def get_company_name(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_pickup_location(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_city(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_deposit_amount(self, obj):
        return getattr(obj, "deposit", None)

    def get_company_verified(self, obj):
        branch = getattr(obj, "branch", None)
        return bool(getattr(branch, "is_verified", False))

    def get_whatsapp_number(self, obj):
        business = BusinessProfile.get_solo()
        return (business.phone_number or "").strip()

    def get_image_url(self, obj):
        request = self.context.get("request")

        possible_fields = [
            "image",
            "photo",
            "thumbnail",
            "main_image",
        ]

        for field_name in possible_fields:
            file_obj = getattr(obj, field_name, None)
            if file_obj:
                try:
                    url = file_obj.url
                    if request is not None:
                        return request.build_absolute_uri(url)
                    return url
                except Exception:
                    continue

        return ""

    def get_images(self, obj):
        request = self.context.get("request")
        images = []
        for photo in obj.photos.all():
            try:
                url = photo.image.url
                if request is not None:
                    url = request.build_absolute_uri(url)
                images.append(url)
            except Exception:
                continue
        return images

    def get_rating(self, obj):
        return obj.reviews.aggregate(avg=Avg("rating")).get("avg") or 0

    def get_review_count(self, obj):
        return obj.reviews.count()


class VehicleSearchSerializer(serializers.ModelSerializer):
    brand_name = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    daily_rate = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    city = serializers.SerializerMethodField()
    deposit_amount = serializers.SerializerMethodField()
    company_verified = serializers.SerializerMethodField()
    whatsapp_number = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "brand_name",
            "model_name",
            "year",
            "daily_rate",
            "deposit_amount",
            "status",
            "image_url",
            "rating",
            "review_count",
            "company_name",
            "pickup_location",
            "city",
            "company_verified",
            "whatsapp_number",
        ]

    def get_brand_name(self, obj):
        brand = getattr(obj, "brand", None)
        return getattr(brand, "name", "")

    def get_model_name(self, obj):
        model = getattr(obj, "model", None)
        return getattr(model, "name", "")

    def get_daily_rate(self, obj):
        return getattr(obj, "daily_rate", None)

    def get_deposit_amount(self, obj):
        return getattr(obj, "deposit", None)

    def get_status(self, obj):
        return getattr(obj, "status", "")

    def get_image_url(self, obj):
        request = self.context.get("request")

        possible_fields = [
            "image",
            "photo",
            "thumbnail",
            "main_image",
        ]

        for field_name in possible_fields:
            file_obj = getattr(obj, field_name, None)
            if file_obj:
                try:
                    url = file_obj.url
                    if request is not None:
                        return request.build_absolute_uri(url)
                    return url
                except Exception:
                    continue

        return ""

    def get_company_name(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_pickup_location(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_city(self, obj):
        branch = getattr(obj, "branch", None)
        return getattr(branch, "name", "")

    def get_company_verified(self, obj):
        branch = getattr(obj, "branch", None)
        return bool(getattr(branch, "is_verified", False))

    def get_whatsapp_number(self, obj):
        business = BusinessProfile.get_solo()
        return (business.phone_number or "").strip()

    def get_rating(self, obj):
        return obj.reviews.aggregate(avg=Avg("rating")).get("avg") or 0

    def get_review_count(self, obj):
        return obj.reviews.count()


class TelematicsPingSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelematicsPing
        fields = [
            "id",
            "vehicle",
            "provider",
            "external_vehicle_id",
            "recorded_at",
            "latitude",
            "longitude",
            "speed_kmh",
            "odometer_km",
            "fuel_percent",
            "fuel_used_liters",
            "idle_seconds",
            "engine_on",
            "engine_status",
            "battery_voltage",
            "fault_codes",
            "metadata",
        ]
