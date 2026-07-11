from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create or update demo admin user"

    def handle(self, *args, **options):
        User = get_user_model()

        email = "demo@drivesphere.app"
        password = "Demo@12345"

        user = User.objects.filter(email=email).first()

        if not user:
            user = User(email=email)

        if hasattr(user, "username"):
            user.username = "demo"

        if hasattr(user, "first_name"):
            user.first_name = "Demo"

        if hasattr(user, "last_name"):
            user.last_name = "Admin"

        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS(f"Demo admin ready: {email} / {password}"))
