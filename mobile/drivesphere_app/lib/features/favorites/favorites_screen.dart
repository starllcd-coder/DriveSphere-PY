import 'package:flutter/material.dart';

import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';

class FavoritesScreen extends StatefulWidget {
  const FavoritesScreen({super.key});

  @override
  State<FavoritesScreen> createState() => _FavoritesScreenState();
}

class _FavoritesScreenState extends State<FavoritesScreen> {
  final ApiService _apiService = ApiService();
  List<VehicleModel> _favorites = [];
  List<String> _favoriteCompanies = [];
  Map<String, List<VehicleModel>> _companyVehicles = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadFavorites();
  }

  Future<void> _loadFavorites() async {
    final vehicles = await _apiService.fetchVehicles();
    final companies = await _apiService.getFavoriteCompanyNames();
    final companyMap = <String, List<VehicleModel>>{};
    for (final vehicle in vehicles) {
      final key = vehicle.companyName.trim();
      if (key.isEmpty) continue;
      companyMap.putIfAbsent(key, () => []).add(vehicle);
    }
    if (!mounted) return;
    setState(() {
      _favorites = vehicles.where((e) => e.isFavorite).toList();
      _favoriteCompanies = companies;
      _companyVehicles = companyMap;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Favorites'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Vehicles'),
              Tab(text: 'Companies'),
            ],
          ),
        ),
        body: _loading
            ? const Center(child: CircularProgressIndicator())
            : TabBarView(
                children: [
                  _favorites.isEmpty
                      ? const Center(child: Text('No favorite vehicles yet'))
                      : ListView.builder(
                          itemCount: _favorites.length,
                          itemBuilder: (_, index) {
                            final vehicle = _favorites[index];
                            return ListTile(
                              title: Text(vehicle.fullName),
                              subtitle: Text(vehicle.companyName),
                              trailing:
                                  Text(vehicle.dailyRate.toStringAsFixed(0)),
                              onTap: () => Navigator.pushNamed(
                                context,
                                AppRoutes.vehicleDetail,
                                arguments: vehicle,
                              ),
                            );
                          },
                        ),
                  _favoriteCompanies.isEmpty
                      ? const Center(
                          child: Text('No favorite companies yet'),
                        )
                      : ListView.builder(
                          itemCount: _favoriteCompanies.length,
                          itemBuilder: (_, index) {
                            final company = _favoriteCompanies[index];
                            final count =
                                _companyVehicles[company]?.length ?? 0;
                            return ListTile(
                              title: Text(company),
                              subtitle: Text('$count vehicles available'),
                              trailing: IconButton(
                                icon: const Icon(Icons.favorite_rounded,
                                    color: Color(0xFFD14848)),
                                onPressed: () async {
                                  await _apiService
                                      .toggleFavoriteCompany(company);
                                  await _loadFavorites();
                                },
                              ),
                              onTap: () => Navigator.pushNamed(
                                context,
                                AppRoutes.vehicleSearch,
                                arguments: {'company': company},
                              ),
                            );
                          },
                        ),
                ],
              ),
      ),
    );
  }
}
