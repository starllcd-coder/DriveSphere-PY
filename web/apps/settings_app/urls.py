from django.urls import path
from . import views

urlpatterns = [
    # ---- PAGES (single-page tabs UI) ----
    path("", views.settings_page, name="settings_page"),
    path("general/", views.settings_page, name="settings_general_page"),
    path("employees/", views.settings_page, name="settings_employees_page"),
    path("backup/", views.settings_page, name="settings_backup_page"),
    path("database/", views.settings_page, name="settings_database_page"),
    path("about/", views.settings_page, name="settings_about_page"),

    # ---- API (DB tab) ----
    path("api/db/profile/", views.api_db_profile_get, name="api_db_profile_get"),
    path("api/db/profile/save/", views.api_db_profile_save, name="api_db_profile_save"),
    path("api/db/test/", views.api_db_test_connection, name="api_db_test_connection"),
    path("api/db/migrate/", views.api_db_migrate_placeholder, name="api_db_migrate_placeholder"),

    path("api/business/", views.api_business_profile_get, name="api_business_profile_get"),
    path("api/business/save/", views.api_business_profile_save, name="api_business_profile_save"),
    path("api/business/logo/", views.api_business_logo_upload, name="api_business_logo_upload"),

    path("api/branches/", views.api_branches_list, name="api_branches_list"),
    path("api/branches/create/", views.api_branch_create, name="api_branch_create"),
    path("api/branches/<int:branch_id>/update/", views.api_branch_update, name="api_branch_update"),
    path("api/branches/<int:branch_id>/delete/", views.api_branch_delete, name="api_branch_delete"),

    path("api/doc-numbering/", views.api_doc_numbering_list, name="api_doc_numbering_list"),
    path("api/doc-numbering/save/", views.api_doc_numbering_save, name="api_doc_numbering_save"),

    path("api/exchange-rates/", views.api_exchange_rates_get, name="api_exchange_rates_get"),
    path("api/exchange-rates/update/", views.api_exchange_rates_update, name="api_exchange_rates_update"),

    path("api/backup/export/", views.api_backup_export, name="api_backup_export"),
    path("api/backup/restore/", views.api_backup_restore, name="api_backup_restore"),
    path("api/backup/reset/", views.api_backup_reset, name="api_backup_reset"),

    path("api/employees/", views.api_employees_list, name="api_employees_list"),
    path("api/employees/create/", views.api_employee_create, name="api_employee_create"),
    path("api/employees/<int:user_id>/update/", views.api_employee_update, name="api_employee_update"),
    path("api/employees/<int:user_id>/delete/", views.api_employee_delete, name="api_employee_delete"),

    path("api/notifications/", views.api_notifications_list, name="api_notifications_list"),
    path("api/notifications/clear/", views.api_notifications_clear, name="api_notifications_clear"),
    path("api/notifications/dismiss/", views.api_notifications_dismiss, name="api_notifications_dismiss"),
    path("api/notifications/snooze/", views.api_notifications_snooze, name="api_notifications_snooze"),
    path("api/notifications/sync/", views.api_notifications_sync, name="api_notifications_sync"),
    path("api/audit-logs/", views.api_audit_logs_list, name="api_audit_logs_list"),
    path("api/language/", views.api_language_set, name="api_language_set"),
]
