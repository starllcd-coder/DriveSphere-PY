import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../core/theme/app_theme.dart';
import '../../services/staff_api_service.dart';
import '../../widgets/brand_background.dart';
import '../../widgets/glass_panel.dart';
import '../notifications/notifications_screen.dart';
import '../profile/profile_screen.dart';

class StaffShellScreen extends StatefulWidget {
  final StaffBootstrapPayload payload;

  const StaffShellScreen({super.key, required this.payload});

  @override
  State<StaffShellScreen> createState() => _StaffShellScreenState();
}

class _StaffShellScreenState extends State<StaffShellScreen> {
  final _api = StaffApiService();
  late StaffBootstrapPayload _payload;
  int _index = 0;
  bool _switchingBranch = false;
  int _pendingQueueCount = 0;

  @override
  void initState() {
    super.initState();
    _payload = widget.payload;
    _refreshPendingCount();
  }

  bool _can(String perm) => _payload.profile.permissions.contains(perm);

  List<Widget> _pages() {
    final profile = _payload.profile;
    return [
      AppRoutes.dashboardByRole(profile.roleCode),
      _ModulesPage(
        canBookings: _can('bookings.view'),
        canCustomers: _can('customers.view') || _can('customers.manage'),
        canMaintenance: _can('maintenance.view'),
        canPayments: _can('payments.view'),
        canFleet: _can('fleet.view') || _can('fleet.manage'),
        canEmployees: _can('employees.manage'),
        canReports: _can('reports.view') ||
            _can('reports.view_financial') ||
            _can('reports.view_limited') ||
            _can('reports.view_maintenance'),
      ),
      const NotificationsScreen(showBackButton: false),
      const ProfileScreen(showBackButton: false),
    ];
  }

  Future<void> _logout() async {
    await _api.logout();
    if (!mounted) return;
    Navigator.pushNamedAndRemoveUntil(
        context, AppRoutes.login, (route) => false);
  }

