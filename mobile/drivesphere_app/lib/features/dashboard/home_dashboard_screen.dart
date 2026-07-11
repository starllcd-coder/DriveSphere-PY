import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_section_card.dart';

class HomeDashboardScreen extends StatefulWidget {
  const HomeDashboardScreen({super.key});

  @override
  State<HomeDashboardScreen> createState() => _HomeDashboardScreenState();
}

class _HomeDashboardScreenState extends State<HomeDashboardScreen> {
  final ApiService _apiService = ApiService();

  String _selectedCountry = '-';
  String _selectedCity = '-';
  String _currencyCode = 'OMR';
  List<VehicleModel> _recommended = [];
  List<VehicleModel> _popular = [];
  List<VehicleModel> _deals = [];

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  @override
  void initState() {
    super.initState();
    _loadMarketplaceContext();
    _loadVehiclesSections();
  }

  Future<void> _loadMarketplaceContext() async {
    final country = await _apiService.getSelectedCountry();
    final city = await _apiService.getSelectedCity();

    if (!mounted) return;

    setState(() {
      _selectedCountry = country ?? '-';
      _selectedCity = city ?? '-';
      _currencyCode = _currencyFromCountry(_selectedCountry);
    });
  }

  String _currencyFromCountry(String country) {
    switch (country) {
      case 'Oman':
        return 'OMR';
      case 'United Arab Emirates':
        return 'AED';
      case 'Saudi Arabia':
        return 'SAR';
      case 'Qatar':
        return 'QAR';
      case 'Kuwait':
        return 'KWD';
      case 'Bahrain':
        return 'BHD';
      default:
        return 'OMR';
    }
  }

  Future<void> _openMapDiscovery() async {
    final vehicles = await _apiService.fetchVehicles();

    if (!mounted) return;

    Navigator.pushNamed(
      context,
      AppRoutes.vehicleMap,
      arguments: vehicles,
    );
  }

