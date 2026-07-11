import 'package:cached_network_image/cached_network_image.dart';
import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';

import '../../core/constants/app_countries.dart';
import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../widgets/app_empty_state.dart';
import '../../widgets/app_snackbar.dart';

class VehicleSearchScreen extends StatefulWidget {
  final String? initialCompany;

  const VehicleSearchScreen({
    super.key,
    this.initialCompany,
  });

  @override
  State<VehicleSearchScreen> createState() => _VehicleSearchScreenState();
}

class _VehicleSearchScreenState extends State<VehicleSearchScreen> {
  final TextEditingController _brandController = TextEditingController();
  final TextEditingController _companyController = TextEditingController();
  final TextEditingController _pickupLocationController =
      TextEditingController();
  final TextEditingController _returnLocationController =
      TextEditingController();
  final TextEditingController _minPriceController = TextEditingController();
  final TextEditingController _maxPriceController = TextEditingController();
  final TextEditingController _maxDepositController = TextEditingController();
  final ApiService _apiService = ApiService();

  DateTime? _pickupDate;
  DateTime? _returnDate;

  bool _loading = false;
  List<VehicleModel> _vehicles = [];
  final List<CountryConfig> _countries = AppCountries.supported;
  String? _selectedCountry;
  List<String> _cities = [];
  String? _selectedCity;
  String _currencyCode = 'OMR';
  String? _category;
  String? _transmission;
  String? _fuelType;
  int? _minSeats;
  double? _minRating;
  bool _instantBookOnly = false;
  bool _deliveryOnly = false;
  bool _airportOnly = false;

