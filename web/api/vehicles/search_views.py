from datetime import datetime
from django.db.models import Avg

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from apps.fleet.models import Vehicle
from apps.bookings.models import Booking

from api.responses import paginated_list_response
from .serializers import VehicleSearchSerializer


class VehicleSearchAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        brand = request.query_params.get("brand")
        country = request.query_params.get("country")
        city = request.query_params.get("city")
        pickup_location = request.query_params.get("pickup_location")
        return_location = request.query_params.get("return_location")
        category = request.query_params.get("category")
        transmission = request.query_params.get("transmission")
        fuel_type = request.query_params.get("fuel_type")
        min_seats = request.query_params.get("min_seats")
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        max_deposit = request.query_params.get("max_deposit")
        instant_book = request.query_params.get("instant_book")
        delivery_available = request.query_params.get("delivery_available")
        airport_pickup = request.query_params.get("airport_pickup")
        company = request.query_params.get("company")
        min_rating = request.query_params.get("min_rating")
        pickup_date = request.query_params.get("pickup_date")
        return_date = request.query_params.get("return_date")

        vehicles = Vehicle.objects.all().order_by("-id")

        if brand:
            vehicles = vehicles.filter(brand__name__icontains=brand)

        if country and not city:
            vehicles = vehicles.filter(branch__name__icontains=country)

        if city:
            vehicles = vehicles.filter(branch__name__icontains=city)

        if pickup_location:
            vehicles = vehicles.filter(branch__name__icontains=pickup_location)

        if return_location:
            vehicles = vehicles.filter(branch__name__icontains=return_location)

        if category:
            vehicles = vehicles.filter(category__name__icontains=category)

        if transmission:
            vehicles = vehicles.filter(transmission__iexact=transmission)

        if fuel_type:
            vehicles = vehicles.filter(fuel__iexact=fuel_type)

        if min_seats:
            try:
                vehicles = vehicles.filter(seats__gte=int(min_seats))
            except Exception:
                pass

        if min_price:
            try:
                vehicles = vehicles.filter(daily_rate__gte=min_price)
            except Exception:
                pass

        if max_price:
            try:
                vehicles = vehicles.filter(daily_rate__lte=max_price)
            except Exception:
                pass

        if max_deposit:
            try:
                vehicles = vehicles.filter(deposit__lte=max_deposit)
            except Exception:
                pass

        if company:
            vehicles = vehicles.filter(branch__name__icontains=company)

        vehicle_fields = {f.name for f in Vehicle._meta.get_fields()}

        if instant_book is not None and "instant_book" in vehicle_fields:
            if instant_book in ["true", "1", "True", True]:
                vehicles = vehicles.filter(instant_book=True)
            elif instant_book in ["false", "0", "False", False]:
                vehicles = vehicles.filter(instant_book=False)

        if delivery_available is not None and "delivery_available" in vehicle_fields:
            if delivery_available in ["true", "1", "True", True]:
                vehicles = vehicles.filter(delivery_available=True)
            elif delivery_available in ["false", "0", "False", False]:
                vehicles = vehicles.filter(delivery_available=False)

        if airport_pickup is not None and "airport_pickup" in vehicle_fields:
            if airport_pickup in ["true", "1", "True", True]:
                vehicles = vehicles.filter(airport_pickup=True)
            elif airport_pickup in ["false", "0", "False", False]:
                vehicles = vehicles.filter(airport_pickup=False)

        if pickup_date and return_date:
            pickup_date = datetime.strptime(pickup_date, "%Y-%m-%d").date()
            return_date = datetime.strptime(return_date, "%Y-%m-%d").date()

            booked_vehicle_ids = Booking.objects.filter(
                pickup_date__lte=return_date,
                return_date__gte=pickup_date,
            ).values_list("vehicle_id", flat=True)

            vehicles = vehicles.exclude(id__in=booked_vehicle_ids)

        if min_rating:
            try:
                vehicles = vehicles.annotate(avg_rating=Avg("reviews__rating")).filter(
                    avg_rating__gte=float(min_rating)
                )
            except Exception:
                pass

        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, vehicles, VehicleSearchSerializer)
        serializer = VehicleSearchSerializer(
            vehicles,
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)
