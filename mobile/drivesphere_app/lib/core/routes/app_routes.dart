import 'package:flutter/material.dart';

import '../../features/auth/login_screen.dart';
import '../../features/auth/register_screen.dart';
import '../../features/bookings/booking_history_screen.dart';
import '../../features/bookings/booking_screen.dart';
import '../../features/bookings/booking_cart_screen.dart';
import '../../features/dashboard/app_shell_screen.dart';
import '../../features/documents/documents_screen.dart';
import '../../features/favorites/favorites_screen.dart';
import '../../features/notifications/notifications_screen.dart';
import '../../features/onboarding/country_selection_screen.dart';
import '../../features/payments/payments_screen.dart';
import '../../features/profile/profile_screen.dart';
import '../../features/settings/settings_screen.dart';
import '../../features/splash/splash_screen.dart';
import '../../features/support/support_screen.dart';
import '../../features/reviews/review_screen.dart';
import '../../features/vehicles/compare_screen.dart';
import '../../features/vehicles/vehicle_detail_screen.dart';
import '../../features/vehicles/vehicle_list_screen.dart';
import '../../features/vehicles/vehicle_map_screen.dart';
import '../../features/vehicles/vehicle_search_screen.dart';
import '../../models/vehicle_model.dart';

class AppRoutes {
  static const String appShell = '/app-shell';
  static const String splash = '/splash';
  static const String login = '/login';
  static const String dashboard = '/dashboard';
  static const String register = '/register';
  static const String vehicles = '/vehicles';
  static const String vehicleDetail = '/vehicle-detail';
  static const String vehicleSearch = '/vehicle-search';
  static const String vehicleMap = '/vehicle-map';
  static const String compare = '/compare';
  static const String favorites = '/favorites';
  static const String booking = '/booking';
  static const String bookingHistory = '/booking-history';
  static const String bookingCart = '/booking-cart';
  static const String payments = '/payments';
  static const String documents = '/documents';
  static const String notifications = '/notifications';
  static const String profile = '/profile';
  static const String settings = '/settings';
  static const String support = '/support';
  static const String reviews = '/reviews';
  static const String countrySelection = '/country-selection';

  static Route<dynamic> onGenerateRoute(RouteSettings routeSettings) {
    final routeName = _normalizeRouteName(routeSettings.name);

    switch (routeName) {
      case '/':
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());

      case countrySelection:
        return MaterialPageRoute(
            builder: (_) => const CountrySelectionScreen());

      case login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());

      case register:
        return MaterialPageRoute(builder: (_) => const RegisterScreen());

      case appShell:
        return MaterialPageRoute(builder: (_) => const AppShellScreen());

      case vehicles:
        return MaterialPageRoute(builder: (_) => const VehicleListScreen());

      case vehicleSearch:
        final args = routeSettings.arguments as Map<String, dynamic>?;
        final company = args?['company']?.toString();
        return MaterialPageRoute(
          builder: (_) => VehicleSearchScreen(initialCompany: company),
        );

      case vehicleMap:
        final vehicles = (routeSettings.arguments as List<VehicleModel>?) ??
            const <VehicleModel>[];
        return MaterialPageRoute(
          builder: (_) => VehicleMapScreen(vehicles: vehicles),
        );

      case vehicleDetail:
        final vehicle = routeSettings.arguments as VehicleModel;
        return MaterialPageRoute(
          builder: (_) => VehicleDetailScreen(vehicle: vehicle),
        );

      case compare:
        return MaterialPageRoute(builder: (_) => const CompareScreen());

      case favorites:
        return MaterialPageRoute(builder: (_) => const FavoritesScreen());

      case booking:
        final vehicle = routeSettings.arguments as VehicleModel;
        return MaterialPageRoute(
          builder: (_) => BookingScreen(vehicle: vehicle),
        );

      case bookingHistory:
        return MaterialPageRoute(builder: (_) => const BookingHistoryScreen());

      case bookingCart:
        return MaterialPageRoute(builder: (_) => const BookingCartScreen());

      case payments:
        return MaterialPageRoute(builder: (_) => const PaymentsScreen());

      case documents:
        return MaterialPageRoute(builder: (_) => const DocumentsScreen());

      case notifications:
        return MaterialPageRoute(builder: (_) => const NotificationsScreen());

      case profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());

      case settings:
        return MaterialPageRoute(builder: (_) => const SettingsScreen());

      case support:
        return MaterialPageRoute(builder: (_) => const SupportScreen());

      case reviews:
        final vehicle = routeSettings.arguments as VehicleModel;
        return MaterialPageRoute(
          builder: (_) => ReviewScreen(vehicle: vehicle),
        );

      default:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
    }
  }

  static String _normalizeRouteName(String? rawName) {
    var name = (rawName ?? '').trim();
    if (name.isEmpty) return splash;
    name = name.split('?').first.split('#').first;
    if (name.length > 1 && name.endsWith('/')) {
      name = name.substring(0, name.length - 1);
    }
    return name.isEmpty ? splash : name;
  }
}