  String _t(String en, String ar) {
    return context.locale.languageCode == 'ar' ? ar : en;
  }

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }

  @override
  void initState() {
    super.initState();
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    final selectedCountry = await _apiService.getSelectedCountry();
    final selectedCity = await _apiService.getSelectedCity();
    final config = AppCountries.byName(selectedCountry);

    if (!mounted) return;
    setState(() {
      _selectedCountry = config.name;
      _cities = config.cities;
      _selectedCity = selectedCity ?? config.cities.first;
      _currencyCode = config.currencyCode;
      if (widget.initialCompany != null &&
          widget.initialCompany!.trim().isNotEmpty) {
        _companyController.text = widget.initialCompany!.trim();
      }
    });

    await _searchVehicles();
  }

  Future<void> _pickPickupDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _pickupDate ?? now,
      firstDate: now,
      lastDate: DateTime(now.year + 2),
    );

    if (picked != null) {
      setState(() {
        _pickupDate = picked;
        if (_returnDate != null && _returnDate!.isBefore(_pickupDate!)) {
          _returnDate = null;
        }
      });
    }
  }

  Future<void> _pickReturnDate() async {
    final now = DateTime.now();
    final initial = _returnDate ?? _pickupDate ?? now;

    final picked = await showDatePicker(
      context: context,
      initialDate: initial,
      firstDate: _pickupDate ?? now,
      lastDate: DateTime(now.year + 2),
    );

    if (picked != null) {
      setState(() => _returnDate = picked);
    }
  }

  void _onCountryChanged(String? value) {
    if (value == null) return;
    final config = AppCountries.byName(value);
    setState(() {
      _selectedCountry = config.name;
      _cities = config.cities;
      _selectedCity = config.cities.isNotEmpty ? config.cities.first : null;
      _currencyCode = config.currencyCode;
    });
  }

  Future<void> _searchVehicles() async {
    setState(() => _loading = true);

    try {
      final storedCountry = await _apiService.getSelectedCountry();
      if (_selectedCity != null && _selectedCountry == storedCountry) {
        await _apiService.saveSelectedCity(_selectedCity!);
      }

      final results = await _apiService.searchVehicles(
        brand: _brandController.text.trim(),
        country: _selectedCountry,
        city: _selectedCity,
        pickupLocation: _pickupLocationController.text.trim(),
        returnLocation: _returnLocationController.text.trim(),
        pickupDate: _pickupDate != null ? _formatDate(_pickupDate!) : null,
        returnDate: _returnDate != null ? _formatDate(_returnDate!) : null,
        category: _category,
        transmission: _transmission,
        fuelType: _fuelType,
        minSeats: _minSeats,
        minPrice: double.tryParse(_minPriceController.text.trim()),
        maxPrice: double.tryParse(_maxPriceController.text.trim()),
        maxDeposit: double.tryParse(_maxDepositController.text.trim()),
        instantBook: _instantBookOnly ? true : null,
        deliveryAvailable: _deliveryOnly ? true : null,
        airportPickup: _airportOnly ? true : null,
        company: _companyController.text.trim(),
        minRating: _minRating,
      );

      if (!mounted) return;
      setState(() => _vehicles = results);
    } catch (_) {
      if (!mounted) return;
      AppSnackBar.error(
        context,
        _t('Search failed. Please try again.',
            'فشل البحث. يرجى المحاولة مرة أخرى.'),
      );
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggleFavorite(VehicleModel vehicle) async {
    await _apiService.toggleFavoriteVehicle(vehicle.id);
    await _searchVehicles();
  }

  Future<void> _toggleCompare(VehicleModel vehicle) async {
    await _apiService.toggleCompareVehicle(vehicle.id);
    if (!mounted) return;
    AppSnackBar.success(
      context,
      _t('Vehicle added to compare list.', 'تمت إضافة المركبة إلى المقارنة.'),
    );
  }

  Future<void> _applyPopularLocations() async {
    if (_cities.isEmpty) return;
    setState(() => _selectedCity = _cities.first);
    await _searchVehicles();
  }

  Future<void> _openNearbyVehicles() async {
    if (_vehicles.isEmpty) {
      await _searchVehicles();
    }
    if (!mounted) return;
    if (_vehicles.isNotEmpty) {
      Navigator.pushNamed(
        context,
        AppRoutes.vehicleMap,
        arguments: _vehicles,
      );
    }
  }

  @override
  void dispose() {
    _brandController.dispose();
    _companyController.dispose();
    _pickupLocationController.dispose();
    _returnLocationController.dispose();
    _minPriceController.dispose();
    _maxPriceController.dispose();
    _maxDepositController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          _t('Search vehicles', 'البحث عن مركبات'),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
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
      body: ListView(
        padding: const EdgeInsets.only(bottom: 24),
        children: [
          Container(
            margin: const EdgeInsets.fromLTRB(16, 14, 16, 8),
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(22),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFFB7C0D1).withAlpha(41),
                  blurRadius: 14,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Column(
              children: [
                TextField(
                  controller: _brandController,
                  decoration: InputDecoration(
                    labelText: _t('Brand or model', 'الماركة أو الموديل'),
                    hintText:
                        _t('Toyota, Nissan, SUV...', 'تويوتا، نيسان، SUV...'),
                    prefixIcon: const Icon(Icons.directions_car_rounded),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: _selectedCountry,
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
                  ),
                  onChanged: _onCountryChanged,
                ),
                const SizedBox(height: 14),
                DropdownButtonFormField<String>(
                  initialValue: _selectedCity,
                  items: _cities
                      .map((city) => DropdownMenuItem<String>(
                          value: city, child: Text(city)))
                      .toList(),
                  decoration: InputDecoration(
                    labelText: _t('City', 'المدينة'),
                    prefixIcon: const Icon(Icons.location_city_outlined),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14),
                    ),
                  ),
                  onChanged: (value) => setState(() => _selectedCity = value),
                ),
                const SizedBox(height: 14),
                Row(
                  children: [
                    Expanded(
                      child: _dateBox(
                        title: _t('Pickup date', 'تاريخ الاستلام'),
                        value: _pickupDate != null
                            ? _formatDate(_pickupDate!)
                            : _t('Select', 'اختر'),
                        onTap: _pickPickupDate,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: _dateBox(
                        title: _t('Return date', 'تاريخ الإرجاع'),
                        value: _returnDate != null
                            ? _formatDate(_returnDate!)
                            : _t('Select', 'اختر'),
                        onTap: _pickReturnDate,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _pickupLocationController,
                        decoration: InputDecoration(
                          labelText: _t('Pickup location', 'موقع الاستلام'),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: TextField(
                        controller: _returnLocationController,
                        decoration: InputDecoration(
                          labelText: _t('Return location', 'موقع الإرجاع'),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(14),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                _suggestionsRow(),
                const SizedBox(height: 10),
                _advancedFiltersCard(),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: SizedBox(
                        height: 48,
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            borderRadius: BorderRadius.circular(16),
                            gradient: const LinearGradient(
                              begin: Alignment.centerLeft,
                              end: Alignment.centerRight,
                              colors: [Color(0xFF234E8C), Color(0xFFD3AE52)],
                            ),
                          ),
                          child: ElevatedButton(
                            onPressed: _loading ? null : _searchVehicles,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.transparent,
                              shadowColor: Colors.transparent,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                            child: _loading
                                ? const SizedBox(
                                    width: 22,
                                    height: 22,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.3,
                                      color: Colors.white,
                                    ),
                                  )
                                : Text(
                                    _t('Search', 'بحث'),
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w700,
                                      color: Colors.white,
                                    ),
                                  ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    SizedBox(
                      height: 48,
                      child: OutlinedButton.icon(
                        onPressed: _vehicles.isEmpty
                            ? null
                            : () {
                                Navigator.pushNamed(
                                  context,
                                  AppRoutes.vehicleMap,
                                  arguments: _vehicles,
                                );
                              },
                        icon: const Icon(Icons.map_outlined),
                        label: Text(_t('Map', 'الخريطة')),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFF234E8C),
                          side: const BorderSide(color: Color(0xFFE2E8F2)),
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
          ),
          if (_vehicles.isEmpty && !_loading)
            AppEmptyState(
                    icon: Icons.search_off_rounded,
                    title: _t('No results found', 'لم يتم العثور على نتائج'),
                    subtitle: _t(
                      'Try another brand, city, or date range.',
                      'جرّب ماركة أو مدينة أو فترة تاريخ مختلفة.',
                    ),
                  )
          else
            ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                    itemCount: _vehicles.length,
                    separatorBuilder: (_, __) => const SizedBox(height: 14),
                    itemBuilder: (context, index) {
                      final vehicle = _vehicles[index];

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
                                color: const Color(0xFFB7C0D1).withAlpha(46),
                                blurRadius: 14,
                                offset: const Offset(0, 8),
                              ),
                            ],
                          ),
                          child: Row(
                            children: [
                              ClipRRect(
                                borderRadius: const BorderRadius.horizontal(
                                    left: Radius.circular(24)),
                                child: SizedBox(
                                  width: 120,
                                  height: 112,
                                  child: vehicle.imageUrl.isNotEmpty
                                      ? CachedNetworkImage(
                                          imageUrl: vehicle.imageUrl,
                                          fit: BoxFit.cover,
                                          errorWidget: (_, __, ___) =>
                                              const Icon(Icons.directions_car),
                                        )
                                      : const DecoratedBox(
                                          decoration: BoxDecoration(
                                              color: Color(0xFFF2F5FA)),
                                          child: Center(
                                            child: Icon(
                                                Icons.directions_car_rounded,
                                                color: Color(0xFF234E8C)),
                                          ),
                                        ),
                                ),
                              ),
                              Expanded(
                                child: Padding(
                                  padding: const EdgeInsets.all(14),
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
                                                fontWeight: FontWeight.w700,
                                                fontSize: 15.5,
                                                color: Color(0xFF162E60),
                                              ),
                                            ),
                                          ),
                                          InkWell(
                                            onTap: () =>
                                                _toggleFavorite(vehicle),
                                            child: Icon(
                                              vehicle.isFavorite
                                                  ? Icons.favorite_rounded
                                                  : Icons
                                                      .favorite_border_rounded,
                                              color: vehicle.isFavorite
                                                  ? const Color(0xFFD14848)
                                                  : const Color(0xFF234E8C),
                                            ),
                                          ),
                                        ],
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
                                      Text(
                                        '${vehicle.category} • ${vehicle.transmission} • ${vehicle.seats} seats',
                                        style: const TextStyle(
                                          fontSize: 12,
                                          color: Color(0xFF687181),
                                        ),
                                      ),
                                      const SizedBox(height: 10),
                                      Row(
                                        children: [
                                          Text(
                                            '$_currencyCode ${vehicle.dailyRate.toStringAsFixed(0)}${_t(' / day', ' / يوم')}',
                                            style: const TextStyle(
                                              fontWeight: FontWeight.w700,
                                              color: Color(0xFF234E8C),
                                            ),
                                          ),
                                          const Spacer(),
                                          IconButton(
                                            onPressed: () =>
                                                _toggleCompare(vehicle),
                                            icon: const Icon(
                                                Icons.compare_arrows_rounded),
                                            color: const Color(0xFF234E8C),
                                            iconSize: 20,
                                            padding: EdgeInsets.zero,
                                            constraints: const BoxConstraints(),
                                          ),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
        ],
      ),
    );
  }

  Widget _dateBox({
    required String title,
    required String value,
    required VoidCallback onTap,
  }) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFE1E7F0)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: const TextStyle(fontSize: 12, color: Color(0xFF7B8192)),
            ),
            const SizedBox(height: 6),
            Text(
              value,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                color: Color(0xFF162E60),
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ignore: unused_element
  Widget _advancedFiltersCardLegacy() {
    return ExpansionTile(
      tilePadding: EdgeInsets.zero,
      title: Text(
        _t('Advanced filters', 'فلاتر متقدمة'),
        style: const TextStyle(
          fontWeight: FontWeight.w700,
          color: Color(0xFF162E60),
        ),
      ),
      children: [
        const SizedBox(height: 8),
        _inlineDropdown<String>(
          label: _t('Category', 'الفئة'),
          value: _category,
          items: const ['Economy', 'Sedan', 'SUV', 'Luxury'],
          onChanged: (value) => setState(() => _category = value),
        ),
        const SizedBox(height: 10),
        _inlineDropdown<String>(
          label: _t('Transmission', 'ناقل الحركة'),
          value: _transmission,
          items: const ['Automatic', 'Manual'],
          onChanged: (value) => setState(() => _transmission = value),
        ),
        const SizedBox(height: 10),
        _inlineDropdown<String>(
          label: _t('Fuel type', 'نوع الوقود'),
          value: _fuelType,
          items: const ['Petrol', 'Diesel', 'Hybrid', 'Electric'],
          onChanged: (value) => setState(() => _fuelType = value),
        ),
        const SizedBox(height: 10),
        _inlineDropdown<int>(
          label: _t('Minimum seats', 'الحد الأدنى للمقاعد'),
          value: _minSeats,
          items: const [2, 4, 5, 7],
          onChanged: (value) => setState(() => _minSeats = value),
        ),
        const SizedBox(height: 10),
        _inlineDropdown<double>(
          label: _t('Minimum rating', 'أدنى تقييم'),
          value: _minRating,
          items: const [3.5, 4.0, 4.5],
          onChanged: (value) => setState(() => _minRating = value),
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _companyController,
          decoration: InputDecoration(
            labelText: _t('Rental company', 'شركة التأجير'),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
        const SizedBox(height: 10),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _minPriceController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: _t('Min price', 'السعر الأدنى'),
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _maxPriceController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration: InputDecoration(
                  labelText: _t('Max price', 'السعر الأعلى'),
                  border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(14)),
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        TextField(
          controller: _maxDepositController,
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          decoration: InputDecoration(
            labelText: _t('Max deposit', 'أقصى تأمين'),
            border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
          ),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          children: [
            FilterChip(
              label: Text(_t('Instant booking', 'حجز فوري')),
              selected: _instantBookOnly,
              onSelected: (value) => setState(() => _instantBookOnly = value),
            ),
            FilterChip(
              label: Text(_t('Delivery available', 'توصيل متاح')),
              selected: _deliveryOnly,
              onSelected: (value) => setState(() => _deliveryOnly = value),
            ),
            FilterChip(
              label: Text(_t('Airport pickup', 'استلام من المطار')),
              selected: _airportOnly,
              onSelected: (value) => setState(() => _airportOnly = value),
            ),
          ],
        ),
        const SizedBox(height: 6),
      ],
    );
  }

  Widget _advancedFiltersCard() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(24),
            blurRadius: 10,
            offset: const Offset(0, 6),
          ),
        ],
      ),
      child: Theme(
        data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          tilePadding: const EdgeInsets.symmetric(horizontal: 4),
          childrenPadding: const EdgeInsets.fromLTRB(4, 6, 4, 10),
          collapsedShape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: Row(
            children: [
              Container(
                width: 30,
                height: 30,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(10),
                  color: const Color(0xFF2F61B1).withAlpha(24),
                ),
                child: const Icon(
                  Icons.tune_rounded,
                  size: 18,
                  color: Color(0xFF2F61B1),
                ),
              ),
              const SizedBox(width: 10),
              Text(
                _t('Advanced filters', 'فلاتر متقدمة'),
                style: const TextStyle(
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF162E60),
                ),
              ),
            ],
          ),
          children: [
            _advancedFieldCard(
              child: _inlineDropdown<String>(
                label: _t('Category', 'الفئة'),
                value: _category,
                items: const ['Economy', 'Sedan', 'SUV', 'Luxury'],
                onChanged: (value) => setState(() => _category = value),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: _inlineDropdown<String>(
                label: _t('Transmission', 'ناقل الحركة'),
                value: _transmission,
                items: const ['Automatic', 'Manual'],
                onChanged: (value) => setState(() => _transmission = value),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: _inlineDropdown<String>(
                label: _t('Fuel type', 'نوع الوقود'),
                value: _fuelType,
                items: const ['Petrol', 'Diesel', 'Hybrid', 'Electric'],
                onChanged: (value) => setState(() => _fuelType = value),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: _inlineDropdown<int>(
                label: _t('Minimum seats', 'الحد الأدنى للمقاعد'),
                value: _minSeats,
                items: const [2, 4, 5, 7],
                onChanged: (value) => setState(() => _minSeats = value),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: _inlineDropdown<double>(
                label: _t('Minimum rating', 'أدنى تقييم'),
                value: _minRating,
                items: const [3.5, 4.0, 4.5],
                onChanged: (value) => setState(() => _minRating = value),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: TextField(
                controller: _companyController,
                decoration:
                    _advancedInputDecoration(_t('Rental company', 'شركة التأجير')),
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _minPriceController,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration:
                          _advancedInputDecoration(_t('Min price', 'السعر الأدنى')),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: TextField(
                      controller: _maxPriceController,
                      keyboardType:
                          const TextInputType.numberWithOptions(decimal: true),
                      decoration:
                          _advancedInputDecoration(_t('Max price', 'السعر الأعلى')),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 10),
            _advancedFieldCard(
              child: TextField(
                controller: _maxDepositController,
                keyboardType:
                    const TextInputType.numberWithOptions(decimal: true),
                decoration:
                    _advancedInputDecoration(_t('Max deposit', 'أقصى تأمين')),
              ),
            ),
            const SizedBox(height: 10),
            LayoutBuilder(
              builder: (context, constraints) {
                final width = (constraints.maxWidth - 10) / 2;
                return Wrap(
                  spacing: 10,
                  runSpacing: 10,
                  children: [
                    _quickFilterCard(
                      width: width,
                      label: _t('Instant booking', 'حجز فوري'),
                      icon: Icons.bolt_rounded,
                      selected: _instantBookOnly,
                      onChanged: (value) async {
                        setState(() => _instantBookOnly = value);
                      },
                    ),
                    _quickFilterCard(
                      width: width,
                      label: _t('Delivery available', 'توصيل متاح'),
                      icon: Icons.local_shipping_rounded,
                      selected: _deliveryOnly,
                      onChanged: (value) async {
                        setState(() => _deliveryOnly = value);
                      },
                    ),
                    _quickFilterCard(
                      width: width,
                      label: _t('Airport pickup', 'استلام من المطار'),
                      icon: Icons.flight_land_rounded,
                      selected: _airportOnly,
                      onChanged: (value) async {
                        setState(() => _airportOnly = value);
                      },
                    ),
                  ],
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  InputDecoration _advancedInputDecoration(String label) {
    return InputDecoration(
      isDense: true,
      labelText: label,
      border: InputBorder.none,
      enabledBorder: InputBorder.none,
      focusedBorder: InputBorder.none,
      contentPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
    );
  }

  Widget _advancedFieldCard({required Widget child}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFD7E1F1)),
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF5F8FE)],
        ),
      ),
      child: child,
    );
  }

  // ignore: unused_element
  Widget _suggestionsRowLegacy() {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        FilterChip(
          label: Text(_t('Airport pickup', 'استلام من المطار')),
          selected: _airportOnly,
          onSelected: (value) async {
            setState(() => _airportOnly = value);
            await _searchVehicles();
          },
        ),
        FilterChip(
          label: Text(_t('Instant booking', 'حجز فوري')),
          selected: _instantBookOnly,
          onSelected: (value) async {
            setState(() => _instantBookOnly = value);
            await _searchVehicles();
          },
        ),
        FilterChip(
          label: Text(_t('Delivery available', 'توصيل متاح')),
          selected: _deliveryOnly,
          onSelected: (value) async {
            setState(() => _deliveryOnly = value);
            await _searchVehicles();
          },
        ),
        ActionChip(
          label: Text(_t('Popular locations', 'مواقع شائعة')),
          onPressed: _applyPopularLocations,
        ),
        ActionChip(
          label: Text(_t('Nearby vehicles', 'مركبات قريبة')),
          onPressed: _openNearbyVehicles,
        ),
      ],
    );
  }

  Widget _suggestionsRow() {
    return LayoutBuilder(
      builder: (context, constraints) {
        final width = (constraints.maxWidth - 10) / 2;
        return Wrap(
          spacing: 10,
          runSpacing: 10,
          children: [
            _quickFilterCard(
              width: width,
              label: _t('Airport pickup', 'استلام من المطار'),
              icon: Icons.flight_land_rounded,
              selected: _airportOnly,
              onChanged: (value) async {
                setState(() => _airportOnly = value);
                await _searchVehicles();
              },
            ),
            _quickFilterCard(
              width: width,
              label: _t('Instant booking', 'حجز فوري'),
              icon: Icons.bolt_rounded,
              selected: _instantBookOnly,
              onChanged: (value) async {
                setState(() => _instantBookOnly = value);
                await _searchVehicles();
              },
            ),
            _quickFilterCard(
              width: width,
              label: _t('Delivery available', 'توصيل متاح'),
              icon: Icons.local_shipping_rounded,
              selected: _deliveryOnly,
              onChanged: (value) async {
                setState(() => _deliveryOnly = value);
                await _searchVehicles();
              },
            ),
            _quickActionCard(
              width: width,
              label: _t('Popular locations', 'مواقع شائعة'),
              icon: Icons.place_rounded,
              onTap: _applyPopularLocations,
            ),
            _quickActionCard(
              width: width,
              label: _t('Nearby vehicles', 'مركبات قريبة'),
              icon: Icons.near_me_rounded,
              onTap: _openNearbyVehicles,
            ),
          ],
        );
      },
    );
  }

  Widget _quickFilterCard({
    required double width,
    required String label,
    required IconData icon,
    required bool selected,
    required Future<void> Function(bool) onChanged,
  }) {
    return SizedBox(
      width: width,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () => onChanged(!selected),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 180),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: selected
                    ? const Color(0xFF2E63B6)
                    : const Color(0xFFD9E2F0),
              ),
              gradient: selected
                  ? const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFF2B5CA8), Color(0xFF3A76D6)],
                    )
                  : const LinearGradient(
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                      colors: [Color(0xFFFFFFFF), Color(0xFFF6F9FF)],
                    ),
              boxShadow: [
                BoxShadow(
                  color: selected
                      ? const Color(0xFF2B5CA8).withAlpha(56)
                      : const Color(0xFF9DA8BE).withAlpha(30),
                  blurRadius: selected ? 14 : 8,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Row(
              children: [
                Icon(
                  icon,
                  size: 18,
                  color: selected ? Colors.white : const Color(0xFF35598D),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13.2,
                      color: selected ? Colors.white : const Color(0xFF213A69),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _quickActionCard({
    required double width,
    required String label,
    required IconData icon,
    required Future<void> Function() onTap,
  }) {
    return SizedBox(
      width: width,
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(16),
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: const Color(0xFFD7E1F1)),
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [Color(0xFFFFFFFF), Color(0xFFF4F8FF)],
              ),
              boxShadow: [
                BoxShadow(
                  color: const Color(0xFF9DA8BE).withAlpha(30),
                  blurRadius: 8,
                  offset: const Offset(0, 5),
                ),
              ],
            ),
            child: Row(
              children: [
                Icon(icon, size: 18, color: const Color(0xFF35598D)),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    label,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 13.2,
                      color: Color(0xFF213A69),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _inlineDropdown<T>({
    required String label,
    required T? value,
    required List<T> items,
    required ValueChanged<T?> onChanged,
  }) {
    return DropdownButtonFormField<T?>(
      initialValue: value,
      items: [
        DropdownMenuItem<T?>(
          value: null,
          child: Text(_t('Any', 'الكل')),
        ),
        ...items.map(
          (item) => DropdownMenuItem<T?>(
            value: item,
            child: Text(item.toString()),
          ),
        ),
      ],
      decoration: InputDecoration(
        labelText: label,
        isDense: true,
        border: InputBorder.none,
        enabledBorder: InputBorder.none,
        focusedBorder: InputBorder.none,
        contentPadding: const EdgeInsets.symmetric(horizontal: 6, vertical: 8),
      ),
      onChanged: onChanged,
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
