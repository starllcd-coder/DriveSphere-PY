from django.urls import path
from . import views

urlpatterns = [
    # ---- PAGES ----
    path("payments/", views.payments_page, name="payments_page"),
    path("payments/new/", views.payment_new_page, name="payment_new_page"),
    path("payments/<int:payment_id>/edit/", views.payment_edit_page, name="payment_edit_page"),
    path("payments/<int:payment_id>/delete/", views.payment_delete_page, name="payment_delete_page"),
    path("payments/refund/", views.refund_new_page, name="refund_new_page"),
    path("print/payments/report/", views.payments_report_print, name="payments_report_print"),

    # ---- API ----
    path("api/payments/", views.api_payments_list, name="api_payments_list"),
    path("api/payments/create/", views.api_payments_create, name="api_payments_create"),
    path("api/refunds/create/", views.api_refunds_create, name="api_refunds_create"),
    path("web-api/payments/", views.api_payments_list, name="web_api_payments_list"),
    path("web-api/payments/create/", views.api_payments_create, name="web_api_payments_create"),
    path("web-api/refunds/create/", views.api_refunds_create, name="web_api_refunds_create"),

    path("api/payments/<int:payment_id>/update/", views.api_payment_update, name="api_payment_update"),
    path("api/payments/<int:payment_id>/void/", views.api_payment_void, name="api_payment_void"),
    path("web-api/payments/<int:payment_id>/update/", views.api_payment_update, name="web_api_payment_update"),
    path("web-api/payments/<int:payment_id>/void/", views.api_payment_void, name="web_api_payment_void"),

    path("api/payments/<int:payment_id>/receipt.pdf", views.api_payment_receipt_pdf, name="api_payment_receipt_pdf"),
    path("api/payments/report.pdf", views.api_payments_report_pdf, name="api_payments_report_pdf"),
    path("web-api/payments/<int:payment_id>/receipt.pdf", views.api_payment_receipt_pdf, name="web_api_payment_receipt_pdf"),
    path("web-api/payments/report.pdf", views.api_payments_report_pdf, name="web_api_payments_report_pdf"),
]