  Future<void> _showBranchSwitcher() async {
    final branches = _payload.branches;
    if (branches.length <= 1 || _switchingBranch) return;

    final selected = await showModalBottomSheet<int>(
      context: context,
      builder: (context) => ListView.separated(
        shrinkWrap: true,
        itemCount: branches.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (_, index) {
          final branch = branches[index];
          final currentId = _payload.activeBranch?.id;
          return ListTile(
            title: Text(branch.name),
            subtitle: Text(branch.code),
            trailing: currentId == branch.id
                ? const Icon(Icons.check_circle_outline,
                    color: AppColors.primary)
                : null,
            onTap: () => Navigator.pop(context, branch.id),
          );
        },
      ),
    );
    if (selected == null) return;
    if (_payload.activeBranch?.id == selected) return;

    setState(() => _switchingBranch = true);
    try {
      final nextPayload = await _api.fetchBootstrap(branchId: selected);
      if (!mounted) return;
      setState(() => _payload = nextPayload);
      await _refreshPendingCount();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
            content: Text(
                'Switched to ${nextPayload.activeBranch?.name ?? 'branch'}')),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    } finally {
      if (mounted) setState(() => _switchingBranch = false);
    }
  }

  Future<void> _refreshPendingCount() async {
    final count = await _api.pendingOfflineActionsCount();
    if (!mounted) return;
    setState(() => _pendingQueueCount = count);
  }

  Future<void> _syncQueuedActions() async {
    try {
      final result = await _api.syncOfflineQueue();
      await _refreshPendingCount();
      if (!mounted) return;
      final synced = result['synced'] ?? 0;
      final text = _pendingQueueCount == 0
          ? 'All queued actions synced. ($synced action(s))'
          : 'Synced $synced action(s). Remaining: $_pendingQueueCount';
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(text)));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
      );
    }
  }

  Widget _drawerNavTile({
    required String label,
    required IconData icon,
    required VoidCallback onTap,
    String? subtitle,
  }) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xB8FFFFFF),
            Color(0x73FFFFFF),
          ],
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0x1423344A)),
        boxShadow: const [
          BoxShadow(
            color: Color(0x1423344A),
            blurRadius: 18,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
        leading: Container(
          width: 34,
          height: 34,
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [Color(0xF5FFFFFF), Color(0xADFFFFFF)],
            ),
            border: Border.all(color: const Color(0x1A23344A)),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, size: 19, color: AppColors.primary),
        ),
        title: Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            color: AppColors.text,
          ),
        ),
        subtitle: subtitle == null
            ? null
            : Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: AppColors.textMuted,
                ),
              ),
        trailing: const Icon(
          Icons.chevron_right_rounded,
          color: AppColors.textMuted,
        ),
        onTap: () {
          Navigator.of(context).pop();
          onTap();
        },
      ),
    );
  }

  List<Widget> _drawerItems() {
    final items = <Widget>[
      const Padding(
        padding: EdgeInsets.fromLTRB(16, 10, 16, 6),
        child: Text(
          'Navigation',
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            letterSpacing: 0.4,
            color: AppColors.textMuted,
          ),
        ),
      ),
    ];
    if (_can('bookings.view')) {
      items.add(
        _drawerNavTile(
          label: 'Bookings',
          icon: Icons.calendar_month_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.bookings),
        ),
      );
    }
    if (_can('customers.view') || _can('customers.manage')) {
      items.add(
        _drawerNavTile(
          label: 'Customers',
          icon: Icons.group_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.customers),
        ),
      );
    }
    if (_can('maintenance.view')) {
      items.add(
        _drawerNavTile(
          label: 'Maintenance',
          icon: Icons.build_circle_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.maintenance),
        ),
      );
    }
    if (_can('payments.view')) {
      items.add(
        _drawerNavTile(
          label: 'Payments',
          icon: Icons.account_balance_wallet_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.payments),
        ),
      );
    }
    if (_can('fleet.view') || _can('fleet.manage')) {
      items.add(
        _drawerNavTile(
          label: 'Vehicles',
          icon: Icons.directions_car_filled_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.vehicles),
        ),
      );
    }
    if (_can('employees.manage')) {
      items.add(
        _drawerNavTile(
          label: 'Employees',
          icon: Icons.badge_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.employees),
        ),
      );
    }
    if (_can('reports.view') ||
        _can('reports.view_financial') ||
        _can('reports.view_limited') ||
        _can('reports.view_maintenance')) {
      items.add(
        _drawerNavTile(
          label: 'Reports',
          icon: Icons.analytics_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.reports),
        ),
      );
    }
    if (_can('settings.manage')) {
      items.add(
        _drawerNavTile(
          label: 'Branches',
          icon: Icons.account_tree_outlined,
          onTap: () => Navigator.pushNamed(context, AppRoutes.branches),
        ),
      );
    }
    items.add(
      _drawerNavTile(
        label: 'Sync Center',
        icon: Icons.sync_rounded,
        subtitle: 'Queued actions: $_pendingQueueCount',
        onTap: () =>
            Navigator.pushNamed(context, AppRoutes.syncCenter).then((_) {
          _refreshPendingCount();
        }),
      ),
    );
    return items;
  }

  @override
  Widget build(BuildContext context) {
    final activeBranch = _payload.activeBranch;
    final companyName =
        _payload.companyName.isEmpty ? 'DriveSphere' : _payload.companyName;
    final companyLogo = _payload.companyLogoUrl.isEmpty
        ? const AssetImage('assets/images/logo.png') as ImageProvider
        : NetworkImage(_payload.companyLogoUrl);

    return Scaffold(
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Text('$companyName Workspace'),
        actions: [
          IconButton(
            onPressed: _syncQueuedActions,
            icon: Badge(
              label: Text('$_pendingQueueCount'),
              isLabelVisible: _pendingQueueCount > 0,
              child: const Icon(Icons.cloud_sync_outlined),
            ),
            tooltip: 'Sync Offline Queue',
          ),
          if (_payload.branches.length > 1)
            IconButton(
              onPressed: _switchingBranch ? null : _showBranchSwitcher,
              icon: _switchingBranch
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.account_tree_outlined),
              tooltip: 'Switch Branch',
            ),
          IconButton(
            onPressed: _logout,
            icon: const Icon(Icons.logout_rounded),
          ),
        ],
      ),
      drawer: Drawer(
        backgroundColor: AppColors.surface,
        child: ListView(
          padding: EdgeInsets.zero,
          children: [
            DrawerHeader(
              decoration: const BoxDecoration(color: AppColors.primaryDark),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 18,
                        backgroundColor: Colors.white,
                        backgroundImage: companyLogo,
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          '$companyName Workspace',
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(
                    activeBranch == null ? 'No branch' : activeBranch.name,
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 15,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            ),
            ..._drawerItems(),
          ],
        ),
      ),
      body: BrandBackground(
        child: SafeArea(
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 1160),
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 8),
                child: GlassPanel(
                  padding: const EdgeInsets.all(10),
                  child: _pages()[_index],
                ),
              ),
            ),
          ),
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.fromLTRB(12, 0, 12, 10),
        child: ClipRRect(
          borderRadius: BorderRadius.circular(18),
          child: NavigationBar(
            backgroundColor: AppColors.surface,
            selectedIndex: _index,
            destinations: const [
              NavigationDestination(
                  icon: Icon(Icons.dashboard_outlined), label: 'Home'),
              NavigationDestination(
                  icon: Icon(Icons.work_outline), label: 'Modules'),
              NavigationDestination(
                  icon: Icon(Icons.notifications_none), label: 'Alerts'),
              NavigationDestination(
                  icon: Icon(Icons.person_outline), label: 'Profile'),
            ],
            onDestinationSelected: (value) => setState(() => _index = value),
          ),
        ),
      ),
    );
  }
}