  Future<void> _loadVehiclesSections() async {
    final vehicles = await _apiService.fetchVehicles();
    if (!mounted) return;
    setState(() {
      _recommended = vehicles.take(3).toList();
      _popular = [...vehicles]..sort((a, b) => b.rating.compareTo(a.rating));
      _popular = _popular.take(3).toList();
      _deals = [...vehicles]
        ..sort((a, b) => a.dailyRate.compareTo(b.dailyRate));
      _deals = _deals.take(3).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
      child: Column(
        children: [
          _heroCard(context),
          const SizedBox(height: 16),
          _marketplaceInfoCard(),
          const SizedBox(height: 16),
          _quickActions(context),
          const SizedBox(height: 16),
          _tipsCard(),
          const SizedBox(height: 16),
          _vehiclesStrip('Recommended Vehicles', _recommended),
          const SizedBox(height: 16),
          _vehiclesStrip('Popular Vehicles', _popular),
          const SizedBox(height: 16),
          _vehiclesStrip('Special Deals', _deals),
        ],
      ),
    );
  }

  Widget _heroCard(BuildContext context) {
    final welcomeText = _selectedCountry != '-'
        ? 'dashboard.welcome_country'.tr(args: [_selectedCountry])
        : 'dashboard.welcome'.tr();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(22),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(26),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Color(0xFF234E8C),
            Color(0xFF1D467E),
            Color(0xFFD3AE52),
          ],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            welcomeText,
            style: const TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'dashboard.subtitle'.tr(),
            style: const TextStyle(
              fontSize: 13,
              height: 1.5,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              Expanded(
                child: SizedBox(
                  height: 46,
                  child: ElevatedButton(
                    onPressed: () =>
                        Navigator.pushNamed(context, AppRoutes.vehicleSearch),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF1C3566),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                    ),
                    child: Text(
                      'dashboard.start_searching'.tr(),
                      style: const TextStyle(fontWeight: FontWeight.w700),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              SizedBox(
                height: 46,
                child: OutlinedButton.icon(
                  onPressed: _openMapDiscovery,
                  icon: const Icon(Icons.map_outlined),
                  label: Text(_t('Map', 'الخريطة')),
                  style: OutlinedButton.styleFrom(
                    foregroundColor: Colors.white,
                    side: const BorderSide(color: Colors.white70),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _marketplaceInfoCard() {
    return AppSectionCard(
      child: Row(
        children: [
          Expanded(
            child: _infoPill(
              icon: Icons.public_rounded,
              label: _t('Country', 'الدولة'),
              value: _selectedCountry,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _infoPill(
              icon: Icons.location_city_outlined,
              label: _t('City', 'المدينة'),
              value: _selectedCity,
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: _infoPill(
              icon: Icons.payments_outlined,
              label: _t('Currency', 'العملة'),
              value: _currencyCode,
            ),
          ),
        ],
      ),
    );
  }

  Widget _infoPill({
    required IconData icon,
    required String label,
    required String value,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7F9FD),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0xFFE2E8F2)),
      ),
      child: Column(
        children: [
          Icon(icon, color: const Color(0xFF234E8C), size: 22),
          const SizedBox(height: 8),
          Text(
            label,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: Color(0xFF687181),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            textAlign: TextAlign.center,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 12.5,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
        ],
      ),
    );
  }

  Widget _quickActions(BuildContext context) {
    return AppSectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'dashboard.quick_actions'.tr(),
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _actionButton(
                  icon: Icons.search_rounded,
                  title: 'Search',
                  onTap: () =>
                      Navigator.pushNamed(context, AppRoutes.vehicleSearch),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  icon: Icons.map_outlined,
                  title: _t('Map discovery', 'استكشاف الخريطة'),
                  onTap: _openMapDiscovery,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _actionButton(
                  icon: Icons.favorite_outline_rounded,
                  title: _t('Favorites', 'المفضلة'),
                  onTap: () =>
                      Navigator.pushNamed(context, AppRoutes.favorites),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  icon: Icons.compare_arrows_rounded,
                  title: _t('Compare', 'مقارنة'),
                  onTap: () => Navigator.pushNamed(context, AppRoutes.compare),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _actionButton(
                  icon: Icons.receipt_long_rounded,
                  title: 'Bookings',
                  onTap: () =>
                      Navigator.pushNamed(context, AppRoutes.bookingHistory),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  icon: Icons.credit_card_rounded,
                  title: 'Payments',
                  onTap: () => Navigator.pushNamed(context, AppRoutes.payments),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _actionButton(
                  icon: Icons.support_agent_rounded,
                  title: _t('Support', 'الدعم'),
                  onTap: () => Navigator.pushNamed(context, AppRoutes.support),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _actionButton(
                  icon: Icons.notifications_none_rounded,
                  title: _t('Alerts', 'التنبيهات'),
                  onTap: () =>
                      Navigator.pushNamed(context, AppRoutes.notifications),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _actionButton({
    required IconData icon,
    required String title,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(18),
      onTap: onTap,
      child: Container(
        height: 92,
        decoration: BoxDecoration(
          color: const Color(0xFFF7F9FD),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFE2E8F2)),
        ),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, color: const Color(0xFF234E8C), size: 26),
            const SizedBox(height: 8),
            Text(
              title,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _tipsCard() {
    return AppSectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'dashboard.need_before_rent'.tr(),
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 12),
          Text(
            'Upload your documents once, compare vehicles, save favorites, and contact rental companies directly on WhatsApp.',
            style: const TextStyle(
              fontSize: 13,
              height: 1.7,
              color: Color(0xFF687181),
            ),
          ),
        ],
      ),
    );
  }

  Widget _vehiclesStrip(String title, List<VehicleModel> vehicles) {
    return AppSectionCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 17,
              fontWeight: FontWeight.w700,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 10),
          if (vehicles.isEmpty)
            const Text('No vehicles available yet.')
          else
            ...vehicles.map(
              (vehicle) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: InkWell(
                  onTap: () {
                    Navigator.pushNamed(
                      context,
                      AppRoutes.vehicleDetail,
                      arguments: vehicle,
                    );
                  },
                  child: Row(
                    children: [
                      Expanded(
                        child: Text(
                          '${vehicle.fullName} • ${vehicle.companyName}',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      Text(
                        '$_currencyCode ${vehicle.dailyRate.toStringAsFixed(0)}',
                        style: const TextStyle(
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF234E8C),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }
}
