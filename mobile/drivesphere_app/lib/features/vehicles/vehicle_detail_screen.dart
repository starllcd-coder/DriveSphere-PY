import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/routes/app_routes.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';

class VehicleDetailScreen extends StatefulWidget {
  final VehicleModel vehicle;

  const VehicleDetailScreen({
    super.key,
    required this.vehicle,
  });

  @override
  State<VehicleDetailScreen> createState() => _VehicleDetailScreenState();
}

class _VehicleDetailScreenState extends State<VehicleDetailScreen> {
  final ApiService _apiService = ApiService();
  late VehicleModel vehicle;
  bool _reviewsLoading = true;
  List<Map<String, dynamic>> _reviews = [];
  bool _companyFavorite = false;

  @override
  void initState() {
    super.initState();
    vehicle = widget.vehicle;
    _loadReviews();
    _loadCompanyFavorite();
  }

  Future<void> _loadCompanyFavorite() async {
    final favorite = await _apiService.isCompanyFavorite(vehicle.companyName);
    if (!mounted) return;
    setState(() => _companyFavorite = favorite);
  }

  Future<void> _loadReviews() async {
    final items = await _apiService.getReviewsForVehicle(vehicle.id);
    if (!mounted) return;
    setState(() {
      _reviews = items;
      _reviewsLoading = false;
    });
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

  Future<void> _toggleFavorite() async {
    await _apiService.toggleFavoriteVehicle(vehicle.id);
    setState(() {
      vehicle = vehicle.copyWith(isFavorite: !vehicle.isFavorite);
    });
  }

  Future<void> _toggleCompare() async {
    await _apiService.toggleCompareVehicle(vehicle.id);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Compare list updated')),
    );
  }

  Future<void> _toggleCompanyFavorite() async {
    await _apiService.toggleFavoriteCompany(vehicle.companyName);
    final current = await _apiService.isCompanyFavorite(vehicle.companyName);
    if (!mounted) return;
    setState(() => _companyFavorite = current);
  }

