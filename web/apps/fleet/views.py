import json
from datetime import date

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from apps.accounts.permissions import has_perm, is_admin
from apps.core.services import get_active_branch
from apps.maintenance.models import MaintenanceTask

from .forms import VehicleForm, VehicleDocumentForm, VehiclePhotoForm
from .models import (
    Vehicle,
    VehicleBrand,
    VehicleModel,
    VehicleDocument,
    VehiclePhoto,
    VehicleCategory,
)
from .seed_data import ensure_vehicle_brands_models, ensure_all_fleet_seed_data


# -------------------------
# Helpers
# -------------------------
def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


def _status_label(code: str) -> str:
    mapping = {
        "AVAILABLE": "Available",
        "RESERVED": "Reserved",
        "RENTED": "Rented",
        "MAINTENANCE": "Maintenance",
        "INACTIVE": "Inactive",
    }
    return mapping.get(code or "", code or "")


def _apply_branch(qs, branch, field_name: str = "branch"):
    if branch:
        return qs.filter(**{field_name: branch})
    return qs


def _maybe_create_service_task(vehicle, *, branch=None, user=None, previous_odometer=None):
    try:
        interval = int(getattr(vehicle, "service_interval_km", 0) or 0)
        last_service = int(getattr(vehicle, "last_service_odometer", 0) or 0)
        current = int(getattr(vehicle, "odometer_km", 0) or 0)
    except Exception:
        return

    if interval <= 0:
        return
    if previous_odometer is not None and current <= int(previous_odometer or 0):
        return
    if current < (last_service + interval):
        return

    existing = MaintenanceTask.objects.filter(
        vehicle=vehicle,
        task_type="SERVICE",
        status__in=["OPEN", "IN_PROGRESS"],
    ).exists()
    if existing:
        return

    task = MaintenanceTask(
        vehicle=vehicle,
        task_type="SERVICE",
        priority="MEDIUM",
        due_date=timezone.localdate(),
        notes="Auto-created from odometer reading.",
        assignee=user if user and hasattr(MaintenanceTask, "assignee_id") else None,
    )
    if branch and hasattr(task, "branch"):
        task.branch = branch
    task.save()

    if getattr(vehicle, "status", "") != "MAINTENANCE":
        vehicle.status = "MAINTENANCE"
        vehicle.save(update_fields=["status"])


# -------------------------
# Pages
# -------------------------
@login_required
def vehicles_page(request):
    if not has_perm(request.user, "fleet.view"):
        return render(request, "errors/403.html", status=403)
    return render(request, "vehicles/index.html")


def _vehicle_form_for_request(request, *, instance=None):
    form = VehicleForm(request.POST or None, instance=instance)
    if "branch" in form.fields:
        form.fields["branch"].widget = forms.HiddenInput()

    brand_id = None
    if request.method == "POST":
        brand_id = request.POST.get("brand") or None
    elif instance and instance.brand_id:
        brand_id = instance.brand_id

    if brand_id:
        form.fields["model"].queryset = VehicleModel.objects.filter(brand_id=brand_id).order_by("name")
    else:
        form.fields["model"].queryset = VehicleModel.objects.none()

    form.fields["brand"].queryset = VehicleBrand.objects.all().order_by("name")
    form.fields["category"].queryset = VehicleCategory.objects.all().order_by("name")
    return form


def _wizard_get(request):
    return request.session.get("vehicle_wizard", {})


def _wizard_set(request, data):
    request.session["vehicle_wizard"] = data
    request.session.modified = True


def _wizard_clear(request):
    if "vehicle_wizard" in request.session:
        del request.session["vehicle_wizard"]
        request.session.modified = True


@login_required
def vehicle_wizard_start(request):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)
    return redirect("vehicle_wizard_details")


