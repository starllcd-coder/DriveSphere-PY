from django.urls import include, path

urlpatterns = [

    path(
        "auth/",
        include("api.auth.urls")
    ),

    path(
        "vehicles/",
        include("api.vehicles.urls")
    ),

    path(
        "bookings/",
        include("api.bookings.urls")
    ),

    path(
        "profile/",
        include("api.profile.urls")
    ),

    path(
        "documents/",
        include("api.documents.urls")
    ),

    path(
        "payments/",
        include("api.payments.urls")
    ),

    path(
        "notifications/",
        include("api.notifications.urls")
    ),

    path(
        "support/",
        include("api.support.urls")
    ),

    path(
        "devices/",
        include("api.devices.urls")
    ),

    path(
        "integrations/",
        include("api.integrations.urls")
    ),

    path(
        "internal/",
        include("api.internal.urls")
    ),

]
