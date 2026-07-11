class ApiPaths {
  static const login = '/auth/login/';
  static const bootstrap = '/internal/bootstrap/';
  static const employees = '/internal/employees/';
  static const customers = '/internal/customers/';
  static const maintenance = '/internal/maintenance/';
  static const payments = '/internal/payments/';
  static const createRefund = '/internal/payments/refunds/create/';
  static const reportsOverview = '/internal/reports/overview/';
  static const dashboardKpis = '/internal/dashboard/kpis/';
  static const reportsFinancial = '/internal/reports/financial/';
  static const reportsFleet = '/internal/reports/fleet/';
  static const reportsCustomers = '/internal/reports/customers/';
  static const reportsMaintenance = '/internal/reports/maintenance/';
  static const bookings = '/internal/bookings/';
  static const bookingAvailability = '/internal/bookings/availability/';
  static const vehicles = '/vehicles/';
  static const notifications = '/notifications/';
  static String notificationRead(int id) => '/notifications/$id/read/';
  static String notificationDelete(int id) => '/notifications/$id/delete/';
  static String bookingDetail(int bookingId) =>
      '/internal/bookings/$bookingId/';
  static String bookingActivate(int bookingId) =>
      '/internal/bookings/$bookingId/activate/';
  static String bookingExtend(int bookingId) =>
      '/internal/bookings/$bookingId/extend/';
  static String bookingCheckout(int bookingId) =>
      '/internal/bookings/$bookingId/checkout/';
  static String bookingReturn(int bookingId) =>
      '/internal/bookings/$bookingId/return/';
  static String bookingCancel(int bookingId) =>
      '/internal/bookings/$bookingId/cancel/';
}
