# RBAC Matrix

This document describes the current role-based access control (RBAC) permissions used by the app.

## Permission Codes

- `bookings.view`
- `bookings.create`
- `bookings.update`
- `bookings.delete`
- `bookings.extend`
- `bookings.checkout`
- `bookings.return`
- `bookings.damage_photos`
- `customers.view`
- `customers.manage`
- `fleet.view`
- `fleet.manage`
- `maintenance.view`
- `maintenance.create`
- `maintenance.update`
- `maintenance.delete`
- `payments.view`
- `payments.create`
- `payments.manage`
- `payments.refund`
- `reports.view`
- `reports.view_financial`
- `reports.view_maintenance`
- `reports.view_limited`
- `settings.manage`
- `employees.manage`

## Role Mapping

The authoritative mapping is defined in `apps.accounts.permissions.ROLE_PERMISSIONS`.

- ADMIN: full access to all permissions.
- MANAGER: full operational access (bookings, customers, fleet, maintenance, payments, reports).
- AGENT: bookings and customer management, payments create, limited reports.
- MECHANIC: maintenance operations, fleet view, maintenance reports.
- ACCOUNTANT: payments and financial reports.

## Notes

- Server-side checks enforce permissions at the view/API level.
- Templates use the `has_perm` template tag to hide actions from unauthorized users.
- The settings page includes a read-only permissions matrix for visibility.
