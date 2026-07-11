import 'package:cached_network_image/cached_network_image.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';

import '../../core/constants/app_countries.dart';
import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';

class VehicleMapScreen extends StatefulWidget {
  final List<VehicleModel> vehicles;
  final bool embeddedInShell;

  const VehicleMapScreen({
    super.key,
    required this.vehicles,
    this.embeddedInShell = false,
  });

  @override
  State<VehicleMapScreen> createState() => _VehicleMapScreenState();
}

class _VehicleMapScreenState extends State<VehicleMapScreen> {
  final ApiService _apiService = ApiService();
  final MapController _mapController = MapController();
  final Distance _distance = const Distance();

  CountryConfig? _countryConfig;
  final List<CountryConfig> _countries = AppCountries.supported;
  String? _selectedCountryName;
  String? _selectedCity;
  bool _showNearbyOnly = false;
  bool _showAirportOnly = false;
  LatLng? _focusPoint;

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  @override
  void initState() {
    super.initState();
    _loadCountry();
  }

  Future<void> _loadCountry() async {
    final selectedCountry = await _apiService.getSelectedCountry();
    final selectedCity = await _apiService.getSelectedCity();

    if (!mounted) return;

    final config = AppCountries.byName(selectedCountry);

    setState(() {
      _countryConfig = config;
      _selectedCountryName = config.name;
      _selectedCity = selectedCity ?? config.cities.first;
      _focusPoint = LatLng(config.centerLat, config.centerLng);
    });
  }

  void _onCountryChanged(String? value) {
    if (value == null) return;
    final config = AppCountries.byName(value);
    setState(() {
      _countryConfig = config;
      _selectedCountryName = config.name;
      _selectedCity = config.cities.isNotEmpty ? config.cities.first : null;
      _focusPoint = LatLng(config.centerLat, config.centerLng);
    });
    _mapController.move(LatLng(config.centerLat, config.centerLng), 11.2);
  }

  bool _isAirportPickup(VehicleModel vehicle) {
    final value = vehicle.pickupLocation.toLowerCase();
    return value.contains('airport') || value.contains('مطار');
  }

  double _vehicleDistanceKm(VehicleModel vehicle, LatLng origin) {
    if (!vehicle.hasCoordinates) return 999999;
    final meters = _distance.as(
      LengthUnit.Meter,
      origin,
      LatLng(vehicle.latitude!, vehicle.longitude!),
    );
    return meters / 1000;
  }

  bool _cityMatches(String backendCity, String configuredCity) {
    final backend = backendCity.trim().toLowerCase();
    final configured = configuredCity.trim().toLowerCase();
    return backend == configured ||
        backend.contains(configured) ||
        configured.contains(backend);
  }

  List<VehicleModel> _filteredVehicles(CountryConfig country) {
    final origin = _focusPoint ?? LatLng(country.centerLat, country.centerLng);

    List<VehicleModel> list = widget.vehicles.where((vehicle) {
      final countryOk = country.cities.any(
        (city) => _cityMatches(vehicle.city, city),
      );
      final cityOk = _selectedCity == null || _selectedCity!.isEmpty
          ? true
          : _cityMatches(vehicle.city, _selectedCity!);

      final airportOk = !_showAirportOnly ? true : _isAirportPickup(vehicle);

      return countryOk && cityOk && airportOk;
    }).toList();

    if (_showNearbyOnly) {
      list = list.where((vehicle) {
        if (!vehicle.hasCoordinates) return false;
        final km = _vehicleDistanceKm(vehicle, origin);
        return km <= 12;
      }).toList();
    }

    list.sort((a, b) {
      final da = _vehicleDistanceKm(a, origin);
      final db = _vehicleDistanceKm(b, origin);
      return da.compareTo(db);
    });

    return list;
  }

  void _recenter(CountryConfig country) {
    final target = LatLng(country.centerLat, country.centerLng);

    setState(() {
      _focusPoint = target;
    });

    _mapController.move(target, 11.2);
  }

