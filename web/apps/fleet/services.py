from django.db.models import Q
from .models import Vehicle


def filter_vehicles(qs, cleaned):
    q = cleaned.get("q")
    status = cleaned.get("status")
    fuel = cleaned.get("fuel")
    transmission = cleaned.get("transmission")
    year = cleaned.get("year")
    brand = cleaned.get("brand")
    model = cleaned.get("model")

    if q:
        qs = qs.filter(
            Q(plate_number__icontains=q)
            | Q(vin__icontains=q)
            | Q(brand__name__icontains=q)
            | Q(model__name__icontains=q)
        )

    if status:
        qs = qs.filter(status=status)
    if fuel:
        qs = qs.filter(fuel=fuel)
    if transmission:
        qs = qs.filter(transmission=transmission)
    if year:
        qs = qs.filter(year=year)
    if brand:
        qs = qs.filter(brand=brand)
    if model:
        qs = qs.filter(model=model)

    return qs