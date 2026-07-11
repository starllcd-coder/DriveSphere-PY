import 'dart:async';

import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../services/api_service.dart';
import '../../services/offline/offline_mode.dart';
import '../../services/push_notification_service.dart';
import '../../models/vehicle_model.dart';
import '../bookings/booking_history_screen.dart';
import '../favorites/favorites_screen.dart';
import '../notifications/notifications_screen.dart';
import '../profile/profile_screen.dart';
import '../vehicles/vehicle_list_screen.dart';
import '../vehicles/vehicle_map_screen.dart';
import 'home_dashboard_screen.dart';

class AppShellScreen extends StatefulWidget {
  const AppShellScreen({super.key});

  @override
  State<AppShellScreen> createState() => _AppShellScreenState();
}

class _AppShellScreenState extends State<AppShellScreen> {
  int _currentIndex = 0;
  final ApiService _apiService = ApiService();
  late final PushNotificationService _pushService;
  Timer? _modeBannerTimer;
  bool _showModeBanner = true;
  String _lastBannerSignature = '';

  Widget _buildMapScreen() {
    return FutureBuilder<List<VehicleModel>>(
      future: _apiService.fetchVehicles(),
      builder: (context, snapshot) {
        if (!snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }

        return VehicleMapScreen(
          vehicles: snapshot.data ?? const <VehicleModel>[],
          embeddedInShell: true,
        );
      },
    );
  }

  @override
  void initState() {
    super.initState();
    _pushService = PushNotificationService(apiService: _apiService);
    _pushService.initialize();
  }

  @override
  void dispose() {
    _modeBannerTimer?.cancel();
    super.dispose();
  }

  void _refreshBannerVisibility(String signature) {
    if (_lastBannerSignature == signature) return;
    _lastBannerSignature = signature;

    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      setState(() => _showModeBanner = true);
      _modeBannerTimer?.cancel();
      _modeBannerTimer = Timer(const Duration(seconds: 4), () {
        if (!mounted) return;
        setState(() => _showModeBanner = false);
      });
    });
  }

  @override
  Widget build(BuildContext context) {
    final titles = [
      'app_name'.tr(),
      'nav.vehicles'.tr(),
      'nav.map'.tr(),
      'nav.bookings'.tr(),
      'nav.profile'.tr(),
    ];

    final screens = [
      const HomeDashboardScreen(),
      const VehicleListScreen(embeddedInShell: true),
      _buildMapScreen(),
      const BookingHistoryScreen(embeddedInShell: true),
      const ProfileScreen(embeddedInShell: true),
    ];

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          titles[_currentIndex],
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: _currentIndex == 0
            ? [
                IconButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => const NotificationsScreen(),
                      ),
                    );
                  },
                  icon: const Icon(
                    Icons.notifications_none_rounded,
                    color: Color(0xFF1C3566),
                  ),
                ),
                IconButton(
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                          builder: (_) => const FavoritesScreen()),
                    );
                  },
                  icon: const Icon(Icons.favorite_outline_rounded,
                      color: Color(0xFF1C3566)),
                ),
              ]
            : null,
      ),
      body: Column(
        children: [
          ValueListenableBuilder<OfflineMode>(
            valueListenable: _apiService.modeListenable,
            builder: (context, mode, _) {
              Color bg;
              Color fg;
              String text;
              switch (mode) {
                case OfflineMode.online:
                  bg = const Color(0xFFDCFCE7);
                  fg = const Color(0xFF166534);
                  text = 'Online mode';
                  break;
                case OfflineMode.offline:
                  bg = const Color(0xFFFEF3C7);
                  fg = const Color(0xFF92400E);
                  text = 'Offline cached mode';
                  break;
                case OfflineMode.demo:
                  bg = const Color(0xFFE0E7FF);
                  fg = const Color(0xFF3730A3);
                  text = 'Demo mode';
                  break;
              }
              return ValueListenableBuilder<int>(
                valueListenable: _apiService.queueCountListenable,
                builder: (context, queueCount, _) {
                  return ValueListenableBuilder<bool>(
                    valueListenable: _apiService.syncingListenable,
                    builder: (context, syncing, _) {
                      final suffix = <String>[
                        if (syncing) 'Syncing...',
                        if (queueCount > 0) '$queueCount pending',
                      ].join('  ');
                      final fullText =
                          suffix.isEmpty ? text : '$text - $suffix';
                      _refreshBannerVisibility(
                        '${mode.name}|$queueCount|$syncing|$fullText',
                      );
                      if (!_showModeBanner) {
                        return const SizedBox.shrink();
                      }
                      return Container(
                        width: double.infinity,
                        color: bg,
                        padding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 6,
                        ),
                        child: Text(
                          fullText,
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: fg,
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      );
                    },
                  );
                },
              );
            },
          ),
          Expanded(child: screens[_currentIndex]),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        height: 72,
        backgroundColor: Colors.white,
        indicatorColor: const Color(0xFF234E8C).withAlpha(31),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: [
          NavigationDestination(
            icon: const Icon(Icons.home_outlined),
            selectedIcon: const Icon(Icons.home_rounded),
            label: 'nav.home'.tr(),
          ),
          NavigationDestination(
            icon: const Icon(Icons.directions_car_outlined),
            selectedIcon: const Icon(Icons.directions_car_rounded),
            label: 'nav.vehicles'.tr(),
          ),
          NavigationDestination(
            icon: const Icon(Icons.map_outlined),
            selectedIcon: const Icon(Icons.map_rounded),
            label: 'nav.map'.tr(),
          ),
          NavigationDestination(
            icon: const Icon(Icons.receipt_long_outlined),
            selectedIcon: const Icon(Icons.receipt_long_rounded),
            label: 'nav.bookings'.tr(),
          ),
          NavigationDestination(
            icon: const Icon(Icons.person_outline_rounded),
            selectedIcon: const Icon(Icons.person_rounded),
            label: 'nav.profile'.tr(),
          ),
        ],
      ),
    );
  }
}
