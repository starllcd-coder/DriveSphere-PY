import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import has_perm, is_admin

from .models import Customer, CustomerDocument


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return {}


@login_required
def customers_page(request):
    if not has_perm(request.user, "customers.view"):
        return render(request, "errors/403.html", status=403)
    return render(request, "customers/index.html")


def _customer_payload(request):
    return {
        "name": (request.POST.get("name") or "").strip(),
        "phone_number": (request.POST.get("phone_number") or "").strip(),
        "id_type": request.POST.get("id_type") or "ID",
        "id_number": (request.POST.get("id_number") or "").strip(),
        "email": (request.POST.get("email") or "").strip(),
        "address": (request.POST.get("address") or "").strip(),
        "license_number": (request.POST.get("license_number") or "").strip(),
        "license_issuer": (request.POST.get("license_issuer") or "").strip(),
        "license_issue_date": request.POST.get("license_issue_date") or None,
        "license_expiry_date": request.POST.get("license_expiry_date") or None,
        "notes": (request.POST.get("notes") or "").strip(),
    }


@login_required
def customer_new_page(request):
    if not has_perm(request.user, "customers.manage"):
        return render(request, "errors/403.html", status=403)

    error = ""
    payload = {}
    if request.method == "POST":
        payload = _customer_payload(request)
        if not payload.get("name"):
            error = "Customer name is required."
        else:
            Customer.objects.create(**payload)
            return redirect("customers_page")

    context = {
        "title": "Add Customer",
        "page_title": "Add Customer",
        "customer": payload,
        "is_edit": False,
        "error": error,
    }
    return render(request, "customers/customer_form.html", context)


@login_required
def customer_edit_page(request, customer_id: int):
    if not has_perm(request.user, "customers.manage"):
        return render(request, "errors/403.html", status=403)

    customer = get_object_or_404(Customer, id=customer_id)
    error = ""
    if request.method == "POST":
        payload = _customer_payload(request)
        if not payload.get("name"):
            error = "Customer name is required."
        else:
            for key, value in payload.items():
                setattr(customer, key, value)
            customer.save()
            return redirect("customers_page")

    context = {
        "title": "Edit Customer",
        "page_title": "Edit Customer",
        "customer": customer,
        "is_edit": True,
        "error": error,
    }
    return render(request, "customers/customer_form.html", context)


@login_required
def customer_delete_page(request, customer_id: int):
    if not has_perm(request.user, "customers.manage"):
        return render(request, "errors/403.html", status=403)

    customer = get_object_or_404(Customer, id=customer_id)
    if request.method == "POST":
        customer.delete()
        return redirect("customers_page")

    return render(request, "customers/customer_delete.html", {"customer": customer})


@login_required
def customer_documents_page(request, customer_id: int):
    if not has_perm(request.user, "customers.view"):
        return render(request, "errors/403.html", status=403)
    customer = get_object_or_404(Customer, id=customer_id)
    error = ""

    if request.method == "POST":
        if not has_perm(request.user, "customers.manage"):
            return render(request, "errors/403.html", status=403)
        if not request.FILES.get("file"):
            error = "Please select a file to upload."
        else:
            CustomerDocument.objects.create(
                customer=customer,
                doc_type=request.POST.get("doc_type") or "OTHER",
                file=request.FILES["file"],
                expiry_date=request.POST.get("expiry_date") or None,
                notes=(request.POST.get("notes") or "").strip(),
            )
            return redirect("customer_documents_page", customer_id=customer.id)

    context = {
        "title": "Customer Documents",
        "page_title": "Customer Documents",
        "customer": customer,
        "error": error,
    }
    return render(request, "customers/customer_documents.html", context)


