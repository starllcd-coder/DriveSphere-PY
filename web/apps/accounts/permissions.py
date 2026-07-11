def has_role(user, role_code: str) -> bool:
    return bool(user.is_authenticated and user.role and user.role.code == role_code)


def is_admin(user) -> bool:
    return bool(user.is_authenticated and (user.is_superuser or (user.role and user.role.code == "ADMIN")))


# Role -> permission mapping (simple matrix). Update as needed.
ROLE_PERMISSIONS = {
    "ADMIN": [
        "bookings.view", "bookings.create", "bookings.update", "bookings.delete",
        "bookings.extend", "bookings.checkout", "bookings.return", "bookings.damage_photos",
        "customers.view", "customers.manage",
        "fleet.view", "fleet.manage",
        "maintenance.view", "maintenance.create", "maintenance.update", "maintenance.delete",
        "payments.view", "payments.create", "payments.manage", "payments.refund",
        "reports.view", "reports.view_financial", "reports.view_maintenance", "reports.view_limited",
        "settings.manage", "employees.manage",
    ],
    "MANAGER": [
        "bookings.view", "bookings.create", "bookings.update", "bookings.delete",
        "bookings.extend", "bookings.checkout", "bookings.return", "bookings.damage_photos",
        "customers.view", "customers.manage",
        "fleet.view", "fleet.manage",
        "maintenance.view", "maintenance.create", "maintenance.update", "maintenance.delete",
        "payments.view", "payments.create", "payments.manage", "payments.refund",
        "reports.view",
    ],
    "AGENT": [
        "bookings.view", "bookings.create", "bookings.update",
        "bookings.extend", "bookings.checkout", "bookings.return", "bookings.damage_photos",
        "customers.view", "customers.manage",
        "payments.view", "payments.create",
        "reports.view_limited",
    ],
    "MECHANIC": [
        "maintenance.view", "maintenance.update",
        "fleet.view",
        "reports.view_maintenance",
    ],
    "ACCOUNTANT": [
        "payments.view", "payments.create", "payments.manage", "payments.refund",
        "reports.view_financial",
    ],
    "VIEWER": [
        "bookings.view",
        "customers.view",
        "fleet.view",
        "maintenance.view",
        "payments.view",
        "reports.view_limited",
    ],
}


def has_perm(user, perm_code: str) -> bool:
    """Check whether the user has a permission string.

    Superusers always have all permissions. Role-based checks are done
    against the ROLE_PERMISSIONS mapping above.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    role = getattr(user, "role", None)
    if not role:
        return False
    perms = ROLE_PERMISSIONS.get(role.code, [])
    return perm_code in perms
