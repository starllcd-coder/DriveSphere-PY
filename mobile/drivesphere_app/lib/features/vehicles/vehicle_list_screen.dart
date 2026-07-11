import 'package:cached_network_image/cached_network_image.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/constants/app_countries.dart';
import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_error_state.dart';
import '../../widgets/app_snackbar.dart';
import '../../widgets/app_skeleton.dart';

class VehicleListScreen extends StatefulWidget {
  final bool embeddedInShell;

  const VehicleListScreen({
    super.key,
    this.embeddedInShell = false,
  });

  @override
  State<VehicleListScreen> createState() => _VehicleListScreenState();
}

class _VehicleListScreenState extends State<VehicleListScreen> {
  final ApiService _apiService = ApiService();

  bool _loading = true;
  bool _loadError = false;
  List<VehicleModel> _vehicles = [];
  final List<CountryConfig> _countries = AppCountries.supported;
  String? _selectedCountry;
  List<String> _cities = [];
  String _currencyCode = 'OMR';
  String _selectedCity = '';

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  @override
  void initState() {
    super.initState();
    _loadVehicles();
  }

  Future<void> _loadVehicles() async {
    setState(() {
      _loading = true;
      _loadError = false;
    });

    try {
      final selectedCountry = await _apiService.getSelectedCountry();
      final selectedCity = await _apiService.getSelectedCity();
      final country = AppCountries.byName(selectedCountry);

      final vehicles = await _apiService.fetchVehicles();

      if (!mounted) return;
      setState(() {
        _vehicles = vehicles;
        _selectedCountry = country.name;
        _cities = country.cities;
        _currencyCode = country.currencyCode;
        _selectedCity = selectedCity ?? country.cities.first;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() => _loadError = true);
      AppSnackBar.error(
        context,
        _t('Failed to load vehicles.', 'تعذر تحميل المركبات.'),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _onCountryChanged(String? value) {
    if (value == null) return;
    final country = AppCountries.byName(value);
    setState(() {
      _selectedCountry = country.name;
      _cities = country.cities;
      _currencyCode = country.currencyCode;
      _selectedCity = country.cities.isNotEmpty ? country.cities.first : '';
    });
  }

  bool _cityInCountry(String city, String? countryName) {
    if (countryName == null || countryName.isEmpty) return true;
    final country = AppCountries.byName(countryName);
    final cityNorm = city.trim().toLowerCase();
    return country.cities.any((candidate) {
      final candidateNorm = candidate.trim().toLowerCase();
      return cityNorm == candidateNorm ||
          cityNorm.contains(candidateNorm) ||
          candidateNorm.contains(cityNorm);
    });
  }

  bool _cityMatchesSelection(String vehicleCity, String selectedCity) {
    final vehicleCityNorm = vehicleCity.trim().toLowerCase();
    final selectedCityNorm = selectedCity.trim().toLowerCase();
    if (selectedCityNorm.isEmpty) return true;
    return vehicleCityNorm == selectedCityNorm ||
        vehicleCityNorm.contains(selectedCityNorm) ||
        selectedCityNorm.contains(vehicleCityNorm);
  }

  Future<void> _toggleFavorite(VehicleModel vehicle) async {
    final previous = List<VehicleModel>.from(_vehicles);
    setState(() {
      _vehicles = _vehicles
          .map(
            (v) =>
                v.id == vehicle.id ? v.copyWith(isFavorite: !v.isFavorite) : v,
          )
          .toList();
    });
    try {
      await _apiService.toggleFavoriteVehicle(vehicle.id);
    } catch (_) {
      if (!mounted) return;
      setState(() => _vehicles = previous);
      AppSnackBar.error(
        context,
        _t('Could not update favorite right now.', 'تعذر تحديث المفضلة حالياً.'),
      );
    }
  }

  Future<void> _toggleCompare(VehicleModel vehicle) async {
    await _apiService.toggleCompareVehicle(vehicle.id);
    if (!mounted) return;
    AppSnackBar.success(
      context,
      _t('Vehicle compare list updated.', 'تم تحديث قائمة المقارنة.'),
    );
  }

  Color _statusColor(String status) {
    switch (status.toUpperCase()) {
      case 'AVAILABLE':
        return const Color(0xFF179D57);
      case 'MAINTENANCE':
        return const Color(0xFFD28A17);
      case 'BOOKED':
        return const Color(0xFFD14848);
      default:
        return const Color(0xFF6B7280);
    }
  }

  @override
  Widget build(BuildContext context) {
    final countryVehicles =
        _selectedCountry == null || _selectedCountry!.isEmpty
            ? _vehicles
            : _vehicles
                .where((v) => _cityInCountry(v.city, _selectedCountry))
                .toList();
    final visibleVehicles = _selectedCity.isEmpty
        ? countryVehicles
        : countryVehicles
            .where((v) => _cityMatchesSelection(v.city, _selectedCity))
            .toList();

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        automaticallyImplyLeading: !widget.embeddedInShell,
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          _t('Vehicles', 'المركبات'),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            onPressed: () =>
                Navigator.pushNamed(context, AppRoutes.vehicleSearch),
            icon: const Icon(Icons.search_rounded, color: Color(0xFF1C3566)),
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, AppRoutes.compare),
            icon: const Icon(Icons.compare_arrows_rounded,
                color: Color(0xFF1C3566)),
          ),
          IconButton(
            onPressed: () => Navigator.pushNamed(context, AppRoutes.favorites),
            icon: const Icon(Icons.favorite_outline_rounded,
                color: Color(0xFF1C3566)),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 14, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedCountry,
                    isExpanded: true,
                    items: _countries
                        .map(
                          (country) => DropdownMenuItem<String>(
                            value: country.name,
                            child: Text(
                              context.locale.languageCode == 'ar'
                                  ? country.arabicName
                                  : country.name,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    decoration: InputDecoration(
                      hintText: _t('Country', 'الدولة'),
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      prefixIcon: const Icon(Icons.public_rounded, size: 18),
                      prefixIconConstraints: const BoxConstraints(
                        minWidth: 30,
                        maxWidth: 30,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    onChanged: _onCountryChanged,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedCity.isEmpty ? null : _selectedCity,
                    isExpanded: true,
                    items: _cities
                        .map(
                          (city) => DropdownMenuItem<String>(
                            value: city,
                            child: Text(
                              city,
                              overflow: TextOverflow.ellipsis,
                            ),
                          ),
                        )
                        .toList(),
                    decoration: InputDecoration(
                      hintText: _t('City', 'المدينة'),
                      isDense: true,
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 10,
                        vertical: 8,
                      ),
                      prefixIcon: const Icon(Icons.location_city_outlined, size: 18),
                      prefixIconConstraints: const BoxConstraints(
                        minWidth: 30,
                        maxWidth: 30,
                      ),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                    onChanged: (value) {
                      setState(() => _selectedCity = value ?? '');
                    },
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: _headerChip(
                    icon: Icons.location_on_outlined,
                    label: _selectedCity.isEmpty
                        ? _t('All cities', 'كل المدن')
                        : _selectedCity,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: _headerChip(
                    icon: Icons.payments_outlined,
                    label: _currencyCode,
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: visibleVehicles.isEmpty
                        ? null
                        : () {
                            Navigator.pushNamed(
                              context,
                              AppRoutes.vehicleMap,
                              arguments: visibleVehicles,
                            );
                          },
                    icon: const Icon(Icons.map_outlined),
                    label: Text(_t('Map view', 'عرض الخريطة')),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.white,
                      foregroundColor: const Color(0xFF234E8C),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                        side: const BorderSide(color: Color(0xFFE2E8F2)),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: ElevatedButton.icon(
                    onPressed: () =>
                        Navigator.pushNamed(context, AppRoutes.compare),
                    icon: const Icon(Icons.compare_arrows_rounded),
                    label: Text(_t('Compare', 'مقارنة')),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF234E8C),
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(14),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? const AppSkeletonList(itemHeight: 320)
                : _loadError
                    ? AppErrorState(
                        title: _t(
                          'Could not load vehicles',
                          'تعذر تحميل المركبات',
                        ),
                        subtitle: _t(
                          'Please check your connection and retry.',
                          'يرجى التحقق من الاتصال ثم إعادة المحاولة.',
                        ),
                        onRetry: _loadVehicles,
                      )
                : visibleVehicles.isEmpty
                    ? AppEmptyState(
                        icon: Icons.directions_car_outlined,
                        title:
                            _t('No vehicles found', 'لم يتم العثور على مركبات'),
                        subtitle: _t(
                          'Try changing your selected city or filters.',
                          'جرّب تغيير المدينة المختارة أو الفلاتر.',
                        ),
                      )
                    : RefreshIndicator(
                        onRefresh: _loadVehicles,
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                          itemCount: visibleVehicles.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 14),
                          itemBuilder: (context, index) {
                            final vehicle = visibleVehicles[index];

                            return InkWell(
                              borderRadius: BorderRadius.circular(24),
                              onTap: () {
                                Navigator.pushNamed(
                                  context,
                                  AppRoutes.vehicleDetail,
                                  arguments: vehicle,
                                );
                              },
                              child: Container(
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(24),
                                  boxShadow: [
                                    BoxShadow(
                                      color:
                                          const Color(0xFFB7C0D1).withAlpha(46),
                                      blurRadius: 14,
                                      offset: const Offset(0, 8),
                                    ),
                                  ],
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Stack(
                                      children: [
                                        ClipRRect(
                                          borderRadius:
                                              const BorderRadius.vertical(
                                            top: Radius.circular(24),
                                          ),
                                          child: SizedBox(
                                            height: 170,
                                            width: double.infinity,
                                            child: vehicle.imageUrl.isNotEmpty
                                                ? CachedNetworkImage(
                                                    imageUrl: vehicle.imageUrl,
                                                    fit: BoxFit.cover,
                                                    errorWidget: (_, __, ___) =>
                                                        const Center(
                                                      child: Icon(
                                                          Icons.directions_car),
                                                    ),
                                                  )
                                                : const DecoratedBox(
                                                    decoration: BoxDecoration(
                                                        color:
                                                            Color(0xFFF2F5FA)),
                                                    child: Center(
                                                      child: Icon(
                                                        Icons
                                                            .directions_car_rounded,
                                                        size: 44,
                                                        color:
                                                            Color(0xFF234E8C),
                                                      ),
                                                    ),
                                                  ),
                                          ),
                                        ),
                                        Positioned(
                                          top: 12,
                                          right: 12,
                                          child: Row(
                                            children: [
                                              _circleAction(
                                                icon: vehicle.isFavorite
                                                    ? Icons.favorite_rounded
                                                    : Icons
                                                        .favorite_border_rounded,
                                                color: vehicle.isFavorite
                                                    ? const Color(0xFFD14848)
                                                    : const Color(0xFF234E8C),
                                                onTap: () =>
                                                    _toggleFavorite(vehicle),
                                              ),
                                              const SizedBox(width: 8),
                                              _circleAction(
                                                icon: Icons
                                                    .compare_arrows_rounded,
                                                color: const Color(0xFF234E8C),
                                                onTap: () =>
                                                    _toggleCompare(vehicle),
                                              ),
                                            ],
                                          ),
                                        ),
                                      ],
                                    ),
                                    Padding(
                                      padding: const EdgeInsets.all(16),
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Row(
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  vehicle.fullName,
                                                  style: const TextStyle(
                                                    fontSize: 18,
                                                    fontWeight: FontWeight.w700,
                                                    color: Color(0xFF1C3566),
                                                  ),
                                                ),
                                              ),
                                              Container(
                                                padding:
                                                    const EdgeInsets.symmetric(
                                                  horizontal: 10,
                                                  vertical: 6,
                                                ),
                                                decoration: BoxDecoration(
                                                  color: _statusColor(
                                                          vehicle.status)
                                                      .withAlpha(31),
                                                  borderRadius:
                                                      BorderRadius.circular(50),
                                                ),
                                                child: Text(
                                                  vehicle.status,
                                                  style: TextStyle(
                                                    color: _statusColor(
                                                        vehicle.status),
                                                    fontWeight: FontWeight.w700,
                                                    fontSize: 11,
                                                  ),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 8),
                                          Row(
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  '${vehicle.year} • ${vehicle.companyName} • ${vehicle.city}',
                                                  style: const TextStyle(
                                                    color: Color(0xFF687181),
                                                    fontSize: 13,
                                                  ),
                                                ),
                                              ),
                                              if (vehicle.companyVerified)
                                                _verifiedPill(),
                                            ],
                                          ),
                                          const SizedBox(height: 6),
                                          Text(
                                            vehicle.pickupLocation,
                                            style: const TextStyle(
                                              color: Color(0xFF687181),
                                              fontSize: 12.5,
                                            ),
                                          ),
                                          const SizedBox(height: 10),
                                          Wrap(
                                            spacing: 8,
                                            runSpacing: 8,
                                            children: [
                                              _tag(vehicle.category),
                                              _tag(vehicle.transmission),
                                              _tag('${vehicle.seats} seats'),
                                            ],
                                          ),
                                          const SizedBox(height: 14),
                                          Row(
                                            children: [
                                              Text(
                                                '$_currencyCode ${vehicle.dailyRate.toStringAsFixed(0)}',
                                                style: const TextStyle(
                                                  fontSize: 18,
                                                  fontWeight: FontWeight.w700,
                                                  color: Color(0xFF1C3566),
                                                ),
                                              ),
                                              Text(
                                                _t(' / day', ' / يوم'),
                                                style: const TextStyle(
                                                  fontSize: 13,
                                                  fontWeight: FontWeight.w500,
                                                  color: Color(0xFF7C7F8E),
                                                ),
                                              ),
                                              const Spacer(),
                                              SizedBox(
                                                height: 32,
                                                child: ElevatedButton(
                                                  onPressed: () {
                                                    Navigator.pushNamed(
                                                      context,
                                                      AppRoutes.booking,
                                                      arguments: vehicle,
                                                    );
                                                  },
                                                  style:
                                                      ElevatedButton.styleFrom(
                                                    backgroundColor:
                                                        const Color(0xFF234E8C),
                                                    foregroundColor:
                                                        Colors.white,
                                                    padding: const EdgeInsets
                                                        .symmetric(
                                                      horizontal: 10,
                                                    ),
                                                    shape:
                                                        RoundedRectangleBorder(
                                                      borderRadius:
                                                          BorderRadius.circular(
                                                              12),
                                                    ),
                                                  ),
                                                  child: Text(
                                                    _t('Quick book',
                                                        'حجز سريع'),
                                                    style: const TextStyle(
                                                      fontSize: 11,
                                                      fontWeight:
                                                          FontWeight.w700,
                                                    ),
                                                  ),
                                                ),
                                              ),
                                              const SizedBox(width: 8),
                                              const Icon(Icons.star_rounded,
                                                  size: 18,
                                                  color: Color(0xFFD3AE52)),
                                              const SizedBox(width: 4),
                                              Text(
                                                '${vehicle.rating.toStringAsFixed(1)} (${vehicle.reviewCount})',
                                                style: const TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  color: Color(0xFF162E60),
                                                ),
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _headerChip({
    required IconData icon,
    required String label,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F2)),
      ),
      child: Row(
        children: [
          Icon(icon, size: 18, color: const Color(0xFF234E8C)),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              label,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                color: Color(0xFF162E60),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _circleAction({
    required IconData icon,
    required Color color,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.white.withAlpha(240),
      shape: const CircleBorder(),
      child: InkWell(
        customBorder: const CircleBorder(),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Icon(icon, size: 20, color: color),
        ),
      ),
    );
  }

  Widget _tag(String text) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: const Color(0xFFF4F7FB),
        borderRadius: BorderRadius.circular(50),
      ),
      child: Text(
        text,
        style: const TextStyle(
          fontSize: 11.5,
          fontWeight: FontWeight.w600,
          color: Color(0xFF234E8C),
        ),
      ),
    );
  }

  Widget _verifiedPill() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFF179D57).withAlpha(31),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        _t('Verified', 'موثوق'),
        style: const TextStyle(
          color: Color(0xFF179D57),
          fontSize: 11,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }
}