  void _focusVehicle(VehicleModel vehicle) {
    if (!vehicle.hasCoordinates) return;

    final point = LatLng(vehicle.latitude!, vehicle.longitude!);

    setState(() {
      _focusPoint = point;
    });

    _mapController.move(point, 13.6);
  }

  @override
  Widget build(BuildContext context) {
    final country = _countryConfig ?? AppCountries.supported.first;
    final visibleVehicles = _filteredVehicles(country);
    final cities = country.cities;
    final origin = _focusPoint ?? LatLng(country.centerLat, country.centerLng);

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        automaticallyImplyLeading: !widget.embeddedInShell,
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          _t('Map discovery', 'استكشاف الخريطة'),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
      ),
      body: Column(
        children: [
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
            child: Column(
              children: [
                DropdownButtonFormField<String>(
                  initialValue: _selectedCountryName,
                  items: _countries
                      .map(
                        (country) => DropdownMenuItem<String>(
                          value: country.name,
                          child: Text(
                            context.locale.languageCode == 'ar'
                                ? country.arabicName
                                : country.name,
                          ),
                        ),
                      )
                      .toList(),
                  decoration: InputDecoration(
                    labelText: _t('Country', 'الدولة'),
                    prefixIcon: const Icon(Icons.public_rounded),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                    contentPadding: const EdgeInsets.symmetric(
                      horizontal: 12,
                      vertical: 12,
                    ),
                  ),
                  onChanged: _onCountryChanged,
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: DropdownButtonFormField<String>(
                        initialValue: _selectedCity,
                        items: cities
                            .map(
                              (city) => DropdownMenuItem<String>(
                                value: city,
                                child: Text(city),
                              ),
                            )
                            .toList(),
                        decoration: InputDecoration(
                          labelText: _t('City', 'المدينة'),
                          prefixIcon: const Icon(Icons.location_city_outlined),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                          contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12,
                            vertical: 12,
                          ),
                        ),
                        onChanged: (value) async {
                          setState(() => _selectedCity = value);
                          if (value != null) {
                            await _apiService.saveSelectedCity(value);
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    SizedBox(
                      height: 56,
                      child: OutlinedButton.icon(
                        onPressed: () => _recenter(country),
                        icon: const Icon(Icons.my_location_rounded),
                        label: Text(_t('Center', 'توسيط')),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFF234E8C),
                          side: const BorderSide(color: Color(0xFFE2E8F2)),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: _filterChip(
                        active: _showNearbyOnly,
                        icon: Icons.near_me_rounded,
                        label: _t('Nearby', 'القريبة'),
                        onTap: () {
                          setState(() => _showNearbyOnly = !_showNearbyOnly);
                        },
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _filterChip(
                        active: _showAirportOnly,
                        icon: Icons.local_airport_rounded,
                        label: _t('Airport pickup', 'استلام من المطار'),
                        onTap: () {
                          setState(() => _showAirportOnly = !_showAirportOnly);
                        },
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            flex: 5,
            child: Stack(
              children: [
                FlutterMap(
                  mapController: _mapController,
                  options: MapOptions(
                    initialCenter: LatLng(country.centerLat, country.centerLng),
                    initialZoom: 11.2,
                    onPositionChanged: (position, hasGesture) {
                      _focusPoint = position.center;
                      if (mounted) setState(() {});
                    },
                  ),
                  children: [
                    TileLayer(
                      urlTemplate:
                          'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                      userAgentPackageName: 'com.drivesphere.customer',
                    ),
                    MarkerLayer(
                      markers: visibleVehicles
                          .where((vehicle) => vehicle.hasCoordinates)
                          .map((vehicle) {
                        final isAirport = _isAirportPickup(vehicle);

                        return Marker(
                          point: LatLng(vehicle.latitude!, vehicle.longitude!),
                          width: 116,
                          height: 60,
                          child: GestureDetector(
                            onTap: () {
                              Navigator.pushNamed(
                                context,
                                AppRoutes.vehicleDetail,
                                arguments: vehicle,
                              );
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 10,
                                vertical: 8,
                              ),
                              decoration: BoxDecoration(
                                color: isAirport
                                    ? const Color(0xFFD3AE52)
                                    : const Color(0xFF234E8C),
                                borderRadius: BorderRadius.circular(16),
                                boxShadow: [
                                  BoxShadow(
                                    color: Colors.black.withAlpha(46),
                                    blurRadius: 8,
                                    offset: const Offset(0, 4),
                                  ),
                                ],
                              ),
                              child: Stack(
                                children: [
                                  Center(
                                    child: Column(
                                      mainAxisAlignment:
                                          MainAxisAlignment.center,
                                      children: [
                                        Text(
                                          vehicle.brandName,
                                          maxLines: 1,
                                          overflow: TextOverflow.ellipsis,
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 11,
                                            fontWeight: FontWeight.w700,
                                          ),
                                        ),
                                        Text(
                                          '${country.currencyCode} ${vehicle.dailyRate.toStringAsFixed(0)}',
                                          style: const TextStyle(
                                            color: Colors.white,
                                            fontSize: 10.5,
                                            fontWeight: FontWeight.w600,
                                          ),
                                        ),
                                      ],
                                    ),
                                  ),
                                  if (vehicle.companyVerified)
                                    Positioned(
                                      top: 2,
                                      right: 4,
                                      child: _markerVerifiedBadge(),
                                    ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ],
                ),
                Positioned(
                  right: 14,
                  bottom: 14,
                  child: FloatingActionButton.small(
                    heroTag: 'recenter_map_btn',
                    backgroundColor: Colors.white,
                    foregroundColor: const Color(0xFF234E8C),
                    onPressed: () => _recenter(country),
                    child: const Icon(Icons.gps_fixed_rounded),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            flex: 4,
            child: visibleVehicles.isEmpty
                ? Center(
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Text(
                        _t(
                          'No vehicles match the selected map filters.',
                          'لا توجد مركبات مطابقة لفلاتر الخريطة الحالية.',
                        ),
                        textAlign: TextAlign.center,
                        style: const TextStyle(
                          color: Color(0xFF687181),
                          fontSize: 14,
                        ),
                      ),
                    ),
                  )
                : Column(
                    children: [
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
                        child: Text(
                          '${visibleVehicles.length} ${_t('vehicles found', 'مركبة متاحة')}',
                          style: const TextStyle(
                            color: Color(0xFF162E60),
                            fontWeight: FontWeight.w700,
                            fontSize: 14,
                          ),
                        ),
                      ),
                      Expanded(
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(16, 8, 16, 18),
                          itemCount: visibleVehicles.length,
                          separatorBuilder: (_, __) =>
                              const SizedBox(height: 12),
                          itemBuilder: (context, index) {
                            final vehicle = visibleVehicles[index];
                            final km = _vehicleDistanceKm(vehicle, origin);
                            final isAirport = _isAirportPickup(vehicle);

                            return InkWell(
                              onTap: () => _focusVehicle(vehicle),
                              borderRadius: BorderRadius.circular(18),
                              child: Container(
                                padding: const EdgeInsets.all(14),
                                decoration: BoxDecoration(
                                  color: Colors.white,
                                  borderRadius: BorderRadius.circular(18),
                                  border: Border.all(
                                    color: const Color(0xFFE2E8F2),
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color:
                                          const Color(0xFFB7C0D1).withAlpha(26),
                                      blurRadius: 10,
                                      offset: const Offset(0, 6),
                                    ),
                                  ],
                                ),
                                child: Row(
                                  children: [
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(14),
                                      child: SizedBox(
                                        width: 82,
                                        height: 64,
                                        child: vehicle.imageUrl.isNotEmpty
                                            ? CachedNetworkImage(
                                                imageUrl: vehicle.imageUrl,
                                                fit: BoxFit.cover,
                                                errorWidget: (_, __, ___) =>
                                                    const Icon(
                                                        Icons.directions_car),
                                              )
                                            : const DecoratedBox(
                                                decoration: BoxDecoration(
                                                  color: Color(0xFFF2F5FA),
                                                ),
                                                child: Icon(
                                                  Icons.directions_car,
                                                  color: Color(0xFF234E8C),
                                                ),
                                              ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          Text(
                                            vehicle.fullName,
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              color: Color(0xFF162E60),
                                              fontSize: 14.5,
                                            ),
                                          ),
                                          const SizedBox(height: 4),
                                          Row(
                                            children: [
                                              Expanded(
                                                child: Text(
                                                  '${vehicle.companyName} • ${vehicle.pickupLocation}',
                                                  maxLines: 2,
                                                  overflow: TextOverflow.ellipsis,
                                                  style: const TextStyle(
                                                    fontSize: 12.5,
                                                    color: Color(0xFF687181),
                                                  ),
                                                ),
                                              ),
                                              if (vehicle.companyVerified)
                                                _verifiedPill(),
                                            ],
                                          ),
                                          const SizedBox(height: 8),
                                          Wrap(
                                            spacing: 8,
                                            runSpacing: 8,
                                            children: [
                                              _miniTag(
                                                icon: Icons.place_outlined,
                                                text: km >= 999999
                                                    ? _t('No distance',
                                                        'بدون مسافة')
                                                    : '${km.toStringAsFixed(1)} ${_t('km', 'كم')}',
                                                color: const Color(0xFF234E8C),
                                              ),
                                              if (isAirport)
                                                _miniTag(
                                                  icon: Icons
                                                      .local_airport_rounded,
                                                  text: _t('Airport', 'مطار'),
                                                  color:
                                                      const Color(0xFFD3AE52),
                                                ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Column(
                                      crossAxisAlignment:
                                          CrossAxisAlignment.end,
                                      children: [
                                        Text(
                                          '${country.currencyCode} ${vehicle.dailyRate.toStringAsFixed(0)}',
                                          style: const TextStyle(
                                            fontWeight: FontWeight.w700,
                                            color: Color(0xFF234E8C),
                                            fontSize: 14.5,
                                          ),
                                        ),
                                        const SizedBox(height: 8),
                                        SizedBox(
                                          height: 34,
                                          child: ElevatedButton(
                                            onPressed: () {
                                              Navigator.pushNamed(
                                                context,
                                                AppRoutes.vehicleDetail,
                                                arguments: vehicle,
                                              );
                                            },
                                            style: ElevatedButton.styleFrom(
                                              backgroundColor:
                                                  const Color(0xFF234E8C),
                                              foregroundColor: Colors.white,
                                              elevation: 0,
                                              padding:
                                                  const EdgeInsets.symmetric(
                                                horizontal: 12,
                                              ),
                                              shape: RoundedRectangleBorder(
                                                borderRadius:
                                                    BorderRadius.circular(12),
                                              ),
                                            ),
                                            child: Text(
                                              _t('View', 'عرض'),
                                              style: const TextStyle(
                                                fontWeight: FontWeight.w700,
                                                fontSize: 12,
                                              ),
                                            ),
                                          ),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _filterChip({
    required bool active,
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Container(
        height: 46,
        decoration: BoxDecoration(
          color: active ? const Color(0xFF234E8C) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: active ? const Color(0xFF234E8C) : const Color(0xFFE2E8F2),
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              icon,
              size: 18,
              color: active ? Colors.white : const Color(0xFF234E8C),
            ),
            const SizedBox(width: 8),
            Text(
              label,
              style: TextStyle(
                color: active ? Colors.white : const Color(0xFF234E8C),
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _miniTag({
    required IconData icon,
    required String text,
    required Color color,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
      decoration: BoxDecoration(
        color: color.withAlpha(26),
        borderRadius: BorderRadius.circular(50),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 5),
          Text(
            text,
            style: TextStyle(
              color: color,
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
            ),
          ),
        ],
      ),
    );
  }

  Widget _markerVerifiedBadge() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(10),
      ),
      child: const Icon(
        Icons.verified_rounded,
        size: 12,
        color: Color(0xFF179D57),
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
