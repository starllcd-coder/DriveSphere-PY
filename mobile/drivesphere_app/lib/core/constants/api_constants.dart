import '../config/app_config.dart';
import 'package:flutter/foundation.dart';

class ApiConstants {
  static String get baseUrl {
    final configured = AppConfig.apiBaseUrl;
    if (!kIsWeb) return configured;

    try {
      final uri = Uri.parse(configured);
      final host = uri.host.toLowerCase();
      final isLocal = host == '127.0.0.1' || host == 'localhost';
      if (!isLocal) return configured;

      final browserHost = Uri.base.host;
      final browserHostLower = browserHost.toLowerCase();
      final browserIsLocal =
          browserHostLower == '127.0.0.1' || browserHostLower == 'localhost';
      if (browserHost.isEmpty || browserIsLocal) return configured;

      return uri.replace(host: browserHost).toString();
    } catch (_) {
      return configured;
    }
  }

  static const String login = "/auth/login/";
  static const String register = "/auth/register/";
  static const String socialAuth = "/auth/social/";
  static const String registerDevice = "/devices/register/";

  static const String vehicles = "/vehicles/";
  static const String vehicleSearch = "/vehicles/search/";

  static const String bookings = "/bookings/";
  static const String createBooking = "/bookings/create/";

  static const String profile = "/profile/";

  static const String documents = "/documents/";
  static const String uploadDocument = "/documents/upload/";

  static const String payments = "/payments/";
  static const String createPayment = "/payments/create/";
  static const String hyperPayCheckout = "/payments/hyperpay/checkout/";
  static const String hyperPayStatus = "/payments/hyperpay/status/";

  static const String notifications = "/notifications/";
}
