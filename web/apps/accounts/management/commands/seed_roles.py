from django.core.management.base import BaseCommand

from apps.accounts.models import Role
from apps.accounts import permissions as permissions_module


class Command(BaseCommand):
    help = "Create standard Role rows used by the application."

    def handle(self, *args, **options):
        created = []
        for code, label in Role.ROLE_CHOICES:
            role, created_flag = Role.objects.get_or_create(code=code, defaults={"name": label})
            if not created_flag and role.name != label:
                role.name = label
                role.save()
            created.append((code, role.pk))

        self.stdout.write(self.style.SUCCESS(f"Ensured {len(created)} roles exist."))
        for code, pk in created:
            self.stdout.write(f" - {code}: id={pk}")

        # Print role -> permissions mapping from code for operator visibility
        self.stdout.write("")
        self.stdout.write("Role -> permissions mapping (from apps.accounts.permissions):")
        for role_code, perms in permissions_module.ROLE_PERMISSIONS.items():
            self.stdout.write(f" - {role_code}: {', '.join(perms)}")
