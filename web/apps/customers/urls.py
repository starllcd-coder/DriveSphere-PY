from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path("customers/", views.customers_page, name="customers_page"),
    path("customers/new/", views.customer_new_page, name="customer_new_page"),
    path("customers/<int:customer_id>/edit/", views.customer_edit_page, name="customer_edit_page"),
    path("customers/<int:customer_id>/delete/", views.customer_delete_page, name="customer_delete_page"),
    path("customers/<int:customer_id>/documents/", views.customer_documents_page, name="customer_documents_page"),

    # API
    path("api/customers/", views.api_customers_list, name="api_customers_list"),

    path("api/customers/create/", views.api_customer_create, name="api_customer_create"),
    path("api/customers/<int:customer_id>/", views.api_customer_detail, name="api_customer_detail"),
    path("api/customers/<int:customer_id>/update/", views.api_customer_update, name="api_customer_update"),
    path("api/customers/<int:customer_id>/delete/", views.api_customer_delete, name="api_customer_delete"),

    path("api/customers/<int:customer_id>/docs/", views.api_customer_docs_list, name="api_customer_docs_list"),
    path("api/customers/<int:customer_id>/docs/upload/", views.api_customer_docs_upload, name="api_customer_docs_upload"),
    path("api/customers/docs/<int:doc_id>/delete/", views.api_customer_doc_delete, name="api_customer_doc_delete"),
]