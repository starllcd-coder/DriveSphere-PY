from datetime import timedelta

from django.db.models import Avg, Max, Min, Sum
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status

from apps.fleet.models import Vehicle, TelematicsPing
from api.responses import api_ok, paginated_list_response
from .serializers import VehicleListSerializer, VehicleDetailSerializer, TelematicsPingSerializer


class VehicleListAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        vehicles = Vehicle.objects.all().order_by("-id")
        if request.path.startswith("/api/v1/"):
            return paginated_list_response(request, vehicles, VehicleListSerializer)
        serializer = VehicleListSerializer(vehicles, many=True, context={"request": request})
        return Response(serializer.data)


class VehicleDetailAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = VehicleDetailSerializer(vehicle, context={"request": request})
        if request.path.startswith("/api/v1/"):
            return api_ok(data=serializer.data)
        return Response(serializer.data)


class VehicleTelematicsIngestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        payload = dict(request.data)
        payload["vehicle"] = vehicle.id
        serializer = TelematicsPingSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        ping = serializer.save()

        if request.path.startswith("/api/v1/"):
            return api_ok(data=TelematicsPingSerializer(ping).data, http_status=status.HTTP_201_CREATED)
        return Response(TelematicsPingSerializer(ping).data, status=status.HTTP_201_CREATED)


class VehicleTelematicsMetricsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days") or 7)
        days = max(1, min(days, 90))
        start_at = timezone.now() - timedelta(days=days)

        qs = TelematicsPing.objects.filter(vehicle=vehicle, recorded_at__gte=start_at)
        agg = qs.aggregate(
            latest_odometer=Max("odometer_km"),
            earliest_odometer=Min("odometer_km"),
            avg_speed=Avg("speed_kmh"),
            total_idle=Sum("idle_seconds"),
            avg_fuel=Avg("fuel_percent"),
            fuel_used_total=Sum("fuel_used_liters"),
            avg_battery_voltage=Avg("battery_voltage"),
        )
        distance = max((agg["latest_odometer"] or 0) - (agg["earliest_odometer"] or 0), 0)
        pings_count = qs.count()
        fuel_used_liters = float(agg["fuel_used_total"] or 0)
        efficiency_km_per_liter = round(distance / fuel_used_liters, 2) if fuel_used_liters > 0 else 0.0
        data = {
            "vehicle_id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "window_days": days,
            "distance_km": distance,
            "avg_speed_kmh": round(float(agg["avg_speed"] or 0), 2),
            "idle_seconds": int(agg["total_idle"] or 0),
            "avg_fuel_percent": round(float(agg["avg_fuel"] or 0), 2),
            "fuel_used_liters": round(fuel_used_liters, 3),
            "efficiency_km_per_liter": efficiency_km_per_liter,
            "avg_battery_voltage": round(float(agg["avg_battery_voltage"] or 0), 2),
            "pings_count": pings_count,
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(data=data)
        return Response(data)


class VehicleTelematicsLatestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        ping = TelematicsPing.objects.filter(vehicle=vehicle).order_by("-recorded_at", "-id").first()
        if not ping:
            payload = {"vehicle_id": vehicle.id, "plate_number": vehicle.plate_number, "latest": None}
            if request.path.startswith("/api/v1/"):
                return api_ok(data=payload)
            return Response(payload)

        latest = TelematicsPingSerializer(ping).data
        latest["google_maps_url"] = (
            f"https://maps.google.com/?q={ping.latitude},{ping.longitude}"
            if ping.latitude is not None and ping.longitude is not None
            else ""
        )
        payload = {"vehicle_id": vehicle.id, "plate_number": vehicle.plate_number, "latest": latest}
        if request.path.startswith("/api/v1/"):
            return api_ok(data=payload)
        return Response(payload)


class VehicleTelematicsEventsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days") or 7)
        days = max(1, min(days, 90))
        speed_limit = float(request.query_params.get("speed_limit") or 120)
        start_at = timezone.now() - timedelta(days=days)
        qs = TelematicsPing.objects.filter(vehicle=vehicle, recorded_at__gte=start_at).order_by("recorded_at", "id")

        overspeed_events = []
        harsh_brake_count = 0
        harsh_accel_count = 0
        low_battery_events = 0
        diagnostics_faults = []
        previous_speed = None
        previous_time = None

        for ping in qs:
            speed = float(ping.speed_kmh or 0)
            if speed > speed_limit:
                overspeed_events.append(
                    {
                        "recorded_at": ping.recorded_at,
                        "speed_kmh": round(speed, 2),
                        "latitude": ping.latitude,
                        "longitude": ping.longitude,
                    }
                )

            if previous_speed is not None and previous_time is not None:
                seconds = max((ping.recorded_at - previous_time).total_seconds(), 1)
                delta = speed - previous_speed
                accel = delta / seconds
                if accel <= -4.0:
                    harsh_brake_count += 1
                elif accel >= 4.0:
                    harsh_accel_count += 1

            previous_speed = speed
            previous_time = ping.recorded_at

            if ping.battery_voltage is not None and float(ping.battery_voltage) < 11.8:
                low_battery_events += 1

            if ping.fault_codes:
                diagnostics_faults.extend([str(code) for code in ping.fault_codes if code])

            meta = ping.metadata or {}
            harsh_brake_count += int(meta.get("harsh_brake_count") or 0)
            harsh_accel_count += int(meta.get("harsh_accel_count") or 0)

        payload = {
            "vehicle_id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "window_days": days,
            "speed_limit_kmh": speed_limit,
            "overspeed_count": len(overspeed_events),
            "overspeed_events": overspeed_events[:200],
            "harsh_brake_count": harsh_brake_count,
            "harsh_accel_count": harsh_accel_count,
            "low_battery_events": low_battery_events,
            "fault_codes": sorted(set(diagnostics_faults)),
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(data=payload)
        return Response(payload)


class VehicleTelematicsTripsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            vehicle = Vehicle.objects.get(pk=pk)
        except Vehicle.DoesNotExist:
            return Response({"error": "Vehicle not found"}, status=status.HTTP_404_NOT_FOUND)

        days = int(request.query_params.get("days") or 7)
        days = max(1, min(days, 90))
        start_at = timezone.now() - timedelta(days=days)
        gap_minutes = int(request.query_params.get("gap_minutes") or 45)
        gap_minutes = max(5, min(gap_minutes, 240))

        pings = list(
            TelematicsPing.objects.filter(vehicle=vehicle, recorded_at__gte=start_at)
            .order_by("recorded_at", "id")
        )
        trips = []
        if pings:
            trip_start = pings[0]
            trip_end = pings[0]
            max_speed = float(pings[0].speed_kmh or 0)
            idle_seconds = int(pings[0].idle_seconds or 0)
            fuel_used = float(pings[0].fuel_used_liters or 0)

            for ping in pings[1:]:
                diff_minutes = (ping.recorded_at - trip_end.recorded_at).total_seconds() / 60.0
                if diff_minutes > gap_minutes:
                    distance = max(int(trip_end.odometer_km or 0) - int(trip_start.odometer_km or 0), 0)
                    duration_sec = int((trip_end.recorded_at - trip_start.recorded_at).total_seconds())
                    trips.append(
                        {
                            "start_at": trip_start.recorded_at,
                            "end_at": trip_end.recorded_at,
                            "distance_km": distance,
                            "duration_seconds": max(duration_sec, 0),
                            "max_speed_kmh": round(max_speed, 2),
                            "idle_seconds": idle_seconds,
                            "fuel_used_liters": round(fuel_used, 3),
                            "start_latitude": trip_start.latitude,
                            "start_longitude": trip_start.longitude,
                            "end_latitude": trip_end.latitude,
                            "end_longitude": trip_end.longitude,
                        }
                    )
                    trip_start = ping
                    trip_end = ping
                    max_speed = float(ping.speed_kmh or 0)
                    idle_seconds = int(ping.idle_seconds or 0)
                    fuel_used = float(ping.fuel_used_liters or 0)
                    continue

                trip_end = ping
                max_speed = max(max_speed, float(ping.speed_kmh or 0))
                idle_seconds += int(ping.idle_seconds or 0)
                fuel_used += float(ping.fuel_used_liters or 0)

            distance = max(int(trip_end.odometer_km or 0) - int(trip_start.odometer_km or 0), 0)
            duration_sec = int((trip_end.recorded_at - trip_start.recorded_at).total_seconds())
            trips.append(
                {
                    "start_at": trip_start.recorded_at,
                    "end_at": trip_end.recorded_at,
                    "distance_km": distance,
                    "duration_seconds": max(duration_sec, 0),
                    "max_speed_kmh": round(max_speed, 2),
                    "idle_seconds": idle_seconds,
                    "fuel_used_liters": round(fuel_used, 3),
                    "start_latitude": trip_start.latitude,
                    "start_longitude": trip_start.longitude,
                    "end_latitude": trip_end.latitude,
                    "end_longitude": trip_end.longitude,
                }
            )

        payload = {
            "vehicle_id": vehicle.id,
            "plate_number": vehicle.plate_number,
            "window_days": days,
            "trip_count": len(trips),
            "trips": trips[::-1][:300],
        }
        if request.path.startswith("/api/v1/"):
            return api_ok(data=payload)
        return Response(payload)
