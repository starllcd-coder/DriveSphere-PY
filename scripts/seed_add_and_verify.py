from apps.fleet.seed_data import ensure_vehicle_brands_models
from apps.fleet.models import VehicleBrand

ensure_vehicle_brands_models()
brands = ['Cadillac','GMC','Porsche','Mini','Citroen','Fiat','Alfa Romeo','Mahindra','Tata Motors','Isuzu']
for name in brands:
    b = VehicleBrand.objects.filter(name__iexact=name).first()
    if not b:
        print(f"{name} MISSING")
        continue
    models = [m.name for m in b.models.all().order_by('name')]
    print(f"{name} | found:{len(models)} -> {models}")