  Future<void> _addToCart() async {
    await _apiService.addBookingCartVehicle(vehicle.id);
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Vehicle added to booking cart')),
    );
  }

  Future<void> _openWhatsApp() async {
    final text = Uri.encodeComponent(
      'Hello, I want to ask about ${vehicle.fullName} (${vehicle.companyName}).',
    );
    final url = Uri.parse(
        'https://wa.me/${vehicle.whatsappNumber.replaceAll('+', '')}?text=$text');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tax = vehicle.dailyRate * 0.05;
    final total = vehicle.dailyRate + tax;
    final gallery = _buildGalleryImages();

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            backgroundColor: Colors.white,
            elevation: 0,
            leading: Container(
              margin: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.white.withAlpha(230),
                shape: BoxShape.circle,
              ),
              child: IconButton(
                icon: const Icon(
                  Icons.arrow_back_ios_new_rounded,
                  color: Color(0xFF1C3566),
                  size: 18,
                ),
                onPressed: () => Navigator.pop(context),
              ),
            ),
            actions: [
              IconButton(
                onPressed: _toggleFavorite,
                icon: Icon(
                  vehicle.isFavorite
                      ? Icons.favorite_rounded
                      : Icons.favorite_border_rounded,
                  color: vehicle.isFavorite
                      ? const Color(0xFFD14848)
                      : const Color(0xFF1C3566),
                ),
              ),
              IconButton(
                onPressed: _toggleCompare,
                icon: const Icon(Icons.compare_arrows_rounded,
                    color: Color(0xFF1C3566)),
              ),
            ],
            flexibleSpace: FlexibleSpaceBar(
              background: gallery.isNotEmpty
                  ? _galleryView(gallery)
                  : _placeholderImage(),
            ),
          ),
          SliverToBoxAdapter(
            child: Padding(
              padding: const EdgeInsets.fromLTRB(18, 18, 18, 28),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          vehicle.fullName,
                          style: const TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF162E60),
                          ),
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: _statusColor(vehicle.status).withAlpha(31),
                          borderRadius: BorderRadius.circular(24),
                        ),
                        child: Text(
                          vehicle.status,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: _statusColor(vehicle.status),
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Text(
                    '${vehicle.year} • ${vehicle.category} • ${vehicle.city}',
                    style: const TextStyle(
                      fontSize: 14,
                      color: Color(0xFF7B8192),
                    ),
                  ),
                  const SizedBox(height: 18),
                  _section(
                    child: Row(
                      children: [
                        Expanded(
                            child: _infoItem(
                                'Daily price',
                                vehicle.dailyRate.toStringAsFixed(2),
                                Icons.payments)),
                        Expanded(
                            child: _infoItem(
                                'Deposit',
                                vehicle.depositAmount.toStringAsFixed(0),
                                Icons.security)),
                        Expanded(
                            child: _infoItem(
                                'Rating',
                                '${vehicle.rating.toStringAsFixed(1)} (${vehicle.reviewCount})',
                                Icons.star)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _section(
                    title: 'Rental Company',
                    child: Column(
                      children: [
                        Row(
                          children: [
                            const Expanded(
                              child: Text(
                                'Company',
                                style: TextStyle(color: Color(0xFF7B8192)),
                              ),
                            ),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    vehicle.companyName,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      color: Color(0xFF162E60),
                                    ),
                                  ),
                                  if (vehicle.companyVerified)
                                    Container(
                                      margin: const EdgeInsets.only(top: 6),
                                      padding: const EdgeInsets.symmetric(
                                        horizontal: 8,
                                        vertical: 3,
                                      ),
                                      decoration: BoxDecoration(
                                        color: const Color(0xFF179D57)
                                            .withAlpha(28),
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                      child: const Text(
                                        'Verified',
                                        style: TextStyle(
                                          color: Color(0xFF179D57),
                                          fontSize: 11,
                                          fontWeight: FontWeight.w700,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                            ),
                            IconButton(
                              onPressed: _toggleCompanyFavorite,
                              icon: Icon(
                                _companyFavorite
                                    ? Icons.favorite_rounded
                                    : Icons.favorite_border_rounded,
                                color: _companyFavorite
                                    ? const Color(0xFFD14848)
                                    : const Color(0xFF234E8C),
                              ),
                            ),
                          ],
                        ),
                        _specRow('Pickup location', vehicle.pickupLocation),
                        _specRow('Instant booking',
                            vehicle.instantBook ? 'Yes' : 'No'),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _section(
                    title: 'Vehicle Specifications',
                    child: Column(
                      children: [
                        _specRow('Brand', vehicle.brandName),
                        _specRow('Model', vehicle.modelName),
                        _specRow('Year', vehicle.year.toString()),
                        _specRow('Category', vehicle.category),
                        _specRow('Transmission', vehicle.transmission),
                        _specRow('Engine', vehicle.engineType),
                        _specRow('Fuel type', vehicle.fuelType),
                        _specRow('Seats', vehicle.seats.toString()),
                        _specRow('Luggage', vehicle.luggage.toString()),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _section(
                    title: 'Pricing Breakdown',
                    child: Column(
                      children: [
                        _specRow(
                            'Daily rate', vehicle.dailyRate.toStringAsFixed(2)),
                        _specRow('Deposit',
                            vehicle.depositAmount.toStringAsFixed(2)),
                        _specRow('Taxes', tax.toStringAsFixed(2)),
                        _specRow('Estimated payable today',
                            total.toStringAsFixed(2)),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _section(
                    title: 'Rental Conditions',
                    child: Column(
                      children: [
                        _ConditionRow(
                          'Minimum driver age',
                          vehicle.minimumDriverAge.toString(),
                        ),
                        _ConditionRow(
                          'Mileage limit',
                          '${vehicle.mileageLimitPerDay} km / day',
                        ),
                        _ConditionRow('Insurance', vehicle.insuranceCoverage),
                        _ConditionRow(
                          'Cancellation',
                          vehicle.cancellationPolicy,
                        ),
                        _ConditionRow(
                          'Delivery available',
                          vehicle.deliveryAvailable ? 'Yes' : 'No',
                        ),
                        _ConditionRow(
                          'Airport pickup',
                          vehicle.airportPickup ? 'Yes' : 'No',
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 16),
                  _section(
                    title: 'Customer Reviews',
                    child: _reviewsLoading
                        ? const Padding(
                            padding: EdgeInsets.symmetric(vertical: 8),
                            child: LinearProgressIndicator(),
                          )
                        : _reviews.isEmpty
                            ? const Text('No reviews yet.')
                            : Column(
                                children: _reviews
                                    .map((review) => _reviewCard(review))
                                    .toList(),
                              ),
                  ),
                  const SizedBox(height: 18),
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(24),
                      gradient: const LinearGradient(
                        colors: [
                          Color(0xFF234E8C),
                          Color(0xFF1D467E),
                          Color(0xFFD3AE52)
                        ],
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Ready to book this vehicle?',
                          style: TextStyle(
                            fontSize: 17,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                        const SizedBox(height: 14),
                        Row(
                          children: [
                            Expanded(
                              child: SizedBox(
                                height: 50,
                                child: ElevatedButton(
                                  onPressed: () {
                                    Navigator.pushNamed(
                                      context,
                                      AppRoutes.booking,
                                      arguments: vehicle,
                                    );
                                  },
                                  style: ElevatedButton.styleFrom(
                                    backgroundColor: Colors.white,
                                    foregroundColor: const Color(0xFF1C3566),
                                    shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(16),
                                    ),
                                  ),
                                  child: const Text(
                                    'Book Now',
                                    style: TextStyle(
                                      fontWeight: FontWeight.w700,
                                      fontSize: 15,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(width: 10),
                            SizedBox(
                              height: 50,
                              child: OutlinedButton.icon(
                                onPressed: _addToCart,
                                icon: const Icon(Icons.add_shopping_cart),
                                label: const Text('Add to cart'),
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
                        const SizedBox(height: 10),
                        SizedBox(
                          width: double.infinity,
                          height: 50,
                          child: OutlinedButton.icon(
                            onPressed: _openWhatsApp,
                            icon: const Icon(Icons.chat_outlined),
                            label: const Text('WhatsApp'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: const BorderSide(color: Colors.white70),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(16),
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 10),
                        SizedBox(
                          width: double.infinity,
                          child: OutlinedButton.icon(
                            onPressed: () {
                              Navigator.pushNamed(
                                context,
                                AppRoutes.reviews,
                                arguments: vehicle,
                              );
                            },
                            icon: const Icon(Icons.star_outline_rounded),
                            label: const Text('Rate this vehicle'),
                            style: OutlinedButton.styleFrom(
                              foregroundColor: Colors.white,
                              side: const BorderSide(color: Colors.white70),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _section({String? title, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFFB7C0D1).withAlpha(36),
            blurRadius: 14,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (title != null) ...[
            Text(
              title,
              style: const TextStyle(
                fontWeight: FontWeight.w700,
                fontSize: 16,
                color: Color(0xFF162E60),
              ),
            ),
            const SizedBox(height: 14),
          ],
          child,
        ],
      ),
    );
  }

  List<String> _buildGalleryImages() {
    final images = <String>[];
    if (vehicle.imageUrl.isNotEmpty) {
      images.add(vehicle.imageUrl);
    }
    for (final url in vehicle.galleryImages) {
      if (url.isNotEmpty && !images.contains(url)) {
        images.add(url);
      }
    }
    return images;
  }

  Widget _galleryView(List<String> images) {
    return Stack(
      children: [
        PageView.builder(
          itemCount: images.length,
          itemBuilder: (context, index) {
            final url = images[index];
            return CachedNetworkImage(
              imageUrl: url,
              fit: BoxFit.cover,
              errorWidget: (_, __, ___) => _placeholderImage(),
            );
          },
        ),
        if (images.length > 1)
          Positioned(
            left: 16,
            right: 16,
            bottom: 16,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: Colors.black.withAlpha(120),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Text(
                '${images.length} photos',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                  fontSize: 12,
                ),
              ),
            ),
          ),
      ],
    );
  }

  Widget _reviewCard(Map<String, dynamic> review) {
    final rating = int.tryParse(review['rating']?.toString() ?? '0') ?? 0;
    final comment = review['comment']?.toString() ?? '';
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF7F9FD),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE2E8F2)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: List.generate(5, (index) {
              final value = index + 1;
              return Icon(
                value <= rating
                    ? Icons.star_rounded
                    : Icons.star_outline_rounded,
                color: const Color(0xFFD3AE52),
                size: 18,
              );
            }),
          ),
          if (comment.isNotEmpty) ...[
            const SizedBox(height: 8),
            Text(
              comment,
              style: const TextStyle(
                fontSize: 13,
                height: 1.4,
                color: Color(0xFF687181),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _infoItem(String title, String value, IconData icon) {
    return Column(
      children: [
        Icon(icon, color: const Color(0xFF234E8C)),
        const SizedBox(height: 6),
        Text(title,
            style: const TextStyle(fontSize: 12, color: Color(0xFF7B8192))),
        const SizedBox(height: 4),
        Text(
          value,
          textAlign: TextAlign.center,
          style: const TextStyle(
              fontWeight: FontWeight.w700, color: Color(0xFF162E60)),
        ),
      ],
    );
  }

  Widget _specRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
            child: Text(
              label,
              style: const TextStyle(color: Color(0xFF7B8192)),
            ),
          ),
          Text(
            value,
            style: const TextStyle(
              fontWeight: FontWeight.w600,
              color: Color(0xFF162E60),
            ),
          ),
        ],
      ),
    );
  }

  Widget _placeholderImage() {
    return Container(
      color: const Color(0xFFF2F4FA),
      child: const Center(
        child: Icon(
          Icons.directions_car,
          size: 70,
          color: Color(0xFFB3BAC8),
        ),
      ),
    );
  }
}

class _ConditionRow extends StatelessWidget {
  final String label;
  final String value;

  const _ConditionRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
              child: Text(label,
                  style: const TextStyle(color: Color(0xFF7B8192)))),
          Text(value,
              style: const TextStyle(
                  fontWeight: FontWeight.w600, color: Color(0xFF162E60))),
        ],
      ),
    );
  }
}
