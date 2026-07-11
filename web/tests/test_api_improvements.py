from datetime import date, timedelta
from decimal import Decimal

from django.core.cache import cache
from django.test import TestCase

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.core.models import Notification, SupportMessage
from apps.customers.models import Customer
from apps.fleet.models import Vehicle, VehicleBrand, VehicleCategory, VehicleModel
from apps.payments.models import Payment, Refund


class ApiImprovementsTests(TestCase):
    def setUp(self):
        for code, label in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": label})

        manager_role = Role.objects.get(code="MANAGER")
        self.user = User.objects.create_user(
            email="manager2@example.com",
            password="pass1234",
            username="manager2",
            role=manager_role,
            is_active=True,
        )

        self.customer = Customer.objects.create(name="API Customer", phone_number="971500000")
        brand = VehicleBrand.objects.create(name="Nissan")
        model = VehicleModel.objects.create(brand=brand, name="Sunny")
        category = VehicleCategory.objects.create(name="Sedan")
        self.vehicle = Vehicle.objects.create(
            plate_number="API-200",
            brand=brand,
            model=model,
            category=category,
            year=2024,
            daily_rate=Decimal("30.000"),
            status="AVAILABLE",
        )

    def test_auth_login_returns_tokens(self):
        response = self.client.post(
            "/api/auth/login/",
            data={"identifier": "manager2@example.com", "password": "pass1234"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIn("tokens", body)
        self.assertIn("access", body["tokens"])
        self.assertIn("refresh", body["tokens"])

    def test_auth_v1_login_uses_standard_shape(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            data={"identifier": "manager2@example.com", "password": "pass1234"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertIn("data", body)
        self.assertIn("tokens", body["data"])
        self.assertIn("user", body["data"])

    def test_otp_verify_success_and_failure(self):
        cache.set("otp:+971500000", "123456", timeout=90)

        ok_response = self.client.post(
            "/api/auth/otp/verify/",
            data={"phone": "+971500000", "otp": "123456"},
            content_type="application/json",
        )
        self.assertEqual(ok_response.status_code, 200)
        self.assertTrue(ok_response.json()["success"])

        fail_response = self.client.post(
            "/api/auth/otp/verify/",
            data={"phone": "+971500000", "otp": "999999"},
            content_type="application/json",
        )
        self.assertEqual(fail_response.status_code, 200)
        self.assertFalse(fail_response.json()["success"])

    def test_otp_verify_v1_standard_shape(self):
        cache.set("otp:+971500001", "111111", timeout=90)
        ok_response = self.client.post(
            "/api/v1/auth/otp/verify/",
            data={"phone": "+971500001", "otp": "111111"},
            content_type="application/json",
        )
        self.assertEqual(ok_response.status_code, 200)
        ok_body = ok_response.json()
        self.assertTrue(ok_body["ok"])
        self.assertTrue(ok_body["data"]["verified"])

        fail_response = self.client.post(
            "/api/v1/auth/otp/verify/",
            data={"phone": "+971500001", "otp": "222222"},
            content_type="application/json",
        )
        self.assertEqual(fail_response.status_code, 200)
        fail_body = fail_response.json()
        self.assertFalse(fail_body["ok"])
        self.assertFalse(fail_body["verified"])

    def test_booking_overlap_conflict_returns_400(self):
        self.client.force_login(self.user)
        Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today() + timedelta(days=2),
            return_date=date.today() + timedelta(days=5),
            status="CONFIRMED",
            daily_rate=Decimal("30.000"),
            subtotal_amount=Decimal("90.000"),
            total_amount=Decimal("90.000"),
        )

        response = self.client.post(
            "/api/bookings/create/",
            data={
                "customer_id": self.customer.id,
                "vehicle_id": self.vehicle.id,
                "pickup_date": (date.today() + timedelta(days=3)).isoformat(),
                "return_date": (date.today() + timedelta(days=4)).isoformat(),
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_payment_idempotency_replay_returns_same_record(self):
        self.client.force_login(self.user)
        booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
            total_amount=Decimal("100.000"),
        )

        payload = {
            "booking_id": booking.id,
            "amount": "50.000",
            "method": "CARD",
            "idempotency_key": "pay-key-1",
        }
        first = self.client.post("/api/payments/create/", data=payload, content_type="application/json")
        second = self.client.post("/api/payments/create/", data=payload, content_type="application/json")

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(Payment.objects.count(), 1)
        self.assertEqual(first.json()["payment"]["id"], second.json()["payment"]["id"])

    def test_payment_idempotency_conflict_payload_rejected(self):
        self.client.force_login(self.user)
        booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
            total_amount=Decimal("100.000"),
        )

        self.client.post(
            "/api/payments/create/",
            data={
                "booking_id": booking.id,
                "amount": "50.000",
                "method": "CARD",
                "idempotency_key": "pay-key-2",
            },
            content_type="application/json",
        )

        conflict = self.client.post(
            "/api/payments/create/",
            data={
                "booking_id": booking.id,
                "amount": "70.000",
                "method": "CARD",
                "idempotency_key": "pay-key-2",
            },
            content_type="application/json",
        )
        self.assertEqual(conflict.status_code, 400)
        self.assertIn("Idempotency key", conflict.json().get("error", ""))

    def test_refund_over_payment_is_rejected(self):
        self.client.force_login(self.user)
        booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
            total_amount=Decimal("100.000"),
        )
        payment = Payment.objects.create(
            booking=booking,
            receipt_number="RCT-TST-001",
            payment_date=date.today(),
            amount=Decimal("100.000"),
            method="CASH",
            status="PAID",
        )

        response = self.client.post(
            "/api/payments/refunds/create/",
            data={"payment_id": payment.id, "amount": "101.000", "method": "CASH"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Refund.objects.count(), 0)

    def test_api_v1_validation_error_is_standardized(self):
        self.client.force_login(self.user)
        response = self.client.post("/api/v1/payments/create/", data={}, content_type="application/json")
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn("ok", body)
        self.assertFalse(body["ok"])
        self.assertIn("details", body)

    def test_api_v1_vehicles_list_has_standard_paginated_shape(self):
        response = self.client.get("/api/v1/vehicles/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertIn("data", body)
        self.assertIn("pagination", body)

    def test_legacy_api_vehicles_list_keeps_array_shape(self):
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertIsInstance(body, list)

    def test_api_v1_notifications_and_support_use_standard_shape(self):
        self.client.force_login(self.user)
        Notification.objects.create(
            user=self.user,
            title="Reminder",
            message="Review booking",
            notification_type="REMINDER",
        )
        SupportMessage.objects.create(
            user=self.user,
            sender="customer",
            message="Need help",
        )

        notifications = self.client.get("/api/v1/notifications/")
        self.assertEqual(notifications.status_code, 200)
        n_body = notifications.json()
        self.assertTrue(n_body["ok"])
        self.assertIn("data", n_body)
        self.assertIn("pagination", n_body)

        support = self.client.get("/api/v1/support/messages/")
        self.assertEqual(support.status_code, 200)
        s_body = support.json()
        self.assertTrue(s_body["ok"])
        self.assertIn("data", s_body)
        self.assertIn("pagination", s_body)

    def test_api_v1_profile_get_and_update_use_standard_shape(self):
        self.client.force_login(self.user)
        get_response = self.client.get("/api/v1/profile/")
        self.assertEqual(get_response.status_code, 200)
        self.assertTrue(get_response.json()["ok"])

        update_response = self.client.put(
            "/api/v1/profile/update/",
            data={"first_name": "Updated"},
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        update_body = update_response.json()
        self.assertTrue(update_body["ok"])
        self.assertIn("data", update_body)
