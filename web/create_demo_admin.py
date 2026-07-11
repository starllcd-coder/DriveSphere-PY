from django.contrib.auth import get_user_model

User = get_user_model()

email = "demo@drivesphere.app"
password = "Demo@12345"

user, created = User.objects.get_or_create(
    email=email,
    defaults={
        "username": "demo",
        "is_staff": True,
        "is_superuser": True,
        "is_active": True,
    }
)

user.username = "demo"
user.is_staff = True
user.is_superuser = True
user.is_active = True
user.set_password(password)
user.save()

print("Demo admin ready:", email, password)
