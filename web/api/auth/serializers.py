from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from apps.accounts.permissions import ROLE_PERMISSIONS

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    identifier = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs.get("identifier", "").strip()
        password = attrs.get("password", "")

        if not identifier or not password:
            raise serializers.ValidationError("Username/email and password are required.")

        user = None

        if "@" in identifier:
            try:
                matched_user = User.objects.get(email__iexact=identifier)
                user = authenticate(
                    request=self.context.get("request"),
                    username=matched_user.username,
                    password=password,
                )
            except User.DoesNotExist:
                user = None
        else:
            user = authenticate(
                request=self.context.get("request"),
                username=identifier,
                password=password,
            )

        if user is None:
            raise serializers.ValidationError("Invalid username/email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        attrs["user"] = user
        return attrs


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=False, allow_blank=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    nationality = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = [
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "nationality",
            "password",
            "confirm_password",
        ]

    def validate_email(self, value):
        value = value.strip().lower()
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        full_name = (validated_data.pop("full_name", "") or "").strip()
        phone = (validated_data.pop("phone", "") or "").strip()
        nationality = (validated_data.pop("nationality", "") or "").strip()
        email = validated_data.get("email", "").strip().lower()

        if full_name and (not validated_data.get("first_name") or not validated_data.get("last_name")):
            parts = full_name.split()
            validated_data["first_name"] = parts[0]
            validated_data["last_name"] = " ".join(parts[1:]) if len(parts) > 1 else ""

        username = email if email else f"user_{User.objects.count() + 1}"

        user = User(
            username=username,
            email=email,
            first_name=validated_data.get("first_name", "").strip(),
            last_name=validated_data.get("last_name", "").strip(),
            phone_number=phone,
            nationality=nationality,
            is_active=True,
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    default_branch = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "is_staff",
            "role",
            "permissions",
            "default_branch",
        ]

    def get_full_name(self, obj):
        full_name = f"{obj.first_name or ''} {obj.last_name or ''}".strip()
        return full_name or obj.username or obj.email

    def get_role(self, obj):
        role = getattr(obj, "role", None)
        if not role:
            return None
        return {
            "code": role.code,
            "name": role.name,
        }

    def get_permissions(self, obj):
        if getattr(obj, "is_superuser", False):
            all_perms = set()
            for perm_list in ROLE_PERMISSIONS.values():
                all_perms.update(perm_list)
            return sorted(all_perms)

        role = getattr(obj, "role", None)
        if not role:
            return []
        return sorted(ROLE_PERMISSIONS.get(role.code, []))

    def get_default_branch(self, obj):
        branch = getattr(obj, "default_branch", None)
        if not branch:
            return None
        return {
            "id": branch.id,
            "name": branch.name,
            "code": branch.code,
        }
