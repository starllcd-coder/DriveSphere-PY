# DriveSphere Staff App

Internal mobile app for Admin and Employees (Manager, Agent, Mechanic, Accountant, Viewer).

## Chunk Plan

1. Chunk 1: Foundation + Auth + Role Shell
2. Chunk 2: Employee Operations (bookings, customers, maintenance, payments)
3. Chunk 3: Admin + Accountant Modules (employees, reports, branches)
4. Chunk 4: Hardening + Release (notifications/profile/readiness)

## Run

```bash
flutter pub get
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8000/api/v1
```