@login_required
def vehicle_wizard_details(request):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    ensure_vehicle_brands_models()
    data = _wizard_get(request)
    brands = VehicleBrand.objects.all().order_by("name")
    models = []
    if data.get("brand_id"):
        models = VehicleModel.objects.filter(brand_id=data.get("brand_id")).order_by("name")

    now = date.today().year
    # years range from 2010 up to 2070 (inclusive), newest first so current year is near the top
    years = list(range(2070, 2009, -1))

    # if no year selected yet, default to current year
    if not data.get("year"):
        data["year"] = str(now)

    if request.method == "POST":
        brand_id = request.POST.get("brand_id") or ""
        model_id = request.POST.get("model_id") or ""
        brand_new = (request.POST.get("brand_new") or "").strip()
        model_new = (request.POST.get("model_new") or "").strip()

        if brand_new:
            brand_obj, _ = VehicleBrand.objects.get_or_create(name=brand_new)
            brand_id = str(brand_obj.id)

        if model_new and brand_id:
            model_obj, _ = VehicleModel.objects.get_or_create(brand_id=int(brand_id), name=model_new)
            model_id = str(model_obj.id)

        data.update({
            "plate_number": (request.POST.get("plate_number") or "").strip(),
            "vin": (request.POST.get("vin") or "").strip(),
            "brand_id": brand_id,
            "model_id": model_id,
            "year": request.POST.get("year") or "",
        })
        _wizard_set(request, data)
        return redirect("vehicle_wizard_specs")

    context = {
        "title": "New Vehicle",
        "step": 1,
        "data": data,
        "brands": brands,
        "models": models,
        "years": years,
    }
    return render(request, "vehicles/wizard/details.html", context)


@login_required
def vehicle_wizard_specs(request):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    # ensure seed data for brands/models and categories exists
    ensure_all_fleet_seed_data()

    data = _wizard_get(request)
    categories = VehicleCategory.objects.all().order_by("name")

    if request.method == "POST":
        data.update({
            "category_id": request.POST.get("category_id") or "",
            "fuel": request.POST.get("fuel") or "PETROL",
            "transmission": request.POST.get("transmission") or "AUTOMATIC",
            "color": (request.POST.get("color") or "").strip(),
            "seats": request.POST.get("seats") or "",
            "odometer_km": request.POST.get("odometer_km") or "0",
        })
        _wizard_set(request, data)
        return redirect("vehicle_wizard_pricing")

    context = {
        "title": "New Vehicle",
        "step": 2,
        "data": data,
        "categories": categories,
    }
    return render(request, "vehicles/wizard/specs.html", context)


@login_required
def vehicle_wizard_pricing(request):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    data = _wizard_get(request)

    if request.method == "POST":
        data.update({
            "status": request.POST.get("status") or "AVAILABLE",
            "daily_rate": request.POST.get("daily_rate") or "0",
            "deposit": request.POST.get("deposit") or "0",
            "tags": (request.POST.get("tags") or "").strip(),
            "notes": (request.POST.get("notes") or "").strip(),
        })
        _wizard_set(request, data)
        return redirect("vehicle_wizard_documents")

    context = {
        "title": "New Vehicle",
        "step": 3,
        "data": data,
    }
    return render(request, "vehicles/wizard/pricing.html", context)


