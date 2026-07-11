from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path("vehicles/", views.vehicles_page, name="vehicles_page"),
    path("vehicles/new/", views.vehicle_wizard_start, name="vehicle_wizard_start"),
    path("vehicles/new/details/", views.vehicle_wizard_details, name="vehicle_wizard_details"),
    path("vehicles/new/specs/", views.vehicle_wizard_specs, name="vehicle_wizard_specs"),
    path("vehicles/new/pricing/", views.vehicle_wizard_pricing, name="vehicle_wizard_pricing"),
    path("vehicles/new/documents/", views.vehicle_wizard_documents, name="vehicle_wizard_documents"),
    path("vehicles/<int:vehicle_id>/edit/", views.vehicle_edit_page, name="vehicle_edit_page"),
    path("vehicles/<int:vehicle_id>/delete/", views.vehicle_delete_page, name="vehicle_delete_page"),
    path("vehicles/<int:vehicle_id>/documents/", views.vehicle_documents_page, name="vehicle_documents_page"),
    path("vehicles/<int:vehicle_id>/photos/", views.vehicle_photos_page, name="vehicle_photos_page"),

    # API
    path("api/vehicles/", views.api_vehicles_list, name="api_vehicles_list"),
    path("web-api/vehicles/", views.api_vehicles_list, name="web_api_vehicles_list"),

    path("api/vehicles/create/", views.api_vehicle_create, name="api_vehicle_create"),
    path("web-api/vehicles/create/", views.api_vehicle_create, name="web_api_vehicle_create"),
    path("api/vehicles/<int:vehicle_id>/", views.api_vehicle_detail, name="api_vehicle_detail"),
    path("web-api/vehicles/<int:vehicle_id>/", views.api_vehicle_detail, name="web_api_vehicle_detail"),
    path("api/vehicles/<int:vehicle_id>/update/", views.api_vehicle_update, name="api_vehicle_update"),
    path("web-api/vehicles/<int:vehicle_id>/update/", views.api_vehicle_update, name="web_api_vehicle_update"),
    path("api/vehicles/<int:vehicle_id>/delete/", views.api_vehicle_delete, name="api_vehicle_delete"),
    path("web-api/vehicles/<int:vehicle_id>/delete/", views.api_vehicle_delete, name="web_api_vehicle_delete"),

    path("api/vehicle-brands/", views.api_vehicle_brands, name="api_vehicle_brands"),
    path("web-api/vehicle-brands/", views.api_vehicle_brands, name="web_api_vehicle_brands"),
    path("api/vehicle-brands/create/", views.api_vehicle_brand_create, name="api_vehicle_brand_create"),
    path("web-api/vehicle-brands/create/", views.api_vehicle_brand_create, name="web_api_vehicle_brand_create"),
    path("api/vehicle-models/", views.api_vehicle_models, name="api_vehicle_models"),
    path("web-api/vehicle-models/", views.api_vehicle_models, name="web_api_vehicle_models"),
    path("api/vehicle-models/create/", views.api_vehicle_model_create, name="api_vehicle_model_create"),
    path("web-api/vehicle-models/create/", views.api_vehicle_model_create, name="web_api_vehicle_model_create"),

    path("api/vehicles/<int:vehicle_id>/docs/", views.api_vehicle_docs_list, name="api_vehicle_docs_list"),
    path("web-api/vehicles/<int:vehicle_id>/docs/", views.api_vehicle_docs_list, name="web_api_vehicle_docs_list"),
    path("api/vehicles/<int:vehicle_id>/docs/upload/", views.api_vehicle_docs_upload, name="api_vehicle_docs_upload"),
    path("web-api/vehicles/<int:vehicle_id>/docs/upload/", views.api_vehicle_docs_upload, name="web_api_vehicle_docs_upload"),
    path("api/vehicles/docs/<int:doc_id>/delete/", views.api_vehicle_doc_delete, name="api_vehicle_doc_delete"),
    path("web-api/vehicles/docs/<int:doc_id>/delete/", views.api_vehicle_doc_delete, name="web_api_vehicle_doc_delete"),

    path("api/vehicles/<int:vehicle_id>/photos/", views.api_vehicle_photos_list, name="api_vehicle_photos_list"),
    path("web-api/vehicles/<int:vehicle_id>/photos/", views.api_vehicle_photos_list, name="web_api_vehicle_photos_list"),
    path("api/vehicles/<int:vehicle_id>/photos/upload/", views.api_vehicle_photos_upload, name="api_vehicle_photos_upload"),
    path("web-api/vehicles/<int:vehicle_id>/photos/upload/", views.api_vehicle_photos_upload, name="web_api_vehicle_photos_upload"),
    path("api/vehicles/photos/<int:photo_id>/delete/", views.api_vehicle_photo_delete, name="api_vehicle_photo_delete"),
    path("web-api/vehicles/photos/<int:photo_id>/delete/", views.api_vehicle_photo_delete, name="web_api_vehicle_photo_delete"),
]
