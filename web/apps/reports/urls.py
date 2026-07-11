from django.urls import path
from . import views

urlpatterns = [
    # ---- PAGES ----
    path("reports/", views.reports_page, name="reports_page"),

    # ---- API ----
    path("api/reports/overview/", views.api_reports_overview, name="api_reports_overview"),
    path("api/reports/overview/table/", views.api_reports_overview_table, name="api_reports_overview_table"),
    path("api/reports/revenue/", views.api_reports_revenue, name="api_reports_revenue"),
    path("api/reports/financial/", views.api_reports_financial, name="api_reports_financial"),
    path("api/reports/fleet/", views.api_reports_fleet, name="api_reports_fleet"),
    path("api/reports/maintenance/", views.api_reports_maintenance, name="api_reports_maintenance"),
    path("api/reports/customers/", views.api_reports_customers, name="api_reports_customers"),
    path("api/reports/insights/", views.api_reports_insights, name="api_reports_insights"),
    path("api/reports/anomalies/", views.api_reports_anomalies, name="api_reports_anomalies"),
    path("api/reports/anomalies/<int:anomaly_id>/resolve/", views.api_reports_anomaly_resolve, name="api_reports_anomaly_resolve"),
    path("api/reports/accounting/export/", views.api_reports_accounting_export, name="api_reports_accounting_export"),

    path("api/reports/revenue/table/", views.api_reports_revenue_table, name="api_reports_revenue_table"),
    path("api/reports/financial/table/", views.api_reports_financial_table, name="api_reports_financial_table"),
    path("api/reports/fleet/table/", views.api_reports_fleet_table, name="api_reports_fleet_table"),
    path("api/reports/maintenance/table/", views.api_reports_maintenance_table, name="api_reports_maintenance_table"),
    path("api/reports/customers/table/", views.api_reports_customers_table, name="api_reports_customers_table"),

    path("api/reports/overview.pdf", views.api_reports_overview_pdf, name="api_reports_overview_pdf"),
    path("api/reports/revenue.pdf", views.api_reports_revenue_pdf, name="api_reports_revenue_pdf"),
    path("api/reports/financial.pdf", views.api_reports_financial_pdf, name="api_reports_financial_pdf"),
    path("api/reports/fleet.pdf", views.api_reports_fleet_pdf, name="api_reports_fleet_pdf"),
    path("api/reports/maintenance.pdf", views.api_reports_maintenance_pdf, name="api_reports_maintenance_pdf"),
    path("api/reports/customers.pdf", views.api_reports_customers_pdf, name="api_reports_customers_pdf"),

    path("print/reports/overview/", views.reports_overview_print, name="reports_overview_print"),
    path("print/reports/revenue/", views.reports_revenue_print, name="reports_revenue_print"),
    path("print/reports/financial/", views.reports_financial_print, name="reports_financial_print"),
    path("print/reports/fleet/", views.reports_fleet_print, name="reports_fleet_print"),
    path("print/reports/maintenance/", views.reports_maintenance_print, name="reports_maintenance_print"),
    path("print/reports/customers/", views.reports_customers_print, name="reports_customers_print"),
]
