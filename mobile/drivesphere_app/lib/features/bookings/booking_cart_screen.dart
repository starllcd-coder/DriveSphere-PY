import 'package:flutter/material.dart';

import '../../core/utils/app_message_helper.dart';
import '../../core/utils/app_validators.dart';
import '../../models/vehicle_model.dart';
import '../../services/api_service.dart';
import '../../services/hyperpay_service.dart';
import '../../widgets/app_primary_button.dart';
import '../../widgets/app_snackbar.dart';

class BookingCartScreen extends StatefulWidget {
  const BookingCartScreen({super.key});

  @override
  State<BookingCartScreen> createState() => _BookingCartScreenState();
}

class _BookingCartScreenState extends State<BookingCartScreen> {
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
  bool _loading = true;
  bool _processing = false;
  bool _payNow = true;

  List<VehicleModel> _vehicles = [];
  List<String> _paymentMethods = const ['CARD'];
  String _selectedPaymentMethod = 'CARD';
  String _selectedCardBrand = 'VISA';
  String _currencyCode = 'SAR';

  @override
  void initState() {
    super.initState();
    _hyperPayService = HyperPayService(apiService: _apiService);
    _loadCart();
    _loadCurrency();
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

  Future<void> _loadCart() async {
    setState(() => _loading = true);
    final vehicles = await _apiService.fetchVehicles();
    final ids = await _apiService.getBookingCartVehicleIds();
    final methods = await _apiService.getSavedPaymentMethods();

    if (!mounted) return;
    setState(() {
      _vehicles = vehicles.where((e) => ids.contains(e.id)).toList();
      _paymentMethods = methods.isNotEmpty ? methods : const ['CARD'];
      _selectedPaymentMethod = _paymentMethods.first;
      _loading = false;
    });
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

  String _formatDate(DateTime date) {
    final month = date.month.toString().padLeft(2, '0');
    final day = date.day.toString().padLeft(2, '0');
    return '${date.year}-$month-$day';
  }

  Future<void> _removeVehicle(VehicleModel vehicle) async {
    await _apiService.removeBookingCartVehicle(vehicle.id);
    await _loadCart();
  }

  Future<void> _clearCart() async {
    await _apiService.clearBookingCart();
    await _loadCart();
  }

  Future<void> _submitBookings() async {
    if (_vehicles.isEmpty) {
      AppSnackBar.error(context, 'Cart is empty.');
      return;
    }

    final customerError = AppValidators.integerId(
      _customerIdController.text,
      'Customer ID',
    );
    final pickupLocationError = AppValidators.requiredField(
      _pickupLocationController.text,
      'Pickup location',
    );
    final returnLocationError = AppValidators.requiredField(
      _returnLocationController.text,
      'Return location',
    );

    if (customerError != null) {
      AppSnackBar.error(context, customerError);
      return;
    }

    if (_pickupDate == null || _returnDate == null) {
      AppSnackBar.error(context, 'Select pickup and return dates first.');
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

    setState(() => _processing = true);
    final references = <String>[];

    try {
      for (final vehicle in _vehicles) {
        final available = await _apiService.validateVehicleAvailability(
          vehicleId: vehicle.id,
          pickupDate: _formatDate(_pickupDate!),
          returnDate: _formatDate(_returnDate!),
        );

        if (!available) {
          continue;
        }

        final result = await _apiService.createBooking(
          customerId: int.parse(_customerIdController.text.trim()),
          vehicleId: vehicle.id,
          pickupDate: _formatDate(_pickupDate!),
          returnDate: _formatDate(_returnDate!),
          pickupLocation: _pickupLocationController.text.trim(),
          returnLocation: _returnLocationController.text.trim(),
          notes: _notesController.text.trim(),
        );

        final reference = result['reference']?.toString() ?? 'DS-UNKNOWN';
        final bookingId = result['id'] ?? 0;
        references.add(reference);

        if (_payNow && bookingId != 0) {
          final rentalDays =
              _returnDate!.difference(_pickupDate!).inDays.abs() + 1;
          final subtotal = rentalDays * vehicle.dailyRate;
          final total = subtotal + (subtotal * 0.05);
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
              notes: 'Auto payment from cart',
            );
          }
        }
      }

      if (!mounted) return;
      await _apiService.clearBookingCart();
      await _loadCart();
      if (!mounted) return;

      showDialog<void>(
        context: context,
        builder: (context) => AlertDialog(
          title: const Text('Bookings created'),
          content: Text(
            references.isEmpty
                ? 'No bookings could be created.'
                : 'Created bookings:\n${references.join('\n')}',
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        ),
      );
    } catch (e) {
      if (!mounted) return;
      AppSnackBar.error(context, AppMessageHelper.extractErrorMessage(e));
    } finally {
      if (mounted) setState(() => _processing = false);
    }
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
    return Scaffold(
      backgroundColor: const Color(0xFFF6F7FB),
      appBar: AppBar(
        title: const Text('Booking Cart'),
        actions: [
          IconButton(
            onPressed: _clearCart,
            icon: const Icon(Icons.delete_outline_rounded),
          ),
        ],
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 24),
              children: [
                if (_vehicles.isEmpty)
                  const Center(child: Text('No vehicles in cart.'))
                else
                  ..._vehicles.map(
                    (vehicle) => Container(
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(14),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
                        ),
                        border: Border.all(color: const Color(0xFFDCE5F3)),
                        borderRadius: BorderRadius.circular(18),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF9DA8BE).withAlpha(28),
                            blurRadius: 14,
                            offset: const Offset(0, 9),
                          ),
                        ],
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  vehicle.fullName,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  vehicle.companyName,
                                  style: const TextStyle(
                                    color: Color(0xFF687181),
                                    fontSize: 12,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            onPressed: () => _removeVehicle(vehicle),
                            icon: const Icon(Icons.close_rounded),
                          ),
                        ],
                      ),
                    ),
                  ),
                const SizedBox(height: 12),
                _card(
                  child: Column(
                    children: [
                      _textField(
                        controller: _customerIdController,
                        label: 'Customer ID',
                        keyboardType: TextInputType.number,
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: _dateBox(
                              title: 'Pickup date',
                              value: _pickupDate != null
                                  ? _formatDate(_pickupDate!)
                                  : 'Select',
                              onTap: _pickPickupDate,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: _dateBox(
                              title: 'Return date',
                              value: _returnDate != null
                                  ? _formatDate(_returnDate!)
                                  : 'Select',
                              onTap: _pickReturnDate,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      _textField(
                        controller: _pickupLocationController,
                        label: 'Pickup location',
                      ),
                      const SizedBox(height: 12),
                      _textField(
                        controller: _returnLocationController,
                        label: 'Return location',
                      ),
                      const SizedBox(height: 12),
                      _textField(
                        controller: _notesController,
                        label: 'Notes (optional)',
                        maxLines: 3,
                      ),
                      const SizedBox(height: 12),
                      SwitchListTile(
                        value: _payNow,
                        onChanged: (value) => setState(() => _payNow = value),
                        title: const Text('Pay now'),
                        contentPadding: EdgeInsets.zero,
                      ),
                      if (_payNow) ...[
                        const SizedBox(height: 8),
                        DropdownButtonFormField<String>(
                          initialValue: _selectedPaymentMethod,
                          decoration: InputDecoration(
                            labelText: 'Payment method',
                            border: OutlineInputBorder(
                              borderRadius: BorderRadius.circular(14),
                            ),
                          ),
                          items: _paymentMethods
                              .map(
                                (method) => DropdownMenuItem(
                                  value: method,
                                  child: Text(method),
                                ),
                              )
                              .toList(),
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
                            decoration: InputDecoration(
                              labelText: 'Card brand',
                              border: OutlineInputBorder(
                                borderRadius: BorderRadius.circular(14),
                              ),
                            ),
                            items: const [
                              DropdownMenuItem(
                                  value: 'VISA', child: Text('VISA')),
                              DropdownMenuItem(
                                  value: 'MASTER', child: Text('Mastercard')),
                            ],
                            onChanged: (value) {
                              if (value != null) {
                                setState(() => _selectedCardBrand = value);
                              }
                            },
                          ),
                        ],
                      ],
                      const SizedBox(height: 16),
                      AppPrimaryButton(
                        label: 'Create bookings',
                        loading: _processing,
                        onPressed: _submitBookings,
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }

  Widget _card({required Widget child}) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [Color(0xFFFFFFFF), Color(0xFFF6FAFF)],
        ),
        border: Border.all(color: const Color(0xFFDCE5F3)),
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF9DA8BE).withAlpha(28),
            blurRadius: 14,
            offset: const Offset(0, 9),
          ),
        ],
      ),
      child: child,
    );
  }

  Widget _textField({
    required TextEditingController controller,
    required String label,
    TextInputType? keyboardType,
    int maxLines = 1,
  }) {
    return TextField(
      controller: controller,
      keyboardType: keyboardType,
      maxLines: maxLines,
      decoration: InputDecoration(
        labelText: label,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
        ),
      ),
    );
  }

  Widget _dateBox({
    required String title,
    required String value,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: const Color(0xFFF7F9FD),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: const Color(0xFFE2E8F2)),
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
}
