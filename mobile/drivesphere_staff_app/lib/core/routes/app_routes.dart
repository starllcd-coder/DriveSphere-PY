import 'package:flutter/material.dart';

import '../../features/auth/branch_selector_screen.dart';
import '../../features/auth/login_screen.dart';
import '../../features/bookings/booking_detail_screen.dart';
import '../../features/bookings/booking_wizard_screen.dart';
import '../../features/bookings/bookings_screen.dart';
import '../../features/customers/customers_screen.dart';
import '../../features/dashboard/accountant_dashboard_screen.dart';
import '../../features/dashboard/admin_dashboard_screen.dart';
import '../../features/dashboard/agent_dashboard_screen.dart';
import '../../features/dashboard/mechanic_dashboard_screen.dart';
import '../../features/employees/employees_screen.dart';
import '../../features/maintenance/maintenance_screen.dart';
import '../../features/notifications/notifications_screen.dart';
import '../../features/payments/payments_screen.dart';
import '../../features/profile/profile_screen.dart';
import '../../features/reports/reports_overview_screen.dart';
import '../../features/settings/branches_screen.dart';
import '../../features/shell/staff_shell_screen.dart';
import '../../features/splash/splash_screen.dart';
import '../../features/sync/sync_center_screen.dart';
import '../../features/vehicles/vehicles_screen.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/permission_gate.dart';

class AppRoutes {
  static const splash = '/splash';
  static const login = '/login';
  static const branchSelector = '/branch-selector';
  static const shell = '/shell';

  static const bookings = '/bookings';
  static const bookingDetail = '/booking-detail';
  static const bookingWizard = '/booking-wizard';
  static const customers = '/customers';
  static const maintenance = '/maintenance';
  static const payments = '/payments';
  static const employees = '/employees';
  static const reports = '/reports';
  static const branches = '/branches';
  static const notifications = '/notifications';
  static const profile = '/profile';
  static const syncCenter = '/sync-center';
  static const vehicles = '/vehicles';

  static Route<dynamic> onGenerateRoute(RouteSettings settings) {
    switch (settings.name) {
      case splash:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
      case login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());
      case branchSelector:
        final payload = settings.arguments as StaffBootstrapPayload;
        return MaterialPageRoute(
          builder: (_) => BranchSelectorScreen(payload: payload),
        );
      case shell:
        final payload = settings.arguments as StaffBootstrapPayload;
        return MaterialPageRoute(
          builder: (_) => StaffShellScreen(payload: payload),
        );
      case bookings:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['bookings.view'],
            child: BookingsScreen(),
          ),
        );
      case bookingDetail:
        final bookingId = settings.arguments as int;
        return MaterialPageRoute(
          builder: (_) => PermissionGate(
            anyOf: const ['bookings.view'],
            child: BookingDetailScreen(bookingId: bookingId),
          ),
        );
      case bookingWizard:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['bookings.create'],
            child: BookingWizardScreen(),
          ),
        );
      case customers:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['customers.view', 'customers.manage'],
            child: CustomersScreen(),
          ),
        );
      case maintenance:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['maintenance.view'],
            child: MaintenanceScreen(),
          ),
        );
      case payments:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['payments.view'],
            child: PaymentsScreen(),
          ),
        );
      case vehicles:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['fleet.view', 'fleet.manage'],
            child: VehiclesScreen(),
          ),
        );
      case employees:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['employees.manage'],
            child: EmployeesScreen(),
          ),
        );
      case reports:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: [
              'reports.view',
              'reports.view_financial',
              'reports.view_limited',
              'reports.view_maintenance',
            ],
            child: ReportsOverviewScreen(),
          ),
        );
      case branches:
        return MaterialPageRoute(
          builder: (_) => const PermissionGate(
            anyOf: ['settings.manage'],
            child: BranchesScreen(),
          ),
        );
      case notifications:
        return MaterialPageRoute(builder: (_) => const NotificationsScreen());
      case profile:
        return MaterialPageRoute(builder: (_) => const ProfileScreen());
      case syncCenter:
        return MaterialPageRoute(builder: (_) => const SyncCenterScreen());
      default:
        return MaterialPageRoute(builder: (_) => const SplashScreen());
    }
  }

  static Widget dashboardByRole(String roleCode) {
    switch (roleCode) {
      case 'ADMIN':
      case 'MANAGER':
        return const AdminDashboardScreen();
      case 'AGENT':
        return const AgentDashboardScreen();
      case 'MECHANIC':
        return const MechanicDashboardScreen();
      case 'ACCOUNTANT':
        return const AccountantDashboardScreen();
      default:
        return const AgentDashboardScreen();
    }
  }
}
