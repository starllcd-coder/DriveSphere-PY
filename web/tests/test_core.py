from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.customers.models import Customer, CustomerDocument
from apps.core.models import AuditLog, Notification
from apps.core.services import sync_operational_notifications
from apps.fleet.models import VehicleBrand, VehicleModel, VehicleCategory, Vehicle
from apps.payments.models import Payment
from apps.settings_app.models import DatabaseProfile
from apps.settings_app.services import save_database_profile


class AuditAndNotificationTests(TestCase):
    def setUp(self):
        for code, label in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": label})

        admin_role = Role.objects.get(code="ADMIN")
        self.user = User.objects.create_user(
            email="admin@example.com",
            password="pass1234",
            username="admin",
            role=admin_role,
            is_active=True,
        )

        customer = Customer.objects.create(
            name="Alert Customer",
            license_expiry_date=date.today() + timedelta(days=5),
        )
        CustomerDocument.objects.create(
            customer=customer,
            doc_type="LICENSE",
            file="customers/documents/test-license.png",
            expiry_date=date.today() + timedelta(days=4),
        )

        brand = VehicleBrand.objects.create(name="Honda")
        model = VehicleModel.objects.create(brand=brand, name="City")
        category = VehicleCategory.objects.create(name="Compact")
        vehicle = Vehicle.objects.create(
            plate_number="AUD-100",
            brand=brand,
            model=model,
            category=category,
            year=2024,
        )
        self.booking = Booking.objects.create(
            customer=customer,
            vehicle=vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
            total_amount=Decimal("80.000"),
        )

    def test_payment_creation_writes_audit_log(self):
        self.client.force_login(self.user)
        response = self.client.post(
            "/api/payments/create/",
            data='{"booking_id": %d, "amount": "80.000", "method": "CARD"}' % self.booking.id,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(AuditLog.objects.filter(action="PAYMENT_CREATED").exists())

        logs = self.client.get("/settings/api/audit-logs/")
        self.assertEqual(logs.status_code, 200)
        self.assertEqual(logs.json()["results"][0]["action"], "PAYMENT_CREATED")

    def test_notifications_include_customer_expiry_alerts(self):
        self.client.force_login(self.user)
        response = self.client.get("/settings/api/notifications/")
        self.assertEqual(response.status_code, 200)
        types = {item["type"] for item in response.json()["results"]}
        self.assertIn("CUSTOMER_LICENSE_EXPIRY", types)
        self.assertIn("CUSTOMER_DOCUMENT_EXPIRY", types)

    def test_notifications_can_be_dismissed_and_snoozed(self):
        self.client.force_login(self.user)
        response = self.client.get("/settings/api/notifications/")
        self.assertEqual(response.status_code, 200)
        first_id = response.json()["results"][0]["id"]

        snooze_response = self.client.post(
            "/settings/api/notifications/snooze/",
            data=f'{{"id": "{first_id}", "days": 1}}',
            content_type="application/json",
        )
        self.assertEqual(snooze_response.status_code, 200)

        response_after_snooze = self.client.get("/settings/api/notifications/")
        ids_after_snooze = {item["id"] for item in response_after_snooze.json()["results"]}
        self.assertNotIn(first_id, ids_after_snooze)

        dismiss_target = next(iter(ids_after_snooze))
        dismiss_response = self.client.post(
            "/settings/api/notifications/dismiss/",
            data=f'{{"id": "{dismiss_target}"}}',
            content_type="application/json",
        )
        self.assertEqual(dismiss_response.status_code, 200)

        response_after_dismiss = self.client.get("/settings/api/notifications/")
        ids_after_dismiss = {item["id"] for item in response_after_dismiss.json()["results"]}
        self.assertNotIn(dismiss_target, ids_after_dismiss)

    def test_operational_notification_sync_creates_and_deduplicates_persistent_rows(self):
        result = sync_operational_notifications(today=date.today())
        self.assertGreater(result["created"], 0)

        reminders = Notification.objects.filter(
            user=self.user,
            notification_type="REMINDER",
            metadata__source="operations_reminder",
        )
        self.assertTrue(reminders.exists())
        first_count = reminders.count()

        second_result = sync_operational_notifications(today=date.today())
        reminders_after_second = Notification.objects.filter(
            user=self.user,
            notification_type="REMINDER",
            metadata__source="operations_reminder",
        )
        self.assertEqual(reminders_after_second.count(), first_count)
        self.assertGreaterEqual(second_result["updated"], first_count)

    def test_notification_sync_endpoint_runs_for_settings_users(self):
        self.client.force_login(self.user)
        response = self.client.post("/settings/api/notifications/sync/", data="{}", content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertTrue(
            AuditLog.objects.filter(action="NOTIFICATION_SYNC_RUN").exists()
        )

    def test_api_v1_payment_list_uses_standard_paginated_shape(self):
        self.client.force_login(self.user)
        Payment.objects.create(
            booking=self.booking,
            receipt_number="RCP-API-V1",
            payment_date=date.today(),
            amount=Decimal("20.000"),
        )

        response = self.client.get("/api/v1/payments/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertIn("data", body)
        self.assertIn("pagination", body)

    def test_database_profile_password_is_encrypted_at_rest(self):
        save_database_profile(
            {
                "provider": "POSTGRES",
                "host": "localhost",
                "port": 5432,
                "database_name": "db",
                "username": "user",
                "password": "super-secret-password",
                "sslmode": "require",
                "is_active": False,
            }
        )
        profile = DatabaseProfile.get_solo()
        self.assertNotEqual(profile.password, "super-secret-password")
        self.assertTrue(profile.password.startswith("enc::"))
        self.assertEqual(profile.get_password(), "super-secret-password")
