from django.urls import path
from . import views

urlpatterns = [
    path("api/bookings/<int:booking_id>/invoice.pdf", views.api_booking_invoice_pdf, name="api_booking_invoice_pdf"),
    path("api/bookings/<int:booking_id>/agreement.pdf", views.api_booking_agreement_pdf, name="api_booking_agreement_pdf"),
    path("api/bookings/<int:booking_id>/confirmation.pdf", views.api_booking_confirmation_pdf, name="api_booking_confirmation_pdf"),
    path("api/bookings/<int:booking_id>/quotation.pdf", views.api_booking_quotation_pdf, name="api_booking_quotation_pdf"),
    path("api/bookings/<int:booking_id>/return-report.pdf", views.api_booking_return_report_pdf, name="api_booking_return_report_pdf"),
    path("api/bookings/<int:booking_id>/handover-checklist.pdf", views.api_booking_handover_checklist_pdf, name="api_booking_handover_checklist_pdf"),

    path("print/bookings/<int:booking_id>/invoice/", views.booking_invoice_print, name="booking_invoice_print"),
    path("print/bookings/<int:booking_id>/agreement/", views.booking_agreement_print, name="booking_agreement_print"),
    path("print/bookings/<int:booking_id>/confirmation/", views.booking_confirmation_print, name="booking_confirmation_print"),
    path("print/bookings/<int:booking_id>/quotation/", views.booking_quotation_print, name="booking_quotation_print"),
    path("print/bookings/<int:booking_id>/return-report/", views.booking_return_report_print, name="booking_return_report_print"),
    path("print/bookings/<int:booking_id>/handover-checklist/", views.booking_handover_checklist_print, name="booking_handover_checklist_print"),
    path("print/payments/<int:payment_id>/receipt/", views.payment_receipt_print, name="payment_receipt_print"),

    path("print/bookings/<int:booking_id>/invoice.pdf", views.api_booking_invoice_pdf, name="booking_invoice_pdf"),
    path("print/bookings/<int:booking_id>/agreement.pdf", views.api_booking_agreement_pdf, name="booking_agreement_pdf"),
    path("print/bookings/<int:booking_id>/confirmation.pdf", views.api_booking_confirmation_pdf, name="booking_confirmation_pdf"),
    path("print/bookings/<int:booking_id>/quotation.pdf", views.api_booking_quotation_pdf, name="booking_quotation_pdf"),
    path("print/bookings/<int:booking_id>/return-report.pdf", views.api_booking_return_report_pdf, name="booking_return_report_pdf"),
    path("print/bookings/<int:booking_id>/handover-checklist.pdf", views.api_booking_handover_checklist_pdf, name="booking_handover_checklist_pdf"),
    path("print/payments/<int:payment_id>/receipt.pdf", views.payment_receipt_print, name="payment_receipt_pdf"),
]