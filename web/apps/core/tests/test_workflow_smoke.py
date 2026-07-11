from datetime import timedelta
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.bookings.services import checkout_booking, create_booking, finalize_return
from apps.customers.models import Customer
from apps.fleet.models import Vehicle, VehicleBrand, VehicleCategory, VehicleModel
from apps.payments.services import create_payment, create_refund, get_booking_net_paid


class WorkflowSmokeTests(TestCase):
    def setUp(self):
        for code, label in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": label})

        admin_role = Role.objects.get(code="ADMIN")
        self.admin = User.objects.create_user(
            email="smoke-admin@local",
            password="SmokePass@123",
            username="smoke-admin",
            role=admin_role,
            is_active=True,
            is_staff=True,
        )
        self.factory = RequestFactory()

    def _make_customer_vehicle(self):
        customer = Customer.objects.create(
            name="Smoke Customer",
            phone_number="96890000000",
            id_number="SMK-001",
        )
        brand = VehicleBrand.objects.create(name="SmokeBrand")
        model = VehicleModel.objects.create(brand=brand, name="SmokeModel")
        category = VehicleCategory.objects.create(name="SUV")
        vehicle = Vehicle.objects.create(
            plate_number="SMK-1001",
            brand=brand,
            model=model,
            category=category,
            year=2025,
            daily_rate=Decimal("50.000"),
            deposit=Decimal("20.000"),
            status="AVAILABLE",
        )
        return customer, vehicle

    def test_auth_v1_login_returns_tokens(self):
        response = self.client.post(
            "/api/v1/auth/login/",
            data={"identifier": "smoke-admin@local", "password": "SmokePass@123"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body.get("ok"))
        self.assertIn("data", body)
        self.assertIn("tokens", body["data"])
        self.assertIn("access", body["data"]["tokens"])

    def test_settings_employee_save_success_and_duplicate_validation(self):
        self.client.force_login(self.admin)

        create_response = self.client.post(
            "/settings/api/employees/create/",
            data={
                "username": "smoke-employee",
                "email": "smoke-employee@local",
                "password": "Smoke123!",
                "role": "ADMIN",
            },
            content_type="application/json",
        )
        self.assertEqual(create_response.status_code, 200)
        self.assertTrue(create_response.json().get("ok"))
        self.assertEqual(create_response.json().get("message"), "User saved")

        duplicate_response = self.client.post(
            "/settings/api/employees/create/",
            data={
                "username": "smoke-employee",
                "email": "smoke-employee@local",
                "password": "Smoke123!",
                "role": "ADMIN",
            },
            content_type="application/json",
        )
        self.assertEqual(duplicate_response.status_code, 400)
        self.assertFalse(duplicate_response.json().get("ok"))
        self.assertIn("already exists", duplicate_response.json().get("error", "").lower())

    def test_booking_checkout_return_and_payment_refund_flow(self):
        customer, vehicle = self._make_customer_vehicle()
        today = timezone.localdate()

        booking = create_booking(
            branch=None,
            created_by=self.admin,
            customer=customer,
            vehicle=vehicle,
            pickup_date=today,
            return_date=today + timedelta(days=2),
            daily_rate=Decimal("50.000"),
            deposit_amount=Decimal("20.000"),
            vat_rate=Decimal("0"),
            extras=[],
            status="CONFIRMED",
            notes="smoke",
        )
        self.assertEqual(booking.status, "CONFIRMED")
        self.assertEqual(booking.total_amount, Decimal("100.000"))

        checkout_booking(
            booking,
            inspector=self.admin,
            odometer_out_km=1000,
            fuel_out_percent=100,
            checklist={"spare": True, "docs": True},
            customer_signature_data="sig-data",
        )
        booking.refresh_from_db()
        vehicle.refresh_from_db()
        self.assertEqual(booking.status, "CHECKED_OUT")
        self.assertEqual(vehicle.status, "RENTED")

        ret = finalize_return(
            booking,
            inspector=self.admin,
            inspector_name="Inspector",
            actual_return_date=today + timedelta(days=1),  # early return
            odometer_in_km=1100,
            fuel_return_percent=90,
            fuel_charge=Decimal("0"),
            late_fee=Decimal("0"),
            damage_fee=Decimal("0"),
            other_fee=Decimal("0"),
            damage_details="",
            inspector_signature_data="sig-return",
            extra_km_override=0,
        )
        booking.refresh_from_db()
        vehicle.refresh_from_db()
        self.assertEqual(booking.status, "RETURNED")
        self.assertEqual(vehicle.status, "AVAILABLE")
        self.assertEqual(ret.final_due, Decimal("30.000"))

        request = self.factory.post("/payments/")
        request.user = self.admin
        request.session = {}

        payment = create_payment(
            request=request,
            booking=booking,
            amount=Decimal("30.000"),
            method="CASH",
            notes="Return settlement",
        )
        refund = create_refund(
            request=request,
            payment=payment,
            amount=Decimal("10.000"),
            method="CASH",
            notes="Partial refund",
        )
        self.assertEqual(payment.status, "PAID")
        self.assertEqual(refund.status, "REFUNDED")
        self.assertEqual(get_booking_net_paid(booking), Decimal("20.000"))