@login_required
def vehicle_wizard_documents(request):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    data = _wizard_get(request)

    if request.method == "POST":
        branch = get_active_branch(request)

        if not data.get("plate_number") or not data.get("brand_id") or not data.get("model_id") or not data.get("year"):
            return redirect("vehicle_wizard_details")

        try:
            v = Vehicle.objects.create(
                branch=branch,
                plate_number=data.get("plate_number") or "",
                vin=data.get("vin") or "",
                brand_id=int(data.get("brand_id")),
                model_id=int(data.get("model_id")),
                year=int(data.get("year") or 0),
                category_id=int(data.get("category_id")) if data.get("category_id") else None,
                fuel=data.get("fuel") or "PETROL",
                transmission=data.get("transmission") or "AUTOMATIC",
                color=data.get("color") or "",
                seats=int(data.get("seats") or 5),
                odometer_km=int(data.get("odometer_km") or 0),
                status=data.get("status") or "AVAILABLE",
                daily_rate=data.get("daily_rate") or 0,
                deposit=data.get("deposit") or 0,
                tags=data.get("tags") or "",
                notes=data.get("notes") or "",
                registration_expiry=request.POST.get("registration_expiry") or None,
                insurance_expiry=request.POST.get("insurance_expiry") or None,
            )

            v.last_service_odometer = v.odometer_km
            v.save(update_fields=["last_service_odometer"])

            _maybe_create_service_task(v, branch=branch, user=request.user)

            if request.FILES.get("registration_scan"):
                VehicleDocument.objects.create(
                    vehicle=v,
                    doc_type="REGISTRATION",
                    file=request.FILES["registration_scan"],
                    expiry_date=request.POST.get("registration_expiry") or None,
                )

            if request.FILES.get("insurance_scan"):
                VehicleDocument.objects.create(
                    vehicle=v,
                    doc_type="INSURANCE",
                    file=request.FILES["insurance_scan"],
                    expiry_date=request.POST.get("insurance_expiry") or None,
                )

            for f in request.FILES.getlist("photos"):
                VehiclePhoto.objects.create(vehicle=v, image=f)

            _wizard_clear(request)
            return redirect("vehicles_page")
        except Exception:
            pass

    context = {
        "title": "New Vehicle",
        "step": 4,
        "data": data,
    }
    return render(request, "vehicles/wizard/documents.html", context)


