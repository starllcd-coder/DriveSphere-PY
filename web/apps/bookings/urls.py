from django.urls import path

from . import views
from . import page_views

urlpatterns = [
    # Pages
    path("bookings/", page_views.bookings_page, name="bookings_page"),
    path("bookings/upcoming/", page_views.upcoming_bookings_page, name="upcoming_bookings_page"),
    path("bookings/new/", page_views.booking_wizard_page, name="booking_wizard_page"),
    path("bookings/new/customer/", page_views.booking_wizard_customer, name="booking_wizard_customer"),
    path("bookings/new/driver/", page_views.booking_wizard_driver, name="booking_wizard_driver"),
    path("bookings/new/dates/", page_views.booking_wizard_dates, name="booking_wizard_dates"),
    path("bookings/new/vehicle/", page_views.booking_wizard_vehicle, name="booking_wizard_vehicle"),
    path("bookings/new/extras/", page_views.booking_wizard_extras, name="booking_wizard_extras"),
    path("bookings/new/pricing/", page_views.booking_wizard_pricing, name="booking_wizard_pricing"),
    path("bookings/new/signature/", page_views.booking_wizard_signature, name="booking_wizard_signature"),
    path("bookings/new/handover/", page_views.booking_wizard_handover, name="booking_wizard_handover"),
    path("bookings/new/documents/", page_views.booking_wizard_documents, name="booking_wizard_documents"),
    path("bookings/new/finish/", page_views.booking_wizard_finish, name="booking_wizard_finish"),
    path("bookings/<int:booking_id>/", page_views.booking_detail_page, name="booking_detail_page"),
    path("bookings/<int:booking_id>/edit/", page_views.booking_edit_page, name="booking_edit_page"),
    path("bookings/<int:booking_id>/edit/customer/", page_views.booking_edit_customer, name="booking_edit_customer"),
    path("bookings/<int:booking_id>/edit/driver/", page_views.booking_edit_driver, name="booking_edit_driver"),
    path("bookings/<int:booking_id>/edit/dates/", page_views.booking_edit_dates, name="booking_edit_dates"),
    path("bookings/<int:booking_id>/edit/vehicle/", page_views.booking_edit_vehicle, name="booking_edit_vehicle"),
    path("bookings/<int:booking_id>/edit/extras/", page_views.booking_edit_extras, name="booking_edit_extras"),
    path("bookings/<int:booking_id>/edit/pricing/", page_views.booking_edit_pricing, name="booking_edit_pricing"),
    path("bookings/<int:booking_id>/edit/signature/", page_views.booking_edit_signature, name="booking_edit_signature"),
    path("bookings/<int:booking_id>/edit/handover/", page_views.booking_edit_handover, name="booking_edit_handover"),
    path("bookings/<int:booking_id>/edit/documents/", page_views.booking_edit_documents, name="booking_edit_documents"),
    path("bookings/<int:booking_id>/edit/finish/", page_views.booking_edit_finish, name="booking_edit_finish"),
    path("bookings/<int:booking_id>/delete/", page_views.booking_delete_page, name="booking_delete_page"),
    path("bookings/<int:booking_id>/return/", page_views.booking_return_page, name="booking_return_page"),

    # APIs
    path("api/bookings/", views.api_bookings_list, name="api_bookings_list"),
    path("api/bookings/create/", views.api_booking_create, name="api_booking_create"),
    path("api/bookings/<int:booking_id>/update/", views.api_booking_update, name="api_booking_update"),
    path("api/bookings/<int:booking_id>/delete/", views.api_booking_delete, name="api_booking_delete"),
    path("web-api/bookings/", views.api_bookings_list, name="web_api_bookings_list"),
    path("web-api/bookings/create/", views.api_booking_create, name="web_api_booking_create"),
    path("web-api/bookings/<int:booking_id>/update/", views.api_booking_update, name="web_api_booking_update"),
    path("web-api/bookings/<int:booking_id>/delete/", views.api_booking_delete, name="web_api_booking_delete"),

    path("api/availability/", views.api_vehicle_availability, name="api_vehicle_availability"),
    path("web-api/availability/", views.api_vehicle_availability, name="web_api_vehicle_availability"),

    path("api/bookings/<int:booking_id>/activate/", views.api_booking_activate, name="api_booking_activate"),
    path("api/bookings/<int:booking_id>/extend/", views.api_booking_extend, name="api_booking_extend"),
    path("api/bookings/<int:booking_id>/checkout/", views.api_booking_checkout, name="api_booking_checkout"),
    path("api/bookings/<int:booking_id>/return/", views.api_booking_return, name="api_booking_return"),
    path("web-api/bookings/<int:booking_id>/activate/", views.api_booking_activate, name="web_api_booking_activate"),
    path("web-api/bookings/<int:booking_id>/extend/", views.api_booking_extend, name="web_api_booking_extend"),
    path("web-api/bookings/<int:booking_id>/checkout/", views.api_booking_checkout, name="web_api_booking_checkout"),
    path("web-api/bookings/<int:booking_id>/return/", views.api_booking_return, name="web_api_booking_return"),
    path("api/bookings/<int:booking_id>/return/photos/", views.api_booking_return_damage_photos_list, name="api_booking_return_damage_photos_list"),
    path("api/bookings/<int:booking_id>/return/photos/upload/", views.api_booking_return_damage_photos_upload, name="api_booking_return_damage_photos_upload"),
    path("api/bookings/<int:booking_id>/return/photos/<int:attachment_id>/delete/", views.api_booking_return_damage_photos_delete, name="api_booking_return_damage_photos_delete"),
    path("web-api/bookings/<int:booking_id>/return/photos/", views.api_booking_return_damage_photos_list, name="web_api_booking_return_damage_photos_list"),
    path("web-api/bookings/<int:booking_id>/return/photos/upload/", views.api_booking_return_damage_photos_upload, name="web_api_booking_return_damage_photos_upload"),
    path("web-api/bookings/<int:booking_id>/return/photos/<int:attachment_id>/delete/", views.api_booking_return_damage_photos_delete, name="web_api_booking_return_damage_photos_delete"),
]
