import 'package:easy_localization/easy_localization.dart';
import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../core/routes/app_routes.dart';
import '../../core/utils/app_message_helper.dart';
import '../../core/utils/app_validators.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../services/hyperpay_service.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class BookingScreen extends StatefulWidget {
  final VehicleModel vehicle;

  const BookingScreen({
    super.key,
    required this.vehicle,
  });

  @override
  State<BookingScreen> createState() => _BookingScreenState();
}

class _BookingScreenState extends State<BookingScreen> {
  final ApiService _apiService = ApiService();
  late final HyperPayService _hyperPayService;

  final TextEditingController _customerIdController =
      TextEditingController(text: '1');
  final TextEditingController _pickupLocationController =
      TextEditingController();
  final TextEditingController _returnLocationController =
      TextEditingController();
  final TextEditingController _notesController = TextEditingController();

  DateTime? _pickupDate;
  DateTime? _returnDate;
  List<String> _paymentMethods = const ['CARD'];
  String _selectedPaymentMethod = 'CARD';
  bool _payNow = true;
  String _selectedCardBrand = 'VISA';
  String _currencyCode = 'SAR';
  bool _documentsReady = false;
  String? _lastBookingReference;
  List<String> _savedLocations = [];

  bool _loading = false;

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
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

  Future<void> _contactWhatsApp() async {
    final bookingRefText =
        _lastBookingReference != null ? ' booking $_lastBookingReference' : '';
    final text = Uri.encodeComponent(
      'Hello, I want help with$bookingRefText for ${widget.vehicle.fullName}.',
    );
    final url = Uri.parse(
        'https://wa.me/${widget.vehicle.whatsappNumber.replaceAll('+', '')}?text=$text');
    if (await canLaunchUrl(url)) {
      await launchUrl(url, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _submitBooking() async {
    final customerError = AppValidators.integerId(
        _customerIdController.text, 'booking.customer_id'.tr());
    final pickupLocationError = AppValidators.requiredField(
      _pickupLocationController.text,
      'booking.pickup_location'.tr(),
    );
    final returnLocationError = AppValidators.requiredField(
      _returnLocationController.text,
      'booking.return_location'.tr(),
    );

    if (customerError != null) {
      AppSnackBar.error(context, customerError);
      return;
    }

    if (_pickupDate == null) {
      AppSnackBar.error(context, 'booking.pickup_date_required'.tr());
      return;
    }

    if (_returnDate == null) {
      AppSnackBar.error(context, 'booking.return_date_required'.tr());
      return;
    }

    if (_returnDate!.isBefore(_pickupDate!)) {
      AppSnackBar.error(context, 'booking.date_order_error'.tr());
      return;
    }

    if (pickupLocationError != null) {
      AppSnackBar.error(context, pickupLocationError);
      return;
    }

    if (returnLocationError != null) {
      AppSnackBar.error(context, returnLocationError);
      return;
    }

    if (!_documentsReady) {
      AppSnackBar.error(
        context,
        'Please confirm documents are uploaded before booking.',
      );
      return;
    }

    setState(() => _loading = true);

    try {
      final available = await _apiService.validateVehicleAvailability(
        vehicleId: widget.vehicle.id,
        pickupDate: _formatDate(_pickupDate!),
        returnDate: _formatDate(_returnDate!),
      );

      if (!available) {
        if (!mounted) return;
        AppSnackBar.error(
          context,
          'Vehicle is no longer available for the selected dates.',
        );
        setState(() => _loading = false);
        return;
      }

      final result = await _apiService.createBooking(
        customerId: int.parse(_customerIdController.text.trim()),
        vehicleId: widget.vehicle.id,
        pickupDate: _formatDate(_pickupDate!),
        returnDate: _formatDate(_returnDate!),
        pickupLocation: _pickupLocationController.text.trim(),
        returnLocation: _returnLocationController.text.trim(),
        notes: _notesController.text.trim(),
      );

      final reference = result['reference']?.toString() ?? 'DS-UNKNOWN';
      final bookingId = result['id'] ?? 0;
      _lastBookingReference = reference;

      if (_payNow && bookingId != 0) {
        final total = _calculateTotal();
        if (_selectedPaymentMethod == 'CARD') {
          final hyperResult = await _hyperPayService.payWithCard(
            bookingId: bookingId,
            amount: total.toStringAsFixed(2),
            currency: _currencyCode,
            paymentBrand: _selectedCardBrand,
          );
          if (!hyperResult.success) {
            if (!mounted) return;
            AppSnackBar.error(
              context,
              hyperResult.message ?? 'Card payment failed.',
            );
          }
        } else {
          await _apiService.createPayment(
            bookingId: bookingId,
            amount: total.toStringAsFixed(2),
            method: _selectedPaymentMethod,
            notes: 'Auto payment from booking',
          );
        }
      }

      if (!mounted) return;

      showDialog<void>(
        context: context,
        builder: (context) {
          return AlertDialog(
            shape:
                RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
            title: Text(
              'booking.created_title'.tr(),
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
            content: Text(
              'Your booking was created successfully.\n\nReference: $reference\nPayment Method: $_selectedPaymentMethod',
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    AppRoutes.appShell,
                    (route) => false,
                  );
                },
                child: Text('booking.go_dashboard'.tr()),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  Navigator.pushNamedAndRemoveUntil(
                    context,
                    AppRoutes.bookingHistory,
                    (route) => false,
                  );
                },
                child: Text('booking.view_bookings'.tr()),
              ),
            ],
          );
        },
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  void initState() {
    super.initState();
    _hyperPayService = HyperPayService(apiService: _apiService);
    _pickupLocationController.text = widget.vehicle.pickupLocation;
    _returnLocationController.text = widget.vehicle.pickupLocation;
    _loadPaymentMethods();
    _loadCurrency();
    _loadSavedLocations();
  }

  Future<void> _loadSavedLocations() async {
    final locations = await _apiService.getSavedPickupLocations();
    if (!mounted) return;
    setState(() => _savedLocations = locations);
  }

  Future<void> _savePickupLocation() async {
    final value = _pickupLocationController.text.trim();
    if (value.isEmpty) return;
    await _apiService.addSavedPickupLocation(value);
    await _loadSavedLocations();
  }

  Future<void> _loadCurrency() async {
    final country = await _apiService.getSelectedCountry();
    if (!mounted) return;
    setState(() {
      _currencyCode = country == null ? 'SAR' : _currencyFromCountry(country);
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
        return 'SAR';
    }
  }

  Future<void> _loadPaymentMethods() async {
    final methods = await _apiService.getSavedPaymentMethods();
    if (!mounted) return;
    setState(() {
      _paymentMethods = methods;
      _selectedPaymentMethod = methods.first;
    });
  }

  @override
  void dispose() {
    _customerIdController.dispose();
    _pickupLocationController.dispose();
    _returnLocationController.dispose();
    _notesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final rentalDays = _pickupDate != null && _returnDate != null
        ? (_returnDate!.difference(_pickupDate!).inDays + 1)
        : 1;
    final subtotal = rentalDays * widget.vehicle.dailyRate;
    final taxes = subtotal * 0.05;
    final total = subtotal + taxes;

    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        title: Text(
          'booking.title'.tr(),
          style: const TextStyle(
            color: Color(0xFF1C3566),
            fontWeight: FontWeight.w700,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            onPressed: _contactWhatsApp,
            icon: const Icon(Icons.chat_outlined, color: Color(0xFF1C3566)),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
        child: Column(
          children: [
            _topVehicleCard(),
            const SizedBox(height: 16),
            _pricingCard(subtotal, taxes, total, rentalDays),
            const SizedBox(height: 16),
            _formCard(),
          ],
        ),
      ),
    );
  }

  Widget _topVehicleCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: [Color(0xFF234E8C), Color(0xFF1D467E), Color(0xFFD3AE52)],
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            widget.vehicle.fullName,
            style: const TextStyle(
                fontSize: 18, fontWeight: FontWeight.w700, color: Colors.white),
          ),
          const SizedBox(height: 6),
          Text(
            '${widget.vehicle.companyName} • ${widget.vehicle.pickupLocation}',
            style: const TextStyle(fontSize: 14, color: Colors.white),
          ),
          const SizedBox(height: 6),
          Text(
            '$_currencyCode ${widget.vehicle.dailyRate.toStringAsFixed(3)} ${'vehicles.per_day'.tr()}',
            style: const TextStyle(fontSize: 14, color: Colors.white),
          ),
        ],
      ),
    );
  }

  Widget _pricingCard(
      double subtotal, double taxes, double total, int rentalDays) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Pricing Breakdown',
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 16,
              color: Color(0xFF162E60),
            ),
          ),
          const SizedBox(height: 12),
          _priceRow('Rental days', '$rentalDays'),
          _priceRow('Daily rate', widget.vehicle.dailyRate.toStringAsFixed(2)),
          _priceRow('Subtotal', subtotal.toStringAsFixed(2)),
          _priceRow('Taxes', taxes.toStringAsFixed(2)),
          _priceRow('Deposit', widget.vehicle.depositAmount.toStringAsFixed(2)),
          _priceRow('Payment method', _selectedPaymentMethod),
          const Divider(height: 24),
          _priceRow('Estimated total', total.toStringAsFixed(2), bold: true),
        ],
      ),
    );
  }

  Widget _formCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(22),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 16,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: Column(
        children: [
          TextField(
            controller: _customerIdController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(labelText: 'Customer ID'),
          ),
          const SizedBox(height: 12),
          SwitchListTile(
            value: _payNow,
            contentPadding: EdgeInsets.zero,
            onChanged: (value) => setState(() => _payNow = value),
            title: const Text('Pay now'),
          ),
          if (_payNow) ...[
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              initialValue: _selectedPaymentMethod,
              items: _paymentMethods
                  .map(
                    (method) => DropdownMenuItem(
                      value: method,
                      child: Text(method),
                    ),
                  )
                  .toList(),
              decoration: const InputDecoration(labelText: 'Payment method'),
              onChanged: (value) {
                if (value != null) {
                  setState(() => _selectedPaymentMethod = value);
                }
              },
            ),
            if (_selectedPaymentMethod == 'CARD') ...[
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: _selectedCardBrand,
                items: const [
                  DropdownMenuItem(value: 'VISA', child: Text('VISA')),
                  DropdownMenuItem(value: 'MASTER', child: Text('Mastercard')),
                ],
                decoration: const InputDecoration(labelText: 'Card brand'),
                onChanged: (value) {
                  if (value != null) {
                    setState(() => _selectedCardBrand = value);
                  }
                },
              ),
            ],
            const SizedBox(height: 12),
          ],
          _dateTile('Pickup date', _pickupDate, _pickPickupDate),
          const SizedBox(height: 12),
          _dateTile('Return date', _returnDate, _pickReturnDate),
          const SizedBox(height: 12),
          TextField(
            controller: _pickupLocationController,
            decoration: const InputDecoration(labelText: 'Pickup location'),
          ),
          if (_savedLocations.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _savedLocations
                  .map(
                    (location) => ChoiceChip(
                      label: Text(location),
                      selected: _pickupLocationController.text == location,
                      onSelected: (_) {
                        setState(
                            () => _pickupLocationController.text = location);
                      },
                    ),
                  )
                  .toList(),
            ),
          ],
          const SizedBox(height: 8),
          Align(
            alignment: Alignment.centerLeft,
            child: OutlinedButton.icon(
              onPressed: _savePickupLocation,
              icon: const Icon(Icons.bookmark_add_outlined),
              label: const Text('Save pickup location'),
            ),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _returnLocationController,
            decoration: const InputDecoration(labelText: 'Return location'),
          ),
          if (_savedLocations.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _savedLocations
                  .map(
                    (location) => ChoiceChip(
                      label: Text(location),
                      selected: _returnLocationController.text == location,
                      onSelected: (_) {
                        setState(
                            () => _returnLocationController.text = location);
                      },
                    ),
                  )
                  .toList(),
            ),
          ],
          const SizedBox(height: 12),
          TextField(
            controller: _notesController,
            maxLines: 3,
            decoration: const InputDecoration(labelText: 'Notes'),
          ),
          const SizedBox(height: 12),
          CheckboxListTile(
            value: _documentsReady,
            contentPadding: EdgeInsets.zero,
            onChanged: (value) =>
                setState(() => _documentsReady = value ?? false),
            title: const Text('I have uploaded required documents'),
            subtitle: const Text('Driver license and passport or national ID'),
          ),
          const SizedBox(height: 18),
          AppPrimaryButton(
            label: _loading ? 'Processing...' : 'Confirm Booking',
            loading: _loading,
            onPressed: () {
              _submitBooking();
            },
          ),
        ],
      ),
    );
  }

  Widget _dateTile(String title, DateTime? value, VoidCallback onTap) {
    return InkWell(
      onTap: onTap,
      child: InputDecorator(
        decoration: InputDecoration(labelText: title),
        child: Text(value == null ? 'Select date' : _formatDate(value)),
      ),
    );
  }

  Widget _priceRow(String label, String value, {bool bold = false}) {
    final style = TextStyle(
      fontSize: 13.5,
      fontWeight: bold ? FontWeight.w700 : FontWeight.w500,
      color: const Color(0xFF162E60),
    );

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        children: [
          Expanded(
              child: Text(label,
                  style: const TextStyle(color: Color(0xFF7B8192)))),
          Text(value, style: style),
        ],
      ),
    );
  }

  double _calculateTotal() {
    final rentalDays = _pickupDate != null && _returnDate != null
        ? (_returnDate!.difference(_pickupDate!).inDays + 1)
        : 1;
    final subtotal = rentalDays * widget.vehicle.dailyRate;
    final taxes = subtotal * 0.05;
    return subtotal + taxes;
  }
}