@login_required
def vehicle_edit_page(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    branch = get_active_branch(request)
    vehicle = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    form = _vehicle_form_for_request(request, instance=vehicle)

    if request.method == "POST" and form.is_valid():
        prev_odometer = vehicle.odometer_km
        vehicle = form.save()
        _maybe_create_service_task(vehicle, branch=branch, user=request.user, previous_odometer=prev_odometer)
        return redirect("vehicles_page")

    context = {
        "title": "Edit Vehicle",
        "page_title": "Edit Vehicle",
        "form": form,
        "vehicle": vehicle,
        "mode": "edit",
    }
    return render(request, "fleet/vehicle_form.html", context)


@login_required
def vehicle_delete_page(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return render(request, "errors/403.html", status=403)

    branch = get_active_branch(request)
    vehicle = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    if request.method == "POST":
        vehicle.delete()
        return redirect("vehicles_page")

    return render(request, "fleet/vehicle_delete.html", {"vehicle": vehicle})


@login_required
def vehicle_documents_page(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    vehicle = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    error = ""

    if request.method == "POST":
        if not has_perm(request.user, "fleet.manage"):
            return render(request, "errors/403.html", status=403)
        form = VehicleDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.vehicle = vehicle
            doc.save()
            return redirect("vehicle_documents_page", vehicle_id=vehicle.id)
        error = "Please complete all required fields."
    else:
        form = VehicleDocumentForm()

    context = {
        "title": "Vehicle Documents",
        "page_title": "Vehicle Documents",
        "vehicle": vehicle,
        "form": form,
        "error": error,
    }
    return render(request, "fleet/vehicle_documents.html", context)


@login_required
def vehicle_photos_page(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.view"):
        return render(request, "errors/403.html", status=403)
    branch = get_active_branch(request)
    vehicle = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    error = ""

    if request.method == "POST":
        if not has_perm(request.user, "fleet.manage"):
            return render(request, "errors/403.html", status=403)
        form = VehiclePhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.vehicle = vehicle
            photo.save()
            return redirect("vehicle_photos_page", vehicle_id=vehicle.id)
        error = "Please select a photo to upload."
    else:
        form = VehiclePhotoForm()

    context = {
        "title": "Vehicle Photos",
        "page_title": "Vehicle Photos",
        "vehicle": vehicle,
        "form": form,
        "error": error,
    }
    return render(request, "fleet/vehicle_photos.html", context)


# -------------------------
# API: Vehicles list
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_vehicles_list(request):
    if not has_perm(request.user, "fleet.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """
    GET /api/vehicles/?plate=&brand=&model=&status=
    Returns:
      { ok: true, results: [ ... ] }
    """
    branch = get_active_branch(request)

    qs = Vehicle.objects.select_related("brand", "model", "category").all().order_by("-id")
    qs = _apply_branch(qs, branch)

    plate = (request.GET.get("plate") or "").strip()
    brand = (request.GET.get("brand") or "").strip()
    model = (request.GET.get("model") or "").strip()
    status = (request.GET.get("status") or "").strip()

    if plate:
        qs = qs.filter(plate_number__icontains=plate)
    if status:
        qs = qs.filter(status=status)
    if brand:
        qs = qs.filter(Q(brand__name__icontains=brand) | Q(brand_name__icontains=brand) if hasattr(Vehicle, "brand_name") else Q(brand__name__icontains=brand))
    if model:
        qs = qs.filter(Q(model__name__icontains=model) | Q(model_name__icontains=model) if hasattr(Vehicle, "model_name") else Q(model__name__icontains=model))

    results = []
    for v in qs[:800]:
        results.append(
            {
                "id": v.id,
                "plate_number": getattr(v, "plate_number", ""),
                "year": getattr(v, "year", "") or "",
                "category": v.category.name if v.category_id else "",
                "category_id": v.category_id or "",
                "transmission": getattr(v, "transmission", "") or "",
                "fuel_type": getattr(v, "fuel_type", "") or "",
                "color": getattr(v, "color", "") or "",
                "status": getattr(v, "status", "") or "",
                "status_label": _status_label(getattr(v, "status", "") or ""),
                "daily_rate": str(getattr(v, "daily_rate", 0) or 0),
                "brand_id": v.brand_id,
                "model_id": v.model_id,
                "brand_name": v.brand.name if v.brand_id else "",
                "model_name": v.model.name if v.model_id else "",
            }
        )

    return JsonResponse({"ok": True, "results": results})


# -------------------------
# API: Vehicle detail
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_vehicle_detail(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    v = get_object_or_404(
        _apply_branch(Vehicle.objects.select_related("brand", "model", "category"), branch),
        id=vehicle_id,
    )

    return JsonResponse(
        {
            "ok": True,
            "vehicle": {
                "id": v.id,
                "plate_number": getattr(v, "plate_number", ""),
                "vin": getattr(v, "vin", "") or "",
                "brand_id": v.brand_id,
                "model_id": v.model_id,
                "year": getattr(v, "year", "") or "",
                "category": v.category.name if v.category_id else "",
                "category_id": v.category_id or "",
                "fuel_type": getattr(v, "fuel_type", "") or "",
                "transmission": getattr(v, "transmission", "") or "",
                "color": getattr(v, "color", "") or "",
                "seats": getattr(v, "seats", "") or "",
                "odometer_km": getattr(v, "odometer_km", "") or "",
                "status": getattr(v, "status", "") or "",
                "daily_rate": str(getattr(v, "daily_rate", 0) or 0),
                "deposit": str(getattr(v, "deposit", 0) or 0),
                "tags": getattr(v, "tags", "") or "",
                "notes": getattr(v, "notes", "") or "",
                "registration_expiry": str(getattr(v, "registration_expiry", "") or "") if getattr(v, "registration_expiry", None) else "",
                "insurance_expiry": str(getattr(v, "insurance_expiry", "") or "") if getattr(v, "insurance_expiry", None) else "",
            },
        }
    )


# -------------------------
# API: Vehicle create / update / delete
# -------------------------
@login_required
@require_http_methods(["POST"])
def api_vehicle_create(request):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    branch = get_active_branch(request)
    data = _json_body(request)

    plate = (data.get("plate_number") or "").strip()
    if not plate:
        return JsonResponse({"ok": False, "error": "Plate Number is required"}, status=400)

    brand_id = data.get("brand_id")
    model_id = data.get("model_id")
    if not brand_id or not model_id:
        return JsonResponse({"ok": False, "error": "Brand and Model are required"}, status=400)

    v = Vehicle.objects.create(
        branch=branch,
        plate_number=plate,
        vin=(data.get("vin") or "").strip(),
        brand_id=int(brand_id),
        model_id=int(model_id),
        year=data.get("year") or None,
        category=(data.get("category") or "").strip(),
        fuel_type=data.get("fuel_type") or "PETROL",
        transmission=data.get("transmission") or "AUTOMATIC",
        color=(data.get("color") or "").strip(),
        seats=data.get("seats") or None,
        odometer_km=data.get("odometer_km") or 0,
        status=data.get("status") or "AVAILABLE",
        daily_rate=data.get("daily_rate") or 0,
        deposit=data.get("deposit") or 0,
        tags=(data.get("tags") or "").strip(),
        notes=(data.get("notes") or "").strip(),
        registration_expiry=data.get("registration_expiry") or None,
        insurance_expiry=data.get("insurance_expiry") or None,
    )

    v.last_service_odometer = v.odometer_km
    v.service_interval_km = int(data.get("service_interval_km") or v.service_interval_km or 0)
    v.save(update_fields=["last_service_odometer", "service_interval_km"])

    _maybe_create_service_task(v, branch=branch, user=request.user)

    return JsonResponse({"ok": True, "vehicle_id": v.id})


@login_required
@require_http_methods(["POST"])
def api_vehicle_update(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    data = _json_body(request)

    plate = (data.get("plate_number") or "").strip()
    if not plate:
        return JsonResponse({"ok": False, "error": "Plate Number is required"}, status=400)

    brand_id = data.get("brand_id")
    model_id = data.get("model_id")
    if not brand_id or not model_id:
        return JsonResponse({"ok": False, "error": "Brand and Model are required"}, status=400)

    prev_odometer = v.odometer_km
    v.plate_number = plate
    v.vin = (data.get("vin") or "").strip()
    v.brand_id = int(brand_id)
    v.model_id = int(model_id)
    v.year = data.get("year") or None
    v.category = (data.get("category") or "").strip()
    v.fuel_type = data.get("fuel_type") or v.fuel_type
    v.transmission = data.get("transmission") or v.transmission
    v.color = (data.get("color") or "").strip()
    v.seats = data.get("seats") or None
    v.odometer_km = data.get("odometer_km") or 0
    v.status = data.get("status") or v.status
    v.daily_rate = data.get("daily_rate") or 0
    v.deposit = data.get("deposit") or 0
    v.tags = (data.get("tags") or "").strip()
    v.notes = (data.get("notes") or "").strip()
    v.registration_expiry = data.get("registration_expiry") or None
    v.insurance_expiry = data.get("insurance_expiry") or None
    if data.get("service_interval_km") is not None:
        v.service_interval_km = int(data.get("service_interval_km") or 0)
    if data.get("last_service_odometer") is not None:
        v.last_service_odometer = int(data.get("last_service_odometer") or 0)

    v.save()
    _maybe_create_service_task(v, branch=branch, user=request.user, previous_odometer=prev_odometer)
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_vehicle_delete(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)
    v.delete()
    return JsonResponse({"ok": True})


# -------------------------
# API: Brands / Models
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_vehicle_brands(request):
    branch = get_active_branch(request)

    ensure_vehicle_brands_models()

    qs = VehicleBrand.objects.all().order_by("name")
    # If brands are branch-scoped in your models, this will work; if not, it is harmless.
    if hasattr(VehicleBrand, "branch_id"):
        qs = _apply_branch(qs, branch)

    results = [{"id": b.id, "name": b.name} for b in qs[:1000]]
    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_vehicle_brand_create(request):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    branch = get_active_branch(request)
    data = _json_body(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "Brand name is required"}, status=400)

    kwargs = {"name": name}
    if hasattr(VehicleBrand, "branch_id"):
        kwargs["branch"] = branch

    b = VehicleBrand.objects.create(**kwargs)
    return JsonResponse({"ok": True, "brand_id": b.id})


@login_required
@require_http_methods(["GET"])
def api_vehicle_models(request):
    branch = get_active_branch(request)
    brand_id = (request.GET.get("brand_id") or "").strip()
    if not brand_id:
        return JsonResponse({"ok": True, "results": []})

    qs = VehicleModel.objects.filter(brand_id=int(brand_id)).order_by("name")
    if hasattr(VehicleModel, "branch_id"):
        qs = _apply_branch(qs, branch)

    results = [{"id": m.id, "name": m.name} for m in qs[:2000]]
    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_vehicle_model_create(request):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    branch = get_active_branch(request)
    data = _json_body(request)
    brand_id = data.get("brand_id")
    name = (data.get("name") or "").strip()

    if not brand_id:
        return JsonResponse({"ok": False, "error": "Brand is required"}, status=400)
    if not name:
        return JsonResponse({"ok": False, "error": "Model name is required"}, status=400)

    kwargs = {"brand_id": int(brand_id), "name": name}
    if hasattr(VehicleModel, "branch_id"):
        kwargs["branch"] = branch

    m = VehicleModel.objects.create(**kwargs)
    return JsonResponse({"ok": True, "model_id": m.id})


# -------------------------
# API: Vehicle Docs
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_vehicle_docs_list(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)

    qs = VehicleDocument.objects.filter(vehicle=v).order_by("-created_at")
    labels = dict(getattr(VehicleDocument, "DOC_TYPES", [])) if hasattr(VehicleDocument, "DOC_TYPES") else {}

    results = []
    for d in qs[:500]:
        results.append(
            {
                "id": d.id,
                "doc_type": getattr(d, "doc_type", "OTHER"),
                "doc_type_label": labels.get(getattr(d, "doc_type", "OTHER"), getattr(d, "doc_type", "OTHER")),
                "expiry_date": str(getattr(d, "expiry_date", "") or "") if getattr(d, "expiry_date", None) else "",
                "notes": getattr(d, "notes", "") or "",
                "url": d.file.url if getattr(d, "file", None) else "",
            }
        )

    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_vehicle_docs_upload(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)

    if not request.FILES.get("file"):
        return JsonResponse({"ok": False, "error": "File is required"}, status=400)

    doc = VehicleDocument.objects.create(
        vehicle=v,
        doc_type=request.POST.get("doc_type") or "OTHER",
        file=request.FILES["file"],
        expiry_date=request.POST.get("expiry_date") or None,
        notes=(request.POST.get("notes") or "").strip(),
        uploaded_by=request.user if hasattr(VehicleDocument, "uploaded_by_id") else None,
    )

    return JsonResponse({"ok": True, "doc_id": doc.id})


@login_required
@require_http_methods(["POST"])
def api_vehicle_doc_delete(request, doc_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    d = get_object_or_404(VehicleDocument, id=doc_id)
    d.delete()
    return JsonResponse({"ok": True})


# -------------------------
# API: Vehicle Photos
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_vehicle_photos_list(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)

    qs = VehiclePhoto.objects.filter(vehicle=v).order_by("-created_at")

    results = []
    for p in qs[:800]:
        results.append(
            {
                "id": p.id,
                "caption": getattr(p, "caption", "") or "",
                "url": p.file.url if getattr(p, "file", None) else "",
                "created_at": str(getattr(p, "created_at", "") or ""),
            }
        )

    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_vehicle_photos_upload(request, vehicle_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    branch = get_active_branch(request)
    v = get_object_or_404(_apply_branch(Vehicle.objects.all(), branch), id=vehicle_id)

    if not request.FILES.get("file"):
        return JsonResponse({"ok": False, "error": "Image file is required"}, status=400)

    photo = VehiclePhoto.objects.create(
        vehicle=v,
        file=request.FILES["file"],
        caption=(request.POST.get("caption") or "").strip(),
        uploaded_by=request.user if hasattr(VehiclePhoto, "uploaded_by_id") else None,
    )

    return JsonResponse({"ok": True, "photo_id": photo.id})


@login_required
@require_http_methods(["POST"])
def api_vehicle_photo_delete(request, photo_id: int):
    if not has_perm(request.user, "fleet.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    p = get_object_or_404(VehiclePhoto, id=photo_id)
    p.delete()
    return JsonResponse({"ok": True})