class _ModulesPage extends StatelessWidget {
  final bool canBookings;
  final bool canCustomers;
  final bool canMaintenance;
  final bool canPayments;
  final bool canEmployees;
  final bool canReports;
  final bool canFleet;

  const _ModulesPage({
    required this.canBookings,
    required this.canCustomers,
    required this.canMaintenance,
    required this.canPayments,
    required this.canEmployees,
    required this.canReports,
    required this.canFleet,
  });

  @override
  Widget build(BuildContext context) {
    final items = <_ModuleItem>[
      if (canBookings)
        const _ModuleItem(
          label: 'Bookings',
          route: AppRoutes.bookings,
          icon: Icons.calendar_month_outlined,
        ),
      if (canCustomers)
        const _ModuleItem(
          label: 'Customers',
          route: AppRoutes.customers,
          icon: Icons.group_outlined,
        ),
      if (canMaintenance)
        const _ModuleItem(
          label: 'Maintenance',
          route: AppRoutes.maintenance,
          icon: Icons.build_circle_outlined,
        ),
      if (canPayments)
        const _ModuleItem(
          label: 'Payments',
          route: AppRoutes.payments,
          icon: Icons.account_balance_wallet_outlined,
        ),
      if (canFleet)
        const _ModuleItem(
          label: 'Vehicles',
          route: AppRoutes.vehicles,
          icon: Icons.directions_car_filled_outlined,
        ),
      if (canEmployees)
        const _ModuleItem(
          label: 'Employees',
          route: AppRoutes.employees,
          icon: Icons.badge_outlined,
        ),
      if (canReports)
        const _ModuleItem(
          label: 'Reports',
          route: AppRoutes.reports,
          icon: Icons.analytics_outlined,
        ),
    ];
    if (items.isEmpty) {
      return const Center(child: Text('No modules available for your role.'));
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: items.length,
      separatorBuilder: (_, __) => const SizedBox(height: 10),
      itemBuilder: (context, index) {
        final item = items[index];
        return Container(
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                Color(0xB8FFFFFF),
                Color(0x73FFFFFF),
              ],
            ),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0x1423344A)),
            boxShadow: const [
              BoxShadow(
                color: Color(0x1423344A),
                blurRadius: 18,
                offset: Offset(0, 8),
              ),
            ],
          ),
          child: ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 2),
            leading: Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                gradient: const LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xF5FFFFFF), Color(0xADFFFFFF)],
                ),
                border: Border.all(color: const Color(0x1A23344A)),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(item.icon, size: 20, color: AppColors.primary),
            ),
            title: Text(
              item.label,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: AppColors.text,
              ),
            ),
            trailing: const Icon(
              Icons.chevron_right_rounded,
              color: AppColors.textMuted,
            ),
            onTap: () => Navigator.pushNamed(context, item.route),
          ),
        );
      },
    );
  }
}

class _ModuleItem {
  final String label;
  final String route;
  final IconData icon;

  const _ModuleItem({
    required this.label,
    required this.route,
    required this.icon,
  });
}
