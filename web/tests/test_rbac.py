import json
from datetime import date, timedelta

from django.test import TestCase

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.fleet.models import VehicleBrand, VehicleModel, VehicleCategory, Vehicle
from apps.payments.models import Payment


class RbacEnforcementTests(TestCase):
    def setUp(self):
        for code, label in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": label})

        self.manager = self._create_user("manager@example.com", "MANAGER")
        self.agent = self._create_user("agent@example.com", "AGENT")
        self.mechanic = self._create_user("mechanic@example.com", "MECHANIC")
        self.viewer = self._create_user("viewer@example.com", "VIEWER")

        self.customer = Customer.objects.create(name="Alice")
        brand = VehicleBrand.objects.create(name="BrandX")
        model = VehicleModel.objects.create(brand=brand, name="ModelY")
        category = VehicleCategory.objects.create(name="Sedan")
        self.vehicle = Vehicle.objects.create(
            plate_number="XYZ-100",
            brand=brand,
            model=model,
            category=category,
            year=2024,
        )

        self.booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
        )

        self.payment = Payment.objects.create(
            booking=self.booking,
            receipt_number="RCPT-0001",
            payment_date=date.today(),
            amount="50.000",
        )

    def _create_user(self, email: str, role_code: str):
        role = Role.objects.get(code=role_code)
        user = User.objects.create(email=email, username=email.split("@")[0], role=role, is_active=True)
        user.set_password("pass1234")
        user.save()
        return user

    def test_booking_create_requires_permission(self):
        self.client.force_login(self.mechanic)
        payload = {
            "vehicle_id": self.vehicle.id,
            "pickup_date": date.today().isoformat(),
            "return_date": (date.today() + timedelta(days=1)).isoformat(),
            "customer_name": "Client A",
        }
        resp = self.client.post(
            "/api/bookings/create/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_booking_create_allowed_for_manager(self):
        self.client.force_login(self.manager)
        payload = {
            "vehicle_id": self.vehicle.id,
            "pickup_date": (date.today() + timedelta(days=2)).isoformat(),
            "return_date": (date.today() + timedelta(days=3)).isoformat(),
            "customer_name": "Client B",
        }
        resp = self.client.post(
            "/api/bookings/create/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.json()
        self.assertIn("booking", data)

    def test_booking_extend_requires_permission(self):
        self.client.force_login(self.mechanic)
        payload = {"new_return_date": (date.today() + timedelta(days=2)).isoformat()}
        resp = self.client.post(
            f"/api/bookings/{self.booking.id}/extend/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_payment_update_requires_manage(self):
        self.client.force_login(self.agent)
        payload = {"amount": "25.000"}
        resp = self.client.post(
            f"/api/payments/{self.payment.id}/update/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_settings_save_requires_permission(self):
        self.client.force_login(self.agent)
        resp = self.client.post(
            "/settings/api/business/save/",
            data=json.dumps({"business_name": "Test"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 403)

    def test_reports_financial_requires_permission(self):
        self.client.force_login(self.agent)
        resp = self.client.get("/api/reports/financial/?period=today")
        self.assertEqual(resp.status_code, 403)

    def test_viewer_can_access_limited_reports_but_not_mutations(self):
        self.client.force_login(self.viewer)

        reports_resp = self.client.get("/api/reports/customers/?period=today")
        self.assertEqual(reports_resp.status_code, 200)

        payload = {
            "vehicle_id": self.vehicle.id,
            "pickup_date": (date.today() + timedelta(days=2)).isoformat(),
            "return_date": (date.today() + timedelta(days=3)).isoformat(),
            "customer_name": "Viewer Client",
        }
        booking_resp = self.client.post(
            "/api/bookings/create/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(booking_resp.status_code, 403)