@login_required
def api_customers_list(request):
    if not has_perm(request.user, "customers.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    """
    Frontend expects:
    GET /api/customers/?search=
    and/or name/phone/id_number filters.

    Response:
    { ok: true, results: [ {id, name, phone, id_number, address} ] }
    """
    qs = Customer.objects.all().order_by("-id")

    search = (request.GET.get("search") or "").strip()
    name = (request.GET.get("name") or "").strip()
    phone = (request.GET.get("phone") or "").strip()
    id_number = (request.GET.get("id_number") or "").strip()

    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(phone__icontains=search) | qs.filter(id_number__icontains=search)
    if name:
        qs = qs.filter(name__icontains=name)
    if phone:
        qs = qs.filter(phone__icontains=phone)
    if id_number:
        qs = qs.filter(id_number__icontains=id_number)

    results = []
    for c in qs[:500]:
        results.append({
            "id": c.id,
            "name": getattr(c, "name", ""),
            "phone_number": getattr(c, "phone_number", ""),
            "id_number": getattr(c, "id_number", ""),
            "address": getattr(c, "address", ""),
        })

    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["GET"])
def api_customer_detail(request, customer_id: int):
    if not has_perm(request.user, "customers.view"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    c = get_object_or_404(Customer, id=customer_id)
    return JsonResponse(
        {
            "ok": True,
            "customer": {
                "id": c.id,
                "name": c.name,
                "id_type": c.id_type,
                "id_number": c.id_number,
                "phone_number": c.phone_number,
                "email": c.email,
                "address": c.address,
                "license_number": c.license_number,
                "license_issuer": c.license_issuer,
                "license_issue_date": str(c.license_issue_date) if c.license_issue_date else "",
                "license_expiry_date": str(c.license_expiry_date) if c.license_expiry_date else "",
                "notes": c.notes,
            },
        }
    )


@login_required
@require_http_methods(["POST"])
def api_customer_create(request):
    if not has_perm(request.user, "customers.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    data = _json_body(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "Customer Name is required"}, status=400)

    c = Customer.objects.create(
        name=name,
        phone_number=(data.get("phone_number") or "").strip(),
        id_type=data.get("id_type") or "ID",
        id_number=(data.get("id_number") or "").strip(),
        address=(data.get("address") or "").strip(),
        license_number=(data.get("license_number") or "").strip(),
        license_issuer=(data.get("license_issuer") or "").strip(),
        license_issue_date=data.get("license_issue_date") or None,
        license_expiry_date=data.get("license_expiry_date") or None,
        notes=(data.get("notes") or "").strip(),
    )
    return JsonResponse({"ok": True, "customer_id": c.id})


@login_required
@require_http_methods(["POST"])
def api_customer_update(request, customer_id: int):
    if not has_perm(request.user, "customers.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    c = get_object_or_404(Customer, id=customer_id)
    data = _json_body(request)
    name = (data.get("name") or "").strip()
    if not name:
        return JsonResponse({"ok": False, "error": "Customer Name is required"}, status=400)

    c.name = name
    c.phone_number = (data.get("phone_number") or "").strip()
    c.id_type = data.get("id_type") or c.id_type
    c.id_number = (data.get("id_number") or "").strip()
    c.address = (data.get("address") or "").strip()
    c.license_number = (data.get("license_number") or "").strip()
    c.license_issuer = (data.get("license_issuer") or "").strip()
    c.license_issue_date = data.get("license_issue_date") or None
    c.license_expiry_date = data.get("license_expiry_date") or None
    c.notes = (data.get("notes") or "").strip()
    c.save()
    return JsonResponse({"ok": True})


@login_required
@require_http_methods(["POST"])
def api_customer_delete(request, customer_id: int):
    if not has_perm(request.user, "customers.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    c = get_object_or_404(Customer, id=customer_id)
    c.delete()
    return JsonResponse({"ok": True})


# -------------------------
# Customer documents
# -------------------------
@login_required
@require_http_methods(["GET"])
def api_customer_docs_list(request, customer_id: int):
    c = get_object_or_404(Customer, id=customer_id)
    docs = CustomerDocument.objects.filter(customer=c).order_by("-created_at")
    labels = dict(CustomerDocument.DOC_TYPES)
    results = []
    for d in docs:
        results.append(
            {
                "id": d.id,
                "doc_type": d.doc_type,
                "doc_type_label": labels.get(d.doc_type, d.doc_type),
                "expiry_date": str(d.expiry_date) if d.expiry_date else "",
                "notes": d.notes,
                "url": d.file.url if d.file else "",
            }
        )
    return JsonResponse({"ok": True, "results": results})


@login_required
@require_http_methods(["POST"])
def api_customer_docs_upload(request, customer_id: int):
    c = get_object_or_404(Customer, id=customer_id)
    if not request.FILES.get("file"):
        return JsonResponse({"ok": False, "error": "File is required"}, status=400)
    doc = CustomerDocument.objects.create(
        customer=c,
        doc_type=request.POST.get("doc_type") or "OTHER",
        file=request.FILES["file"],
        expiry_date=request.POST.get("expiry_date") or None,
        notes=(request.POST.get("notes") or "").strip(),
    )
    return JsonResponse({"ok": True, "doc_id": doc.id})


@login_required
@require_http_methods(["POST"])
def api_customer_doc_delete(request, doc_id: int):
    if not has_perm(request.user, "customers.manage"):
        return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)
    d = get_object_or_404(CustomerDocument, id=doc_id)
    d.delete()
    return JsonResponse({"ok": True})