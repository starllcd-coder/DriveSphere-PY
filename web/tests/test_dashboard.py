from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import Role, User
from apps.bookings.models import Booking
from apps.customers.models import Customer
from apps.dashboard.services import get_dashboard_kpis
from apps.fleet.models import VehicleBrand, VehicleModel, VehicleCategory, Vehicle
from apps.maintenance.models import MaintenanceTask
from apps.payments.models import Payment


class DashboardImprovementsTests(TestCase):
    def setUp(self):
        for code, label in Role.ROLE_CHOICES:
            Role.objects.get_or_create(code=code, defaults={"name": label})

        manager_role = Role.objects.get(code="MANAGER")
        self.user = User.objects.create_user(
            email="manager@example.com",
            password="pass1234",
            username="manager",
            role=manager_role,
            is_active=True,
        )

        self.customer = Customer.objects.create(name="Alice Walker", phone_number="998877")
        self.brand = VehicleBrand.objects.create(name="Toyota")
        self.model = VehicleModel.objects.create(brand=self.brand, name="Corolla")
        self.category = VehicleCategory.objects.create(name="Sedan")
        self.vehicle = Vehicle.objects.create(
            plate_number="TS-100",
            brand=self.brand,
            model=self.model,
            category=self.category,
            year=2024,
            odometer_km=20500,
            last_service_odometer=10000,
            service_interval_km=10000,
            registration_expiry=date.today() + timedelta(days=10),
        )

    def test_dashboard_kpis_include_real_trends_and_alerts(self):
        today = date.today()
        prev_month_same_day = (today.replace(day=1) - timedelta(days=1)).replace(day=1)

        current_booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=today,
            return_date=today + timedelta(days=2),
            status="CHECKED_OUT",
            total_amount=Decimal("120.000"),
        )
        Booking.objects.filter(id=current_booking.id).update(
            created_at=timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            )
        )

        previous_booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=prev_month_same_day,
            return_date=prev_month_same_day + timedelta(days=1),
            status="CONFIRMED",
            total_amount=Decimal("50.000"),
        )
        Booking.objects.filter(id=previous_booking.id).update(
            created_at=timezone.make_aware(
                timezone.datetime.combine(prev_month_same_day, timezone.datetime.min.time())
            )
        )

        extra_current_booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=today + timedelta(days=5),
            return_date=today + timedelta(days=6),
            status="CONFIRMED",
            total_amount=Decimal("75.000"),
        )
        Booking.objects.filter(id=extra_current_booking.id).update(
            created_at=timezone.make_aware(
                timezone.datetime.combine(today, timezone.datetime.min.time())
            )
        )

        Payment.objects.create(
            booking=current_booking,
            receipt_number="RCP-1",
            payment_date=today,
            amount=Decimal("120.000"),
        )
        Payment.objects.create(
            booking=previous_booking,
            receipt_number="RCP-2",
            payment_date=prev_month_same_day,
            amount=Decimal("60.000"),
        )

        MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            task_type="SERVICE",
            status="OPEN",
            due_date=today,
        )

        kpis = get_dashboard_kpis()

        self.assertGreater(kpis["trend_total_bookings"], 0)
        self.assertGreater(kpis["trend_earnings"], 0)
        self.assertEqual(kpis["active_rentals"], 1)
        self.assertEqual(kpis["today_pickups"], 1)
        self.assertEqual(kpis["upcoming_services"], 1)
        self.assertEqual(kpis["expiring_documents"], 1)
        self.assertEqual(kpis["maintenance_open"], 1)
        self.assertGreater(kpis["fleet_utilization"], 0)

    def test_global_search_returns_cross_module_results(self):
        booking = Booking.objects.create(
            customer=self.customer,
            vehicle=self.vehicle,
            pickup_date=date.today(),
            return_date=date.today() + timedelta(days=1),
            status="CONFIRMED",
            reference="DS-SEARCH",
            total_amount=Decimal("88.000"),
        )
        Payment.objects.create(
            booking=booking,
            receipt_number="RCP-SEARCH",
            payment_date=date.today(),
            amount=Decimal("88.000"),
        )
        MaintenanceTask.objects.create(
            vehicle=self.vehicle,
            task_type="SERVICE",
            status="OPEN",
            notes="Searchable engine check",
        )

        self.client.force_login(self.user)
        response = self.client.get("/api/search/?q=SEARCH")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        labels = {group["label"] for group in data["groups"]}
        self.assertIn("Bookings", labels)
        self.assertIn("Payments", labels)

        response_vehicle = self.client.get("/api/search/?q=TS-100")
        vehicle_labels = {group["label"] for group in response_vehicle.json()["groups"]}
        self.assertIn("Vehicles", vehicle_labels)

        response_customer = self.client.get("/api/search/?q=Alice")
        customer_labels = {group["label"] for group in response_customer.json()["groups"]}
        self.assertIn("Customers", customer_labels)